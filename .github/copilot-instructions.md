# Copilot instructions for this repository

This repository holds **RequestHub**, a small request-and-approval portal with synthetic data: requesters ask for equipment, access, or services, a reviewer triages each request, and an approver decides. It is also a landing zone: the seven GitHub accelerators of AI across the software development lifecycle are installed in it, one per SDLC phase (see `README.md`).

## Repository map

| Path | What lives there |
| --- | --- |
| `app/` | RequestHub: ASP.NET Core 10 API (`src/RequestHub.Api`), domain + EF Core (`src/RequestHub.Core`), notification worker (`src/RequestHub.Worker`), React web UI (`web/`), integration tests (`tests/`), API contract (`contracts/`), and the Bicep modules that host it (`infra/`). |
| `.github/workflows/ci.yml` | CI: the API and worker tests on PostgreSQL, the web UI checks, and the browser tests, on every pull request. |
| `.github/workflows/copilot-setup-steps.yml` | The Copilot cloud agent's environment: .NET, Node.js, Playwright, Python with the accelerators' packages, and PostgreSQL. |
| `.github/agents/`, `.github/skills/`, `.github/workflows/`, `.github/ISSUE_TEMPLATE/`, `.github/instructions/`, `.github/codeql/` | The accelerators: seven custom agents (`<phase>-github`), their skills, workflows, and issue forms. `*.lock.yml` files are compiled by gh-aw v1.2.2 from the `.md` file next to them: never edit them by hand. |
| `planning/` | Plan: the workshop notes and policies a brief cites, Copilot's task, and the publisher's unit tests. |
| `docs/architecture/` | Design: the approved standards, the reviewed brief, Copilot CLI's task, and the ADRs in `adr/`. |
| `docs/runbooks/` | Runbooks, such as the incident triage with Copilot CLI. |
| `docs/see-it-work/` | The recorded end-to-end run: one release cycle through the seven phases, with its screenshots. |
| `site/` | The guide to that run on GitHub Pages: `python site/build.py` builds it into `_site/` and checks its links; `.github/workflows/pages.yml` publishes it. |
| `tests/` | Unit tests of the accelerators' scripts (Test, Release, Operate): `python -m unittest discover -s tests`. |
| `solutions/05-secure-github/` | Secure: the lab patch, the regression reference, the replay setup, and their unit tests. Never apply the lab patch to `main`. |
| `tools/check_landing_zone.py` | Checks that every accelerator is installed, set up, and green. |

## Build and test

- API and worker: `dotnet test --solution app/RequestHub.slnx` (needs PostgreSQL on `localhost:5432`, user `requesthub`, password `devpass`; the Copilot cloud agent environment starts one automatically).
- Web UI: `npm ci --prefix app/web`, then `npm run typecheck --prefix app/web`, `npm test --prefix app/web`, `npm run build --prefix app/web`.
- Run locally: `dotnet run --project app/src/RequestHub.Api` (persona switcher, http://localhost:5080).
- The accelerators' scripts: Python 3.12+, standard library plus `jsonschema` (`pip install -r planning/requirements.txt`). Set `PYTHONDONTWRITEBYTECODE=1` before running their tests, so no `__pycache__` lands in `.github/` or `tests/`.

## Rules

- **Human approval is sacred.** Only a person with the Approver role can approve or reject. Never add an approval path to triage providers, agents, or tools. A requester can never decide their own request.
- **Authorization lives in the API** (`RequestWorkflow`), not only in the UI. Every new endpoint checks role and department access and has a negative test.
- **Never weaken a test, guard, or validation to make a check pass.** Fix the code, or explain why the test is wrong in the PR.
- **Contract `requesthub.v1` is additive-only.** If the API shape changes, regenerate `app/contracts/openapi.json` with `UPDATE_CONTRACT=1 dotnet test --solution app/RequestHub.slnx` and describe the change in the PR.
- **Synthetic data only.** No real people, customers, secrets, tenant ids, or subscription ids in code, tests, docs, or commit messages.
- **Never expose a tenant.** No deployed host names, resource names, GUIDs, account names, or e-mail addresses in code, docs, Issues, pull requests, or comments.
- Keep changes small and reviewable; add or update tests for every behavior change; update the relevant README when behavior or commands change.

## Code conventions

- C#: minimal APIs, `TypedResults`, problem details with a stable `code` (for example `decision.self_approval`). Business errors return `WorkflowError`. Audit every business action with `AuditEvent`.
- Tests: xUnit v3 integration tests against real PostgreSQL through `ApiFixture`; use personas (`u-ava` requester, `u-ben` reviewer, `u-chloe` approver, `u-dan` admin, `u-hugo` requester+approver) via the `X-RequestHub-User` header.
- Web: React + TypeScript, no UI framework, all strings in the EN/FR dictionaries, accessible markup (labels, landmarks, keyboard support).
