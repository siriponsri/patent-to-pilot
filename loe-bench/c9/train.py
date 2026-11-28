"""Train C9 adapters with explicit frozen SFT and GRPO loss reductions."""

import argparse
from importlib.metadata import version
from pathlib import Path
from time import monotonic

import torch
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict, set_peft_model_state_dict
from transformers import AutoModelForCausalLM, GenerationConfig, set_seed

from loe_bench.c9 import grpo_reward, sft_target

from .checkpoint import model_manifest
from .inputs import APPROVED_GPUS, canonical, file_digest, schedule, specification, write_json
from .roster import prepare

ARMS = ("sft", "grpo")
PACKAGES = ("torch", "transformers", "peft", "trl", "datasets", "accelerate", "numpy",
            "huggingface-hub")


def runtime(dry, spec):
    versions = {name: version(name) for name in PACKAGES}
    expected = dict(spec["checkpoint"]["runtime"])
    if dry:
        expected["torch"] = "2.8.0+cpu"
    if any(versions[name] != pinned for name, pinned in expected.items()):
        raise ValueError(f"C9 runtime mismatch: {versions}")
    if dry:
        torch.set_num_threads(4)
        return "cpu", versions
    if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise RuntimeError("C9 needs exactly one visible bfloat16 GPU")
    gpu = torch.cuda.get_device_properties(0)
    if gpu.name not in APPROVED_GPUS or not 21 <= gpu.total_memory / 2**30 <= 24:
        raise RuntimeError(f"C9 needs one 24 GiB NVIDIA A10 or NVIDIA L4, found {gpu.name}")
    return "cuda", versions | {"gpu": gpu.name, "vram_bytes": gpu.total_memory}


def load_base(checkpoint, device, spec):
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False, use_safetensors=True,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32, attn_implementation="sdpa",
    ).to(device)
    if device == "cuda" and model.num_parameters() != spec["checkpoint"]["parameter_count"]:
        raise ValueError("base checkpoint parameter count mismatch")
    model.requires_grad_(False)
    return model


@torch.no_grad()
def generate(model, tokenizer, prompts, decoder, *, sample):
    groups = decoder["group_size"] if sample else 1
    config = GenerationConfig(
        do_sample=sample, num_beams=1, num_return_sequences=groups,
        max_new_tokens=decoder["max_new_tokens"], eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id, use_cache=True,
    )
    if sample:
        config.temperature = decoder["temperature"]
        config.top_p = decoder["top_p"]
        config.top_k = decoder["top_k"]
    model.eval()
    batch = tokenizer.pad({"input_ids": prompts}, padding=True, return_tensors="pt").to(model.device)
    width = batch.input_ids.shape[1]
    continuations = model.generate(**batch, generation_config=config)[:, width:].tolist()
    if len(continuations) != len(prompts) * groups:
        raise RuntimeError("missing generated continuation")
    eos = tokenizer.eos_token_id
    return [seq[:seq.index(eos) + 1] if eos in seq else seq for seq in continuations]


def decode(tokenizer, ids):
    if ids and ids[-1] == tokenizer.eos_token_id:
        ids = ids[:-1]
    return tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)


def completion_logp(model, prompt, continuation):
    # Stop the input before the final target token, then keep just the logits
    # that predict assistant tokens. This avoids a full prompt × vocab tensor.
    if not continuation:
        raise RuntimeError("missing completion token sequence")
    tokens = torch.tensor([prompt + continuation], device=model.device)
    logits = model(input_ids=tokens[:, :-1], use_cache=False,
                   logits_to_keep=len(continuation)).logits.float().squeeze(0)
    selected = logits.gather(1, tokens[:, -len(continuation):].T).squeeze(1)
    return selected - logits.logsumexp(dim=-1)


def standardized_advantages(rewards):
    return (rewards - rewards.mean(dim=1, keepdim=True)) / (
        rewards.std(dim=1, unbiased=False, keepdim=True) + 0.0001
    )


def grpo_loss(logp, old, ref, advantage, decoder):
    ratio = (logp - old).exp()
    epsilon = decoder["clip_epsilon"]
    surrogate = torch.minimum(ratio * advantage, ratio.clamp(1 - epsilon, 1 + epsilon) * advantage)
    delta = ref - logp
    kl = delta.expm1() - delta
    return (decoder["reference_kl_beta"] * kl - surrogate).mean()


