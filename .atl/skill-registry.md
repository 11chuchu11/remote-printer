# Skill Registry — remote-printer

Generated: 2026-07-06

## User Skills

| Skill | Trigger |
|---|---|
| `branch-pr` | Creating a pull request, opening a PR, preparing changes for review |
| `issue-creation` | Creating a GitHub issue, reporting a bug, requesting a feature |
| `judgment-day` | "judgment day", "doble review", "que lo juzguen", adversarial review |
| `go-testing` | Writing Go tests, teatest, table-driven tests (not applicable to this project) |

## SDD Skills

| Skill | Phase |
|---|---|
| `sdd-explore` | Investigate an idea, read codebase, compare approaches |
| `sdd-propose` | Create change proposal with intent, scope, approach |
| `sdd-spec` | Write specs from proposal |
| `sdd-design` | Architecture design from proposal |
| `sdd-tasks` | Break design/spec into tasks |
| `sdd-apply` | Implement tasks |
| `sdd-verify` | Validate implementation against specs |
| `sdd-archive` | Close change, persist final state |

## Project Conventions (Compact Rules)

- **Language**: Python 3.12
- **Commits**: English, imperative mood
- **Bot**: Long polling only — no HTTP server, no webhooks
- **Security**: Never expose port 631 to internet; never commit .env
- **Dependencies**: If adding Python deps to bot/bot.py, update bot/Dockerfile
- **Secrets**: If a token is exposed (log, commit, chat) → revoke immediately
- **CUPS**: Read CONTEXT.md before modifying cups/ Dockerfile, entrypoint.sh, or docker-compose.yml
- **No tests**: No test framework in project — verify features manually via docker compose

## Project Files

| Path | Purpose |
|---|---|
| `bot/config.py` | Env vars, auth helpers, user names |
| `bot/cups.py` | CUPS subprocess abstraction |
| `bot/storage.py` | SQLite: history, logs, print_config |
| `bot/handlers/print.py` | File receive + interactive job keyboard |
| `bot/handlers/callbacks.py` | Inline button dispatch (pj:* / cfg:*) |
| `bot/handlers/keyboards.py` | Keyboard builders + text formatters |
| `bot/handlers/queue.py` | /status /queue /cancel /history |
| `bot/handlers/config.py` | /config interactive |
| `bot/handlers/help.py` | /start /help |
| `bot/handlers/common.py` | reply_unauthorized |
| `bot/bot.py` | Entry point, handler registration |
| `cups/entrypoint.sh` | dbus + avahi + cupsd + printer setup |
| `scripts/*.sh` | User management (add/remove/edit/list) |
| `CONTEXT.md` | Solved problems, gotchas, history |
