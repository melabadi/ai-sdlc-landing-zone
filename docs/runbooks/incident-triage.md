# Incident triage with Copilot CLI

The agentic incident triage starts when an Issue gets the `incident` label, and needs the `COPILOT_GITHUB_TOKEN` secret. Without the token, or to triage on your machine, Copilot CLI drafts the same triage with the same `operate-github` agent and `incident-evidence` skill, and you file it. Copilot does the analysis; nothing reaches GitHub until you have read the drafts and filed them under your name.

This is option B of [07-operate-github](https://github.com/melabadi/adept-assessment-northstars/tree/main/solutions/07-operate-github#use-it-the-first-time). The unit tests in `tests/test_operate_tooling.py` check the command below: one Copilot CLI command, file tools only, and the author check before the export.

## 1. File the incident without the `incident` label

The `incident` label starts the agentic workflow, and the *Operate: report an incident* form applies it. So file the incident from a terminal instead, with the form's sections in the body, and keep its number in `$incident`:

```powershell
$incident = (gh issue create --title "<what happened>" --body-file <your report>.md --label ai-sdlc --label phase:operate).Split('/')[-1]
```

Only an incident that the owner, a member, or a collaborator filed reaches Copilot. When someone outside the team reports an incident, a maintainer files it again in their own words.

## 2. Draft the triage

From the root of the repository, in PowerShell 7, check the incident's author, export it, and let Copilot draft the triage:

```powershell
Remove-Item -Recurse -Force out/operate -ErrorAction SilentlyContinue; New-Item -ItemType Directory out/operate | Out-Null
if ((gh api "repos/{owner}/{repo}/issues/$incident" --jq .author_association) -in 'OWNER', 'MEMBER', 'COLLABORATOR') {
  gh issue view $incident --json number,title,body,url > out/operate/incident.json
} else { Write-Warning "Incident #$incident was not filed by the owner, a member, or a collaborator. File it again in your own words." }
copilot --agent operate-github --available-tools 'view,glob,grep,skill,create,edit,apply_patch' --disable-builtin-mcps `
  --disallow-temp-dir --deny-tool 'read(.env)' --allow-tool 'write(followup-issue.md)' --allow-tool 'write(triage-comment.md)' `
  -p "Draft the triage of the incident in out/operate/incident.json with the incident-evidence skill."
```

The `if` exports the incident only when the owner, a member, or a collaborator filed it, and only its title and description, never its comments. Copilot runs unattended, signed in as you, so the command gives it file tools only:

- `--available-tools` leaves it no shell, no web access, and no subagents.
- `--disable-builtin-mcps` removes the GitHub tools.
- It reads only the repository: no temp directory, and no `.env` file.
- It can write only the two drafts.

What you should see: Copilot reads the skill, the exported incident, and the code, then writes the follow-up to `out/operate/followup-issue.md` (its first line is the title) and the triage comment to `out/operate/triage-comment.md`. `.gitignore` keeps `out/` out of git.

## 3. Read the drafts, then file them

You publish them under your name, so read both first. Then file them, with the severity and area labels Copilot gives in its summary and on the first line of the comment (replace `severity:3` and `area:worker`):

```powershell
Get-Content out/operate/followup-issue.md, out/operate/triage-comment.md
$followup = Get-Content out/operate/followup-issue.md
$followup | Select-Object -Skip 2 | Set-Content out/operate/followup-body.md
gh issue create --title $followup[0] --label incident-followup --label ai-sdlc --label phase:operate --parent $incident --body-file out/operate/followup-body.md
gh issue edit $incident --add-label severity:3 --add-label area:worker
gh issue comment $incident --body-file out/operate/triage-comment.md
```

Then decide whether the follow-up goes to Copilot, as with a triage from the agentic workflow.
