# One-time setup files

These files can't be written into place remotely (Makefile, CI workflow, pre-commit config, Claude Code MCP config are protected). Run once from the repo root:

```bash
cp setup/Makefile.template Makefile
mkdir -p .github/workflows && cp setup/ci.yml .github/workflows/ci.yml
cp setup/pre-commit-config.yaml .pre-commit-config.yaml
cp mcp.json.example .mcp.json
```
