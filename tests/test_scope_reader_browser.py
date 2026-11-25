"""Exercise the Thai reader through the normal launcher and a fresh local store."""

from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys

import pytest


@contextmanager
def workbench(store):
    launcher = Path(__file__).resolve().parents[1] / "scripts" / "ptp_run.py"
    process = subprocess.Popen(
        [sys.executable, "-X", "utf8", "-u", str(launcher), "--serve", "--port", "0",
         "--data-dir", str(store)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8",
    )
    try:
        for line in process.stdout:
            if line.strip().startswith("URL:"):
                yield line.split("URL:", 1)[1].strip()
                return
        pytest.fail("Workbench stopped before printing its local URL")
    finally:
        process.terminate()
        process.wait(timeout=10)
        process.stdout.close()


def run_result(page, action):
    with page.expect_response(lambda r: r.url.endswith("/api/scope/run") and r.request.method == "POST") as response:
        action()
    assert response.value.ok
    trace = response.value.json()
    page.locator("#scope-result").get_by_text(trace["id"], exact=False).wait_for()
    return trace


def check_health_and_pharma_citations(page):
    family = page.locator("#scope-family")
    for group, family_id, name in [("กฎหมายไทย", "demo-th-eta", "ลายมือชื่อ"),
                                  ("กฎหมายไทย", "demo-th-information", "ข้อมูลข่าวสาร"),
                                  ("กฎหมายไทย", "demo-th-healthlaw", "เครื่องมือแพทย์"),
                                  ("กฎหมายไทย", "demo-th-drug-act", "ยา"),
                                  ("กฎหมายไทย", "demo-th-national-health", "สุขภาพ"),
                                  ("สิทธิบัตรภาษาอังกฤษ", "demo-en-paperclip", "คลิปหนีบกระดาษ"),
                                  ("สิทธิบัตรภาษาอังกฤษ", "demo-en-metformin", "เมตฟอร์มิน"),
                                  ("สิทธิบัตรภาษาอังกฤษ", "demo-en-pharma", "กลบรส"),
                                  ("สิทธิบัตรภาษาอังกฤษ", "demo-en-inhaler", "สูดยา"),
                                  ("สิทธิบัตรภาษาอังกฤษ", "demo-en-blister", "บรรจุภัณฑ์")]:
        options = family.locator("optgroup").filter(has=page.locator(f'option[value="{family_id}"]'))
        assert options.get_attribute("label") == group
        assert name in options.locator(f'option[value="{family_id}"]').inner_text()
    run_result(page, lambda: family.select_option("demo-th-healthlaw"))
    advertising = run_result(page, lambda: page.locator("#scope-example").select_option("md-advertising-2551"))
    provision = next(ev for ev in advertising["evidence"] if "๕๗" in ev["locator"])
    page.locator(".scope-answers").get_by_role("button", name="เปิดหลักฐาน · " + provision["locator"]).first.click()
    assert page.locator(".scope-quote").inner_text() == provision["quote"]
    assert provision["sha256"] in page.locator("#drawer-body").inner_text()
    page.keyboard.press("Escape")
    run_result(page, lambda: family.select_option("demo-en-pharma"))
    pharma = run_result(page, lambda: page.locator("#scope-example").select_option("pharma-18"))
    for child, parent in [("Claim 18", "Claim 17"), ("Claim 17", "Claim 1")]:
        row = page.locator(".scope-connection.stated").filter(
            has=page.get_by_role("button", name=child, exact=True)
        ).filter(has=page.get_by_role("button", name=parent, exact=True))
        assert row.locator(".scope-node").all_text_contents() == [child, parent]
        row.locator(".scope-edge").press("Enter")
        span = next(ev for ev in pharma["evidence"] if ev["locator"] == child)
        assert page.locator("#drawer-title").inner_text() == child
        assert page.locator(".scope-quote").inner_text() == span["quote"]
        assert span["meaning_th"] in page.locator("#drawer-body").inner_text()
        page.locator("#drawer-body").get_by_role("button", name=parent, exact=True).click()
        assert page.locator("#drawer-title").inner_text() == parent
        if parent == "Claim 17":
            page.locator("#drawer-body").get_by_role("button", name="Claim 1", exact=True).click()
            root = next(ev for ev in pharma["evidence"] if ev["locator"] == "Claim 1")
            assert page.locator(".scope-quote").inner_text() == root["quote"]
        page.keyboard.press("Escape")
    # Follow the same reading path for every preset in the shipped catalog.
    example = page.locator("#scope-example")
    for family_id in family.locator("option").evaluate_all("options => options.map(o => o.value)"):
        first = run_result(page, lambda: family.select_option(family_id))
        for preset in example.locator("option").evaluate_all("options => options.map(o => o.value)"):
            trace = first if preset == first["example_id"] else run_result(page, lambda: example.select_option(preset))
            assert (trace["family_id"], trace["example_id"]) == (family_id, preset)
            assert trace["question_th"] in page.locator("#scope-result").inner_text()
            if family_id == "demo-en-metformin":
                assert "ทั้งหมด 37 ข้อ · ชุดตัวอย่างคัดข้อ 1, 3, 4, 7" in page.locator("#scope-result").inner_text()
            if trace["evidence"]:
                page.locator(".scope-answers button").first.click()
                assert page.locator(".scope-quote").inner_text() == trace["evidence"][0]["quote"]
                page.keyboard.press("Escape")
            else:
                assert trace["status"] == "qualified"


def test_scope_reader_keyboard_compare_export_restart(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as driver:
        executable = Path(driver.chromium.executable_path)
        if not executable.is_file():
            pytest.skip("Local Playwright Chromium is unavailable")
        browser = driver.chromium.launch(executable_path=str(executable))
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        with workbench(tmp_path / "store") as url:
            page.goto(url)
            page.get_by_role("button", name="เปิดโต๊ะอ่านเอกสาร").click()
            page.locator("#scope-family").select_option("demo-th-eta")
            question = page.locator("#scope-question")
            question.fill("คำถามนอกชุดตัวอย่าง")
            assert page.locator("#scope-submit").is_disabled()
            page.get_by_role("button", name="ใช้คำถามตัวอย่าง").click()
            old = run_result(page, lambda: page.locator("#scope-submit").click())
            new = run_result(page, lambda: page.locator("#scope-example").select_option("eta-2562-no3"))
            changes = page.locator(".scope-changes")
            assert "คงเดิม" in changes.locator("li").nth(0).inner_text()
            assert "เปลี่ยน" in changes.locator("li").nth(1).inner_text()
            changes.locator("li").nth(0).get_by_role("button").first.click()
            assert old["evidence"][0]["sha256"] in page.locator("#drawer-body").inner_text()
            page.keyboard.press("Escape")
            # Both the changed law and its prior citation can be reopened independently.
            assert old["source_sha256"] != new["source_sha256"]
            qualified = run_result(page, lambda: page.locator("#scope-example").select_option("eta-case"))
            assert qualified["status"] == "qualified"
            assert "ยังยืนยันไม่ได้" in page.locator(".scope-answers").inner_text()
            run_result(page, lambda: page.locator("#scope-family").select_option("demo-en-paperclip"))
            patent = run_result(page, lambda: page.locator("#scope-example").select_option("paperclip-4"))
            assert "คงเดิม" in changes.locator("li").nth(0).inner_text()
            assert "เปลี่ยน" in changes.locator("li").nth(1).inner_text()
            edge = next(e for e in patent["edges"] if e["type"] == "stated")
            span = next(e for e in patent["evidence"] if e["id"] == edge["evidence_id"])
            button = page.locator(".stated .scope-edge").first
            button.focus()
            page.keyboard.press("Enter")
            assert page.locator(".scope-quote").inner_text() == span["quote"]
            assert span["meaning_th"] in page.locator("#drawer-body").inner_text()
            assert span["locator"] in page.locator("#drawer-title").inner_text()
            page.keyboard.press("Escape")
            assert button.evaluate("(b) => document.activeElement === b")
            page.locator(".scope-links").locator("..").locator("summary").click()
            page.locator(".scope-links").get_by_text("ต้นฉบับระบุ", exact=False).first.click()
            assert page.locator(".scope-quote").inner_text() == span["quote"]
            page.keyboard.press("Escape")
            with page.expect_download() as download:
                page.get_by_role("button", name="ส่งออกผลและหลักฐาน (JSON)").click()
            assert json.loads(download.value.path().read_text(encoding="utf-8")) == patent
            check_health_and_pharma_citations(page)
            page.get_by_role("button", name="Workbench", exact=True).click()
            page.get_by_role("button", name="Open sample project").wait_for()
        with workbench(tmp_path / "store") as url:
            page.goto(url)
            page.get_by_role("button", name="อ่านเอกสาร", exact=True).click()
            page.locator("#scope-history summary").click()
            page.locator("#scope-runs").select_option(old["id"])
            page.get_by_role("button", name="เปิดผลเดิม", exact=True).click()
            page.locator("#scope-result").get_by_text(old["id"], exact=False).wait_for()
            assert page.locator("#scope-example").input_value() == old["example_id"]
            page.locator(".scope-answers button").first.click()
            assert page.locator(".scope-quote").inner_text() == old["evidence"][0]["quote"]
            assert old["evidence"][0]["sha256"] in page.locator("#drawer-body").inner_text()
        assert not errors
        browser.close()
