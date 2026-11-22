# Using G02: your own files, model profiles and hybrid search

Start the Workbench as before: double-click **`Start-PTP.cmd`** and open **http://127.0.0.1:8765/**. Everything from G01
still works, and lexical search needs no model.

## Your own documents

1. On the welcome page, type a project title and select **Create project**. If a project is already open, choose
   *Create or open another project…* in the project menu.
2. On **Evidence**, choose a `.md` or `.txt` file (UTF-8, up to 2 MB), pick the candidate, and select
   **Add document**.
   - Adding a file with the same name again creates a new version; the old one stays readable.
   - Adding a new file re-checks that candidate's results. A document that was not there before can turn
     "Unknown" into a decision.
3. Select **Run comparison** on **Workbench**. The requirements use the bounded parser, so write lines such as
   `Powered circulation: no.`, `Supported temperature range: 40 to 70 °C.` and
   `Independent module replacement: yes.`

## Model profiles (optional)

On **Providers**, choose a template, adjust it, then select **Save profile** and **Check**. A profile is used only after
its check says **Ready**.

- **Local models** (Ollama or any OpenAI-compatible server on this PC) cost nothing.
- **Claude API profiles** stay **blocked** until you record a spending cap and a request cap on the profile. The key is
  never typed into the page. Set an environment variable, for example `ANTHROPIC_API_KEY`, before starting the
  launcher, and put only that variable's *name* in the profile.
- **Hybrid search:** select an embedding profile, choose **Build index**, then **Use hybrid**. Results are re-checked
  automatically. Choose **Use lexical** to switch back.

## Command line

```bat
.venv\Scripts\python.exe scripts\ptp_run.py --providers
.venv\Scripts\python.exe scripts\ptp_run.py --create-project "My review"
.venv\Scripts\python.exe scripts\ptp_run.py --project PROJECT_ID --ingest notes.md --candidate CONCEPT-A
.venv\Scripts\python.exe scripts\ptp_run.py --project PROJECT_ID --run
.venv\Scripts\python.exe scripts\ptp_run.py --save-profile profile.json
.venv\Scripts\python.exe scripts\ptp_run.py --check-profile PROFILE_ID
.venv\Scripts\python.exe scripts\ptp_run.py --project PROJECT_ID --build-index PROFILE_ID
.venv\Scripts\python.exe scripts\ptp_run.py --project PROJECT_ID --retrieval-mode hybrid
```
