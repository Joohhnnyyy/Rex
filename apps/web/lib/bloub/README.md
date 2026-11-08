# Bloub animation core

Vendored from https://github.com/jeremy-prt/bloub at
`b4bb3c1b5f93c7b87a2e8d620f667c4093d97749` (MIT, Jérémy Perret, 2026).
Only the framework-free animation core is included; no Vue or export dependencies.
See LICENSE. Rex adapters and React rendering live outside this directory.

Local fix in engine.ts: interrupted transitions also preserve the interpolated eye-fit offset, preventing capsule eyes from jumping. Covered by the Rex regression suite.
