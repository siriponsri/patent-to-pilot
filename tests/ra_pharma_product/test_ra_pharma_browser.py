"""Owner walkthrough of the RA Pharma dossier through the normal launcher and a fresh store.

Covers the skill correction, the dossier before and after the applicant report, sentence to
source page, the snapshot comparison, an edited DOCX export, conflicting editions, replay of
the superseded skill, restart and backup/restore. Chromium may reach only 127.0.0.1.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

import pytest

pytest.importorskip("pypdf")

from patent_to_pilot.workbench.letters import docx_text  # noqa: E402

LAUNCHER = Path(__file__).resolve().parents[2] / "scripts" / "ptp_run.py"


@contextmanager
def workbench(store):
    process = subprocess.Popen([sys.executable, "-X", "utf8", "-u", str(LAUNCHER), "--serve", "--port", "0",
                                "--data-dir", str(store)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               encoding="utf-8", env={**os.environ, "PTP_NO_BROWSER": "1"})
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


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def build(page):
    with page.expect_response(lambda r: r.url.endswith("/api/dossier/snapshots") and r.request.method == "POST") as resp:
        page.get_by_role("button", name="สร้างแฟ้มฉบับใหม่").click()
    assert resp.value.ok, resp.value.text()
    snap = resp.value.json()
    page.locator("#dossier-result").get_by_text(f"ฉบับที่ {snap['seq']}", exact=True).wait_for()
    return snap


def click_and_wait(page, name, path):
    with page.expect_response(lambda r: path in r.url and r.request.method == "POST") as resp:
        page.get_by_role("button", name=name).click()
    assert resp.value.ok, resp.value.text()
    page.wait_for_function("document.getElementById('dossier-notice').textContent === ''")
    return resp.value.json()


def applicant(snap):
    return next(i for i in snap["items"] if i["item_id"] == "reg.R-P54.applicant-result")


def test_owner_walkthrough(tmp_path):
    sync_api = pytest.importorskip("playwright.sync_api")
    store = tmp_path / "store"
    outside = []
    with sync_api.sync_playwright() as driver:
        executable = Path(os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or driver.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Local Playwright Chromium is unavailable")
        browser = driver.chromium.launch(executable_path=str(executable))
        with workbench(store) as url:
            context = browser.new_context(accept_downloads=True)

            def guard(route):
                if route.request.url.startswith("http://127.0.0.1"):
                    return route.continue_()
                outside.append(route.request.url)
                return route.abort()

            context.route("**/*", guard)
            page = context.new_page()
            page.goto(url)
            page.get_by_role("button", name="แฟ้มทะเบียนยา").first.click()
            page.wait_for_selector("#dossier-incoming option", state="attached")

            # 1. Version 1.0.0 mistakes the patent example for the applicant result.
            v1 = build(page)
            assert applicant(v1)["value"] == "96"
            click_and_wait(page, "ปฏิเสธ: เป็นข้อเปิดเผยของสิทธิบัตร", "/skills/corrections")
            click_and_wait(page, "เสนอรุ่นทักษะจากการแก้ไข", "/skills/proposals")
            evaluation = click_and_wait(page, "ทดสอบกับชุดพัฒนาแยก", "/skills/evaluations")
            assert evaluation["passed"] and evaluation["dev_family"] == "dev-inhaler-fpf"
            click_and_wait(page, "นำรุ่น 1.1.0 ไปใช้", "/skills/promotions")
            assert page.locator("#dossier-skill").input_value() == "1.1.0"

            # 2. Before the applicant report: the item is missing and the reply says so.
            before = build(page)
            assert applicant(before)["status"] == "missing"
            page.locator("#dossier-reg-sec").get_by_text("ค่าอยู่ในเอกสารสิทธิบัตร", exact=False).wait_for()
            assert page.locator("#dossier-letter-sec textarea[data-block='req-1']").input_value().find("อยู่ระหว่างจัดทำรายงาน") > 0

            # 3. After the report: supported from page 2; follow the sentence to its page.
            page.locator("#dossier-attachments input[value='applicant-dissolution-report-1.0']").check()
            after = build(page)
            assert applicant(after)["value"] == "91"
            req1 = page.locator("#dossier-letter-sec .letter-block").filter(has=page.locator("textarea[data-block='req-1']"))
            req1.get_by_role("button", name="หลักฐาน").click()
            page.locator("#dossier-evidence").get_by_role("button", name="applicant-dissolution-report-1.0 · หน้า 2").click()
            page.locator("#dossier-evidence mark").filter(has_text="30 นาที").wait_for()
            assert page.locator("#dossier-evidence").get_by_role("link", name="เปิด PDF หน้า 2").get_attribute("href").endswith("#page=2")
            page.keyboard.press("Escape")
            assert page.locator("#dossier-evidence").is_hidden()

            # 4. Compare the two snapshots: only the applicant item and its sentences change.
            page.locator("#dossier-history summary").click()
            page.locator("#dossier-compare").select_option(before["snapshot_id"])
            page.get_by_role("button", name="เทียบสองฉบับ").click()
            page.locator("#dossier-diff-result").get_by_text("reg.R-P54.applicant-result", exact=False).first.wait_for()
            diff = get(f"{url}api/dossier/diff/{before['snapshot_id']}/{after['snapshot_id']}")
            assert [c["item_id"] for c in diff["changed_items"]] == ["reg.R-P54.applicant-result"]
            assert "patent.example-6" in diff["unchanged_items"]

            # 5. Edit, save and download the reply. The bundled Thai font renders the sheet.
            page.wait_for_function("document.fonts.check('16px Sarabun')")
            page.locator("#dossier-letter-sec textarea[data-block='number']").fill("ที่ SCP-RA 045/2569")
            click_and_wait(page, "บันทึกฉบับแก้ไข", "/letter")
            with page.expect_download() as download:
                page.get_by_role("link", name="ดาวน์โหลด DOCX").click()
            paragraphs = docx_text(download.value.path().read_bytes())
            assert "ที่ SCP-RA 045/2569" in paragraphs and any("ร้อยละ 91" in p for p in paragraphs)

            # 6. Two editions of the report conflict until the operator chooses one.
            page.locator("#dossier-attachments input[value='applicant-dissolution-report-1.1']").check()
            conflict = build(page)
            assert applicant(conflict)["status"] == "conflict"
            page.locator("#dossier-edition").select_option("1.1")
            chosen = build(page)
            assert applicant(chosen)["value"] == "89"

            # 7. The superseded skill version replays its stored output.
            page.locator("#dossier-snapshots").select_option(v1["snapshot_id"])
            page.locator("#dossier-reopen").get_by_role("button", name="เปิด").click()
            page.locator("#dossier-result").get_by_text("ฉบับที่ 1", exact=True).wait_for()
            page.get_by_role("button", name="ตรวจซ้ำแฟ้มนี้").click()
            page.locator("#dossier-replay-sec").get_by_text("ได้เนื้อหาเดียวกัน", exact=False).wait_for()
            context.close()

        # 8. Restart on the same store, then back up and serve the copy.
        with workbench(store) as url:
            snapshots = get(url + "api/dossier/catalog")["snapshots"]
            assert len(snapshots) == 5
            assert get(f"{url}api/dossier/snapshots/{after['snapshot_id']}/verify")["citations_ok"]
            backup = tmp_path / "restore" / "workbench.sqlite3"
            done = subprocess.run([sys.executable, "-X", "utf8", str(LAUNCHER), "--backup", str(backup),
                                   "--data-dir", str(store)], capture_output=True, text=True, encoding="utf-8")
            assert done.returncode == 0, done.stdout + done.stderr
        with workbench(backup.parent) as url:
            for snap in (v1, before, after, chosen):
                check = get(f"{url}api/dossier/snapshots/{snap['snapshot_id']}/verify")
                assert check["citations_ok"] and check["rebuild_matches"]
            assert get(url + "api/dossier/catalog")["active_skill"] == "1.1.0"
        browser.close()
    assert outside == []
