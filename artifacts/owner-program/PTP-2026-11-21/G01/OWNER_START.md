# Start the Patent-to-Pilot Workbench (G01)

## Start and first check

1. Double-click **`Start-PTP.cmd`** in the repository folder and keep its window open.
2. The browser opens the printed URL, normally **http://127.0.0.1:8765/**. If 8765 is busy, the launcher uses the next free port and prints it.
3. Select **Open sample project**, then **Run comparison**.
4. Select a citation button, for example `DEMO-S3 · v1`, to see the exact source passage (it includes Thai text).
5. Select **Apply sample source revision**. The Changes view opens and shows the effect:
   - `DEMO-S2 · v2` (40–60 °C) replaces v1 (40–70 °C);
   - Concept A on R2 changes from Meets to Does not meet;
   - the old v1 citation still opens, marked Superseded.
6. Stop the server with **Ctrl+C** in the launcher window. Start it again later: the project, runs and both versions are still there, and the page shows a **Recorded run**.

All documents are fictional sample data. Processing runs locally in lexical mode, with no model, key or paid call.

## Support commands

Run these from the repository folder:

```bat
.venv\Scripts\python.exe scripts\ptp_run.py --doctor
.venv\Scripts\python.exe scripts\ptp_run.py --smoke
.venv\Scripts\python.exe scripts\ptp_run.py --port 8765
.venv\Scripts\python.exe scripts\ptp_run.py --run
.venv\Scripts\python.exe scripts\ptp_run.py --backup D:\backup\workbench.sqlite3
```

| Command | What it does |
|---|---|
| `--doctor` | Environment report |
| `--smoke` | Full sample workflow in a temporary store; your data is untouched |
| `--port 8765` | Starts the server without opening a browser |
| `--run` | Runs the comparison through the CLI path, on the same core as the UI |
| `--backup <path>` | Consistent copy, safe while the server runs |

## Data

The store is `%LOCALAPPDATA%\PatentToPilot\workbench\workbench.sqlite3`. Change the location with `--data-dir` or `PTP_DATA_DIR`. To start over, stop the server, then rename or delete that folder.
