"""Restage the exact E4b snapshot and wheel digests on an L4 without the E4b volume."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def main(work):
    config = json.loads((work / "L1E_FROZEN_CONFIG.json").read_bytes())
    for name, digest in config["restage_lf_sha256"].items():
        data = (work / name).read_bytes().replace(b"\r\n", b"\n")
        if sha256(data).hexdigest() != digest:
            raise ValueError(f"restaging file differs from freeze: {name}")
    subprocess.run([sys.executable, str(work / "scripts/runpod_e4b_stage.py"),
                    str(work / "data/E4b_model.json"), str(work / "model")], check=True)
    stage = json.loads((work / "data/E4b_stage.json").read_bytes())
    with TemporaryDirectory(prefix="c2-wheels-", dir=work) as temp:
        directory = Path(temp)
        requirements = directory / "requirements.txt"
        requirements.write_text("".join(f"{wheel['name']}=={wheel['version']} --hash=sha256:{wheel['sha256']}\n"
                                        for wheel in stage["dependencies"]), encoding="utf-8")
        pip = [sys.executable, "-m", "pip", "--disable-pip-version-check"]
        subprocess.run([*pip, "download", "--only-binary=:all:", "--require-hashes", "--no-deps",
                        "--dest", str(directory), "-r", str(requirements)], check=True)
        actual = {path.name: sha256(path.read_bytes()).hexdigest() for path in directory.glob("*.whl")}
        expected = {wheel["wheel"]: wheel["sha256"] for wheel in stage["dependencies"]}
        if actual != expected:
            raise ValueError("downloaded wheels differ from E4b")
        subprocess.run([*pip, "install", "--no-index", "--no-deps", "--no-compile", "--target",
                        str(work / "deps"), *map(str, sorted(directory.glob("*.whl")))], check=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