def rollout(model, tokenizer, prompts, labels, decoder):
    with torch.no_grad():
        continuations = generate(model, tokenizer, prompts, decoder, sample=True)
        group = decoder["group_size"]
        expanded = [prompt for prompt in prompts for _ in range(group)]
        rewards = [grpo_reward(decode(tokenizer, ids), labels[i // group])
                   for i, ids in enumerate(continuations)]
        advantages = standardized_advantages(
            torch.tensor(rewards, device=model.device).reshape(-1, group)
        ).flatten()
        pairs = list(zip(expanded, continuations, strict=True))
        old = [completion_logp(model, *pair) for pair in pairs]
        with model.disable_adapter():
            refs = [completion_logp(model, *pair) for pair in pairs]
    return pairs, old, refs, advantages, rewards.count(-1.25)


def make_adapter(checkpoint, device, spec):
    params = spec["training"]["adapter"]
    model = get_peft_model(load_base(checkpoint, device, spec), LoraConfig(
        r=params["rank"], lora_alpha=params["alpha"], lora_dropout=params["dropout"],
        bias=params["bias"], target_modules=params["target_modules"], task_type="CAUSAL_LM",
    ))
    if device == "cuda":
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    return model


def adapter_files(directory):
    allowed = {"adapter_config.json", "adapter_model.safetensors", "README.md", "run.json"}
    for path in directory.iterdir():
        if path.name not in allowed or not path.is_file() or path.is_symlink():
            raise ValueError("unexpected adapter file")
    return {name: file_digest(directory / name)
            for name in ("adapter_config.json", "adapter_model.safetensors")}


def fit(model, tokenizer, prompts, labels, arm, spec, *, dry):
    cfg = spec["training"]
    opt = cfg["optimizer"]
    decoder = cfg["grpo"]
    trainable = [p for p in model.parameters() if p.requires_grad]
    if not trainable or any(p.dtype != torch.float32 for p in trainable):
        raise RuntimeError("trainable LoRA parameters must be float32")
    optimizer = torch.optim.AdamW(trainable, lr=opt["learning_rate"], betas=tuple(opt["betas"]),
                                  eps=opt["epsilon"], weight_decay=opt["weight_decay"])
    batches, size, repeats = schedule(spec, dry)
    if len(prompts) != batches * size or len(labels) != len(prompts):
        raise ValueError("C9 requires the entire paired batch schedule")
    losses = []
    malformed = 0
    if arm == "grpo":
        set_seed(decoder["rollout_seed"])
    for start in range(0, len(prompts), size):
        batch = prompts[start:start + size]
        ys = labels[start:start + size]
        if arm == "grpo":
            pairs, old, refs, advantages, bad = rollout(model, tokenizer, batch, ys, decoder)
            malformed += bad
        else:
            targets = [tokenizer.encode(sft_target(y), add_special_tokens=False) + [tokenizer.eos_token_id]
                       for y in ys]
            pairs = list(zip(batch, targets, strict=True))
        model.train()
        # Accumulate over completions, with one optimizer step per full batch.
        # GRPO reuses the same trajectories, old log probabilities and rewards.
        for _ in range(repeats):
            optimizer.zero_grad(set_to_none=True)
            total_loss = torch.zeros((), device=model.device)
            for i, pair in enumerate(pairs):
                logp = completion_logp(model, *pair)
                loss = (grpo_loss(logp, old[i], refs[i], advantages[i], decoder)
                        if arm == "grpo" else -logp.mean())
                (loss / len(pairs)).backward()
                total_loss += loss.detach() / len(pairs)
            torch.nn.utils.clip_grad_norm_(trainable, opt["max_grad_norm"], error_if_nonfinite=True)
            value = total_loss.item()
            if not torch.isfinite(total_loss).item():
                raise RuntimeError("nonfinite C9 loss")
            optimizer.step()
            losses.append(value)
            print(f"{arm} update {len(losses)}/{batches * repeats} loss={value:.7g}", flush=True)
    if len(losses) != batches * repeats or not all(p.isfinite().all().item() for p in trainable):
        raise RuntimeError("C9 adapter failed the final update or finiteness check")
    return {"updates": len(losses), "losses": losses, "malformed_rollouts": malformed}


def train(checkpoint, projection, projection_sha, output, *, dry=False, arms=ARMS):
    from safetensors.torch import save_file, load_file

    spec = specification()
    device, versions = runtime(dry, spec)
    model_info = model_manifest(checkpoint, dry=dry)
    rows, tokenizer, prompts, manifest_fields = prepare(checkpoint, projection, projection_sha, spec, dry=dry)
    labels = [row["label"] for row in rows]
    output.mkdir(parents=True, exist_ok=True)
    initial = output / "initial.safetensors"
    roster = {"dry_run": dry, **manifest_fields, "runtime": versions, "checkpoint": model_info,
              "seed": spec["training"]["seed"],
              "schedule": schedule(spec, dry)}
    manifest = output / "training-roster.json"
    if manifest.exists():
        if manifest.read_bytes() != canonical(roster) + b"\n":
            raise ValueError("paired training inputs changed")
    else:
        write_json(manifest, roster)
    for arm in arms:
        target = output / arm
        target.mkdir()
        started = monotonic()
        set_seed(spec["training"]["seed"])
        model = make_adapter(checkpoint, device, spec)
        state = get_peft_model_state_dict(model)
        if initial.exists():
            clone = load_file(initial)
            if clone.keys() != state.keys() or any(
                not torch.equal(clone[key], tensor.cpu()) for key, tensor in state.items()
            ):
                raise ValueError("initial adapter does not reproduce its paired bytes")
            set_peft_model_state_dict(model, clone)
        else:
            save_file({key: tensor.detach().cpu().contiguous() for key, tensor in state.items()}, initial)
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        summary = fit(model, tokenizer, prompts, labels, arm, spec, dry=dry)
        model.save_pretrained(target, safe_serialization=True, save_embedding_layers=False)
        write_json(target / "run.json", {
            "status": "COMPLETE", "arm": arm, "dry_run": dry, **summary,
            "runtime": versions,
            "training_roster_sha256": file_digest(manifest), "initial_sha256": file_digest(initial),
            "files": adapter_files(target), "seconds": monotonic() - started,
            "peak_cuda_bytes": torch.cuda.max_memory_allocated() if device == "cuda" else None,
        })
        del state, model
    return roster


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args()
    train(args.checkpoint, args.projection, args.projection_sha256, args.output,
          arms=(args.arm,) if args.arm else ARMS)


if __name__ == "__main__":
    main()
