"""Check that this landing zone is wired: every accelerator installed, set up once, and green.

The landing zone is one repository with RequestHub and the seven GitHub accelerators of AI across the software
development lifecycle installed together. This script reads the repository through GitHub CLI (`gh`) and reports, for
the shared foundation, each accelerator, and the governance settings, whether what the accelerators' READMEs set up is
there and works: the files on the default branch, the workflows GitHub has registered, the latest result of each
deterministic check, the labels, the environment, the variable, the secret, the ruleset, and the security settings.

It changes nothing and starts nothing: it reads. Sign in to `gh` as someone who administers the repository, because the
secret, the environment's rules, and the Actions settings are visible only to administrators.

Usage, from the root of a checkout (PowerShell 7 or any shell):
  python tools/check_landing_zone.py                     # the repository that `gh` resolves from the checkout
  python tools/check_landing_zone.py --repo owner/name   # another copy of the landing zone
  python tools/check_landing_zone.py --json out/landing-zone-check.json

Each line is PASS, WARN, or FAIL. WARN marks what the landing zone works without: `COPILOT_GITHUB_TOKEN`, which only
the four agentic workflows need when they run, and the nightly replay's variable. The exit code is 1 when a line fails,
otherwise 0.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# The checks a ruleset on the default branch requires: the bounds check (03-develop-github), the app's tests (CI), and the
# ADR and contract checks (02-design-github). Each runs on every pull request, so none stays pending.
REQUIRED_CHECKS = (
    "Feature stays within its bounds",
    "API and worker tests",
    "Web UI checks",
    "Browser tests",
    "ADR checks",
    "API contract compatibility",
)

FOUNDATION_FILES = (
    ".github/copilot-instructions.md",
    ".github/workflows/ci.yml",
    ".github/workflows/copilot-setup-steps.yml",
    ".github/LICENSE-ai-sdlc",
)


@dataclass
class Accelerator:
    id: str
    phase: str
    agent: str
    skills: tuple[str, ...]
    workflows: tuple[str, ...]
    form: str | None
    labels: tuple[str, ...]
    files: tuple[str, ...] = ()
    # Workflows whose latest completed run must have succeeded: the deterministic checks of the accelerator's tooling.
    green: tuple[str, ...] = ()
    # Workflows whose latest completed run on the default branch must have succeeded.
    green_on_default: tuple[str, ...] = ()


ACCELERATORS = (
    Accelerator(
        "01-plan-github", "Plan", "plan-github", ("requirements-traceability", "backlog-publish"),
        ("plan-github-brief.yml", "plan-github-checks.yml"), "01-plan-github-refine.yml",
        ("phase:plan", "brief-approved"),
        files=("planning/inputs/stakeholder-transcript.md", "planning/inputs/routing-policies.md", "planning/refine-task.md"),
        green=("plan-github-checks.yml",)),
    Accelerator(
        "02-design-github", "Design", "design-github", ("architecture-decision", "contract-impact"),
        ("design-github-review.yml", "design-github-agentic-review.lock.yml", "design-github-checks.yml"),
        "02-design-github-adr.yml", ("phase:design", "adr-needed", "standards-conflict"),
        files=("docs/architecture/inputs/reviewed-brief.md", "docs/architecture/standards/STD-API-001.md",
               "docs/architecture/adr-task.md"),
        green=("design-github-review.yml", "design-github-checks.yml")),
    Accelerator(
        "03-develop-github", "Develop", "develop-github", ("bounded-feature", "regression-validation"),
        ("develop-github-bounds.yml",), "03-develop-github-feature.yml", ("phase:develop",),
        green=("develop-github-bounds.yml",)),
    Accelerator(
        "04-test-github", "Test", "test-github", ("failure-reproduction", "review-evidence", "ci-investigation"),
        ("test-github-proof.yml", "test-github-ci-investigation.lock.yml", "test-github-checks.yml"),
        "04-test-github-defect.yml", ("phase:test", "bug", "ci:defect-reproduced", "ci:regression", "ci:infrastructure"),
        files=("tests/test_review_evidence.py", "tests/test_ci_investigation.py"),
        green=("test-github-checks.yml",)),
    Accelerator(
        "05-secure-github", "Secure", "secure-github", ("finding-triage", "verified-remediation"),
        ("secure-github-checks.yml", "secure-github-verify.yml", "secure-github-scan.yml"),
        "05-secure-github-remediate.yml", ("phase:secure",),
        files=("solutions/05-secure-github/lab/code-finding.patch",
               "solutions/05-secure-github/regression/SearchSecurityTests.cs"),
        green=("secure-github-checks.yml",), green_on_default=("secure-github-scan.yml",)),
    Accelerator(
        "06-release-github", "Release", "release-github", ("release-evidence", "workflow-investigation"),
        ("release-github-candidate.yml", "release-github-approve.yml", "release-github-summary.lock.yml",
         "release-github-checks.yml"),
        None, (), files=("tests/test_release_tooling.py",), green=("release-github-checks.yml",)),
    Accelerator(
        "07-operate-github", "Operate", "operate-github", ("incident-evidence", "regression-followup"),
        ("operate-github-incident-triage.lock.yml", "operate-github-regression-proof.yml", "operate-github-checks.yml"),
        "07-operate-github-incident.yml",
        ("phase:operate", "incident", "incident-followup", "severity:1", "severity:2", "severity:3", "severity:4",
         "area:worker", "area:api", "area:web", "area:database", "area:infrastructure", "needs-info"),
        files=("tests/test_operate_tooling.py", "docs/runbooks/incident-triage.md"),
        green=("operate-github-checks.yml",)),
)


@dataclass
class Result:
    area: str
    status: str  # PASS, WARN, or FAIL
    item: str
    detail: str = ""


@dataclass
class Report:
    repository: str
    branch: str
    commit: str
    checked_at: str
    results: list[Result] = field(default_factory=list)

    def add(self, area: str, ok: bool, item: str, detail: str = "", optional: bool = False) -> None:
        self.results.append(Result(area, "PASS" if ok else ("WARN" if optional else "FAIL"), item, detail))


class GitHub:
    """Read-only calls to the GitHub API through `gh api`."""

    def __init__(self, repo: str):
        self.repo = repo

    def get(self, path: str, paginate: bool = False):
        """The JSON of a GET, or None when GitHub answers 404 (or 204 with no body: see `exists`)."""
        command = ["gh", "api", path.replace("{repo}", self.repo)]
        if paginate:
            command += ["--paginate", "--slurp"]
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if done.returncode != 0:
            if "404" in done.stderr or "Not Found" in done.stderr:
                return None
            raise RuntimeError(f"gh api {path}: {done.stderr.strip()}")
        if not done.stdout.strip():
            return {}
        data = json.loads(done.stdout)
        if paginate:
            return [item for page in data for item in (page if isinstance(page, list) else [page])]
        return data

    def exists(self, path: str) -> bool:
        return self.get(path) is not None

    def graphql(self, query: str, **variables: str):
        command = ["gh", "api", "graphql", "-f", f"query={query}"]
        for name, value in variables.items():
            command += ["-F", f"{name}={value}"]
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=True)
        return json.loads(done.stdout)["data"]


def resolve_repo() -> str:
    done = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                          capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0 or not done.stdout.strip():
        sys.exit("error: run this from a checkout of the landing zone, or pass --repo owner/name")
    return done.stdout.strip()


def latest_run(gh: GitHub, workflow: str, branch: str | None = None) -> dict | None:
    query = "?status=completed&per_page=1" + (f"&branch={branch}" if branch else "")
    runs = (gh.get(f"repos/{{repo}}/actions/workflows/{workflow}/runs{query}") or {}).get("workflow_runs") or []
    return runs[0] if runs else None


def describe(run: dict | None) -> str:
    if run is None:
        return "no completed run yet"
    return f"{run['conclusion']}, {run['event']} run {run['id']} on {run['head_branch']} at {run['updated_at']}"


def check(gh: GitHub) -> Report:
    repo = gh.get("repos/{repo}")
    branch = repo["default_branch"]
    head = gh.get(f"repos/{{repo}}/commits/{branch}")
    report = Report(gh.repo, branch, head["sha"][:7], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    tree = {entry["path"] for entry in gh.get(f"repos/{{repo}}/git/trees/{head['sha']}?recursive=1")["tree"]}
    workflows = {Path(w["path"]).name: w for w in gh.get("repos/{repo}/actions/workflows?per_page=100")["workflows"]}
    labels = {label["name"] for label in gh.get("repos/{repo}/labels?per_page=100", paginate=True)}

    def files_present(area: str, paths: tuple[str, ...], item: str) -> None:
        missing = [p for p in paths if p not in tree]
        report.add(area, not missing, item, "missing: " + ", ".join(missing) if missing else f"{len(paths)} on {branch}")

    def labels_present(area: str, names: tuple[str, ...]) -> None:
        missing = [n for n in names if n not in labels]
        report.add(area, not missing, "labels " + ", ".join(names), "missing: " + ", ".join(missing) if missing else "")

    def green(area: str, workflow: str, branch_filter: str | None = None) -> None:
        run = latest_run(gh, workflow, branch_filter)
        report.add(area, run is not None and run["conclusion"] == "success", f"latest run of {workflow}", describe(run))

    # The shared foundation: Copilot's instructions and environment, CI, the licence, and the label every form applies.
    area = "Shared foundation"
    files_present(area, FOUNDATION_FILES, "Copilot's instructions, CI, Copilot setup steps, and the licence")
    green(area, "ci.yml", branch)
    green(area, "copilot-setup-steps.yml", branch)
    labels_present(area, ("ai-sdlc",))
    actors = gh.graphql(
        "query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) {"
        " suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 20) { nodes { login } } } }",
        owner=gh.repo.split("/")[0], name=gh.repo.split("/")[1])
    logins = {node["login"] for node in actors["repository"]["suggestedActors"]["nodes"]}
    report.add(area, "copilot-swe-agent" in logins, "the Copilot cloud agent can be assigned Issues",
               "" if "copilot-swe-agent" in logins else "allow the cloud agent in your Copilot settings")
    token = gh.exists("repos/{repo}/actions/secrets/COPILOT_GITHUB_TOKEN")
    report.add(area, token, "secret COPILOT_GITHUB_TOKEN, for the four agentic workflows",
               "" if token else "only the agentic workflows need it; see the README's one-time setup", optional=True)

    for acc in ACCELERATORS:
        area = f"{acc.id} ({acc.phase})"
        files_present(area, (f".github/agents/{acc.agent}.agent.md",)
                      + tuple(f".github/skills/{s}/SKILL.md" for s in acc.skills)
                      + ((f".github/ISSUE_TEMPLATE/{acc.form}",) if acc.form else ())
                      + acc.files,
                      f"agent {acc.agent}, skills {', '.join(acc.skills)}" + (", issue form" if acc.form else ""))
        inactive = [w for w in acc.workflows if workflows.get(w, {}).get("state") != "active"]
        report.add(area, not inactive, f"{len(acc.workflows)} workflow{'s' if len(acc.workflows) > 1 else ''} registered and active",
                   "not active: " + ", ".join(inactive) if inactive else ", ".join(acc.workflows))
        if acc.labels:
            labels_present(area, acc.labels)
        for workflow in acc.green:
            green(area, workflow)
        for workflow in acc.green_on_default:
            green(area, workflow, branch)
        if acc.id == "05-secure-github":
            variable = gh.get("repos/{repo}/actions/variables/SECURE_REPLAY_PR")
            report.add(area, variable is not None, "variable SECURE_REPLAY_PR, the nightly replay's repair",
                       f"pull request #{variable['value']}" if variable else "run solutions/05-secure-github/replay_setup.py",
                       optional=True)
            if variable is not None:
                green(area, "secure-github-verify.yml")
        if acc.id == "06-release-github":
            env = gh.get("repos/{repo}/environments/release-github")
            rules = sorted(rule["type"] for rule in (env or {}).get("protection_rules", []))
            policies = gh.get("repos/{repo}/environments/release-github/deployment-branch-policies") if env else None
            branches = sorted(p["name"] for p in (policies or {}).get("branch_policies", []))
            ok = env is not None and "required_reviewers" in rules and branches == [branch]
            report.add(area, ok, "environment release-github: only the default branch, with a required reviewer",
                       f"rules {rules}, branches {branches}" if env else "missing")

    # Governance: what keeps the gates where the READMEs put them, on a public repository.
    area = "Governance"
    rules = gh.get(f"repos/{{repo}}/rules/branches/{branch}") or []
    types = {rule["type"] for rule in rules}
    contexts = {c["context"] for rule in rules if rule["type"] == "required_status_checks"
                for c in rule["parameters"]["required_status_checks"]}
    for rule, item in (("pull_request", "a pull request before every merge"), ("deletion", "no deletion"),
                       ("non_fast_forward", "no force push")):
        report.add(area, rule in types, f"ruleset on {branch}: {item}")
    missing = [c for c in REQUIRED_CHECKS if c not in contexts]
    report.add(area, not missing, f"ruleset on {branch}: {len(REQUIRED_CHECKS)} required checks",
               "missing: " + ", ".join(missing) if missing else ", ".join(REQUIRED_CHECKS))
    permissions = gh.get("repos/{repo}/actions/permissions/workflow")
    report.add(area, permissions["default_workflow_permissions"] == "read"
               and not permissions["can_approve_pull_request_reviews"],
               "Actions token read-only by default, and unable to approve pull requests")
    forks = gh.get("repos/{repo}/actions/permissions/fork-pr-contributor-approval") or {}
    report.add(area, forks.get("approval_policy") == "all_external_contributors",
               "runs from every external contributor's fork wait for approval", forks.get("approval_policy", "unknown"))
    security = repo.get("security_and_analysis") or {}
    for feature, item in (("secret_scanning", "secret scanning"), ("secret_scanning_push_protection", "push protection")):
        report.add(area, security.get(feature, {}).get("status") == "enabled", item)
    reporting = gh.get("repos/{repo}/private-vulnerability-reporting") or {}
    report.add(area, bool(reporting.get("enabled")), "private vulnerability reporting")
    report.add(area, gh.exists("repos/{repo}/vulnerability-alerts"), "Dependabot alerts")
    return report


def print_report(report: Report) -> None:
    print(f"Landing zone check: {report.repository}, {report.branch} at {report.commit}, {report.checked_at}")
    area = None
    for result in report.results:
        if result.area != area:
            area = result.area
            print(f"\n{area}")
        print(f"  {result.status:<4}  {result.item}" + (f"  ({result.detail})" if result.detail else ""))
    counts = {status: sum(r.status == status for r in report.results) for status in ("PASS", "WARN", "FAIL")}
    print(f"\n{counts['PASS']} passed, {counts['WARN']} warning{'' if counts['WARN'] == 1 else 's'}, {counts['FAIL']} failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="owner/name of the landing zone; default: the repository of this checkout")
    parser.add_argument("--json", metavar="PATH", help="also write the results as JSON to PATH (for example under out/)")
    args = parser.parse_args()

    report = check(GitHub(args.repo or resolve_repo()))
    print_report(report)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    return 1 if any(r.status == "FAIL" for r in report.results) else 0


if __name__ == "__main__":
    sys.exit(main())
