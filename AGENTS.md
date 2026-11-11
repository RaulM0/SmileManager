# Repository Guidelines

## Development Status & Data Changes

The owner confirms this system is development-only and is not in production. Existing development data is disposable. Contributors may modify or delete it, apply migrations, reset databases, and regenerate fixtures as needed without additional approval. This authorization covers this project's development environment.

## Project Structure & Module Organization

SmileManager uses Django/DRF and React/TypeScript. `SmileManager/` holds configuration; `Usuarios/`, `Pacientes/`, `Citas/`, and `DiagnosticosIA/` hold domain models and migrations. API endpoints, policies, services, and backend tests live in `api/`.

Frontend code lives in `frontend/src/`, organized into pages, components, services, context, and query utilities. Browser tests are in `frontend/e2e/`; styles are in `frontend/src/styles/`. Operational and security documentation lives in `docs/`. Treat `frontend/dist/`, `staticfiles/`, and clinical `media/` as generated or runtime assets.

## Build, Test, and Development Commands

Use Python 3.13, matching CI. Install Python dependencies with `python -m pip install -r requirements.txt`; run frontend commands from `frontend/`.

- `python3 scripts/setup_dev_security.py` and `docker compose --env-file .local-ops.env up --build -d`: starts the local backend and PostgreSQL; consult `docs/operations/docker-local.md`.
- `npm ci`: installs locked frontend dependencies.
- `npm run dev`: starts Vite on port 5173, proxying API requests to port 8000.
- `npm run build`: builds frontend assets.
- `npm run typecheck` and `npm run lint`: check TypeScript and ESLint rules.
- `DJANGO_SETTINGS_MODULE=SmileManager.settings_test python manage.py test --noinput`: runs isolated backend tests.
- `npm test`: runs Vitest; `npm run test:e2e`: runs Playwright.

## Coding Style & Naming Conventions

Use four-space Python indentation and snake_case functions/modules. Use two-space TypeScript indentation, PascalCase components, and `use*` hook names. Follow nearby code and ESLint; no repository-wide formatter is configured. Keep endpoint handlers focused, business logic in services, and authorization enforced server-side through clinic context and resource policies.

## Testing Guidelines

Name backend tests `test_*.py`, frontend tests `*.test.ts(x)`, and browser tests `*.spec.js`. Use synthetic fixtures and isolated databases/storage. PostgreSQL tests require `SmileManager.settings_postgres_test` and `PHASE2_TEST_DATABASE_URL` pointing to an isolated maintenance database named `postgres`. Redis integration tests require `RATE_LIMIT_TEST_REDIS_URL`. Cover authorization, cross-clinic access, concurrency, and regressions; no numeric coverage threshold is configured.

## Commit & Pull Request Guidelines

History uses concise imperative subjects, such as “Improve administration UI”; Conventional Commits are not consistently required. Keep commits focused. PRs should explain behavior, reference relevant issues, report validation and limitations, and include screenshots for UI changes. Document migration, configuration, deployment, and rollback implications.

## Security & Configuration

Never commit patient data, databases, credentials, or custody keys. Run `python scripts/check_sensitive_tracking.py` before review. Maintain document-history and session/MFA controls in application behavior; development fixtures may be reset. See `docs/security/etapa-2-resultados.md` for future production requirements.

## Project Navigation Map

Start repository navigation at `docs/mapa/Inicio.md` and the relevant module index. File notes provide source paths, symbols and static import links; read the real source before changing behavior. Refresh with `python3 scripts/build_project_map.py` after adding, moving or changing indexed source; verify with `--check`. Generated notes are navigation aids, not authoritative architecture or complete dependency analysis. Keep private data and credentials out of notes.


## Codex Commits & Obsidian

When committing this repository through Codex, run `python3 scripts/codex_git.py commit ...` (also supports `-a`); it enables the map pre-commit hook for that invocation. The Codex `PreToolUse` hook in `codex/hooks.json` routes ordinary `git commit` shell calls through this adapter when loaded and trusted. Use `python3 scripts/codex_with_obsidian.py` to launch Codex with this hook without changing global Git settings. The hook indexes staged content, preserves unstaged source/note edits, and prunes generated notes for deleted sources. Do not use `command git`, absolute Git executables, nested shells or `--no-verify` to bypass it. Review the generated staged map before finalizing commits.
