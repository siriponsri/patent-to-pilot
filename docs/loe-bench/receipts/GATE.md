# GATE

- Run start (UTC) `2026-11-28T05:12:47+00:00`
- Code commit `0b9bf827936fd1344f0e788bcc1b27ad71d487a9`
- `FROZEN_CONFIG.json` SHA-256 (LF) `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39`
- `S0_INPUT_MANIFEST.json` SHA-256 (LF) `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d`
- `PREREG_LOCK.json` canonical OSF record SHA-256 `3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77`
- Custodian projection SHA-256 `18477704bf21ce1f68d03ef9dcc19ec287194ca6695fa9c62990e80611ffb1ad`

Run from `loe-bench/` with Python 3.12.10.

```powershell
& 'C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe' -B scripts/freeze_gate.py 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/gate/custodian_projection.json' --ob-dir 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/ob_editions'
```

Verdict **PASS**.

Technical retry. None.
