# Scripts

PowerShell, because Maven's bash launcher fails on this machine (the install path contains
an apostrophe, which breaks the classworlds classpath). The Maven Wrapper avoids it.

| Script | Purpose |
|---|---|
| `dev-up.ps1` | PostGIS, then backend, AI service and frontend in their own windows |
| `dev-down.ps1` | Stops the database. `-Purge` also drops the volume |
| `test-all.ps1` | Every suite. `-WithDatabase` adds the PostGIS migration test |
| `demo-check.ps1` | Preflight. Run immediately before demonstrating, every time |
