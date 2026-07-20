# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` — setup
- `uvicorn main:app --reload` — start the dev server (`http://127.0.0.1:8000`, docs at `/docs`)
- `pytest` — run the test suite (`tests/`; a handful of ad-hoc `test_*.py` scripts also sit at the repo root)

## Architecture

FastAPI backend for a reimbursement-automation tool: employees submit expense requests with a receipt, admins review/approve/reject them, and approved expenses are pushed into Zoho Books as ledger entries. Pairs with a separate React frontend (`../frontend`) that talks to this API — see that project's `CLAUDE.md` for the client side.

**Layering — routes → dependencies → services → repositories:**
- `api/routes/{auth,reimbursements,admin}.py` — thin FastAPI routers, one per domain, all wired through `api/dependencies/services.py` (per-request dependency factories).
- `api/dependencies/auth.py` — `get_current_user` validates the Supabase JWT from the `Authorization: Bearer` header against Supabase auth; `get_current_admin` layers on top, checking `profiles.role == 'admin'` first and falling back to `settings.admin_emails_list` (`ADMIN_EMAILS` env var) if the profile check fails.
- `services/*.py` — business logic + audit logging (`ReimbursementService`, `AuthService`, `ZohoExpenseService`, `OAuthService`, `StorageService`, `EmailService`). Routes never touch repositories directly for writes; only reads (`get_active`, `get_by_id`) go straight from route → repository.
- `repositories/base.py` (`BaseRepository[T]`) + `repositories/impl.py` — thin wrappers around `supabase-py` table calls (`profiles`, `reimbursements`, `audit_logs`); `repositories/oauth.py` does the same for the `oauth_tokens` table.
- Two Supabase clients (`core/supabase.py`): `get_supabase_client(token)` forwards the caller's JWT so **Postgres RLS** enforces employee-sees-own / admin-sees-all — routes like `GET /reimbursements` and `GET /admin/reimbursements` call the *same* `repo.get_active()` and rely entirely on RLS, not app code, for scoping. `get_service_client()` uses the service-role key (bypasses RLS) and is only used by `StorageService` to upload receipts.

**Status workflow** (`models/enums.py: ReimbursementStatus`): `Pending Review` → admin sets `Under Review` (requests clarification) → employee edits it (`ReimbursementService.update` auto-flips it back to `Pending Review`) → admin sets `Approved` or `Rejected`. Every transition goes through `ReimbursementService.update_status`, which writes an `AuditLog` row (`AuditAction`) with old/new value diffs — reimbursements are never hard-deleted, only soft-deleted (`deleted_at`), and `get_active()` filters those out.

**Zoho Books sync** (`services/zoho.py`, `services/oauth.py`): on `Approved`, `api/routes/admin.py` schedules `run_zoho_sync` as a `BackgroundTask`. `ZohoExpenseService._get_account_id_for_expense` maps `nature_of_expense` to a ledger account ID via hardcoded keyword matching (taxi/travel → `ZOHO_LEDGER_TRAVEL_EXPENSES`, hotel/stay → `ZOHO_LEDGER_BOARDING_LODGING`, etc., falling through to `ZOHO_LEDGER_MISC_EXPENSES`) then POSTs to the Zoho Books Expenses API, attaching the receipt file if one was uploaded (not for `gdrive_link` submissions). Auth is OAuth2 client-credentials-style refresh: `OAuthService` stores/refreshes the Zoho token in the Supabase `oauth_tokens` table (`migrations/02_oauth_tokens.sql`), auto-refreshing on expiry via `get_valid_access_token()`. `api/oauth.py` exposes `/oauth/status` and `/oauth/refresh` for manually checking/forcing this. Sync failure doesn't block approval — it still marks the reimbursement `Approved` but sets `zoho_sync_status="failed"` and appends the error to `remarks`. Note: `integrations/zoho/` is an empty placeholder directory; the actual Zoho logic lives in `services/zoho.py` and `services/oauth.py`, not there.

**Payment date calculation** (`utils/payment_calc.py`, covered by `tests/test_payment_calc.py`): from the submission date, add 10 business days, then snap to the nearest 5th/20th of the month if within a ±3 calendar-day window, otherwise roll to the next payment cycle. Set on `Reimbursement.expected_payment_date` at creation time (not final — admins can override on approval via `StatusUpdateRequest.expected_payment_date`, and separately mark actual payment via `POST /admin/reimbursements/{id}/mark-paid`).

**Notifications**: `EmailService` (Brevo/Sendinblue, `services/email.py`) sends a status-change email as a `BackgroundTask` on every admin decision (`Approved`, `Rejected`, `Under Review` → "Need Further Clarification").

**File uploads**: `StorageService` validates content type (`pdf`/`png`/`jpeg` only) and size (10MB max) before uploading to the Supabase Storage bucket `reimbursement-documents`, returning a public URL. Employees may submit either an uploaded file *or* a `gdrive_link` (mutually available, not both required) — `POST /reimbursements` 400s if neither is present.

**CORS** is wide open (`allow_origin_regex=".*"` in `main.py`) — there's no origin allowlist, auth is entirely bearer-token based.

## Environment

Requires a `.env` (see `.env.example`): `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `ZOHO_CLIENT_ID`/`ZOHO_CLIENT_SECRET`/`ZOHO_ORGANIZATION_ID`, `ADMIN_EMAILS` (comma-separated fallback admin list), `BREVO_API_KEY`/`FROM_EMAIL`, `FRONTEND_URL`, and the `ZOHO_LEDGER_*` / `ZOHO_*_ACCOUNT_ID` ledger-mapping vars consumed by `services/zoho.py`. `core/config.py` (`Settings`, pydantic-settings) loads and validates these; missing required vars fail at import time.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **reimburstment-backend** (493 symbols, 998 relationships, 32 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/reimburstment-backend/context` | Codebase overview, check index freshness |
| `gitnexus://repo/reimburstment-backend/clusters` | All functional areas |
| `gitnexus://repo/reimburstment-backend/processes` | All execution flows |
| `gitnexus://repo/reimburstment-backend/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
