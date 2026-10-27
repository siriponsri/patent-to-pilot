# Tooling for this migration

27 October 2026: Windows PowerShell, Git and Python 3.12.10 were used through the existing `rtk proxy` command. RTK's native `git` filter reported a missing Claude config directory; explicit `rtk proxy git` worked. No configuration or hook change was made. A no-hook notice is informational; do not run init to silence it.

PDF inspection used the existing PyMuPDF installation for text extraction, page counts and hashes. No bundled pack scripts, macros, installers or model jobs were executed. Root `.agents/skills` was absent; relevant user skills were read from the existing user skill directory. No agent, memory backend or scheduler was installed or activated.

Checks and exact commands: [verification](healthtech/verification.json). Provider modules and durable budget behavior were preserved. No browser/native desktop automation, credentials or global account/config changes were used for this repo task.
