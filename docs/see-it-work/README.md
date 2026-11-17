# See it work: one release cycle through the seven phases

On 17 November 2026, from 13:37 to 18:59 UTC, all seven accelerators in this landing zone ran live, end to end, on one backlog. Stakeholder notes became a published backlog. The backlog became an accepted architecture decision and a merged feature. A planted defect was fixed test-first, and a planted SQL injection was repaired. Release `demo-v1.0.0` was published, and an incident became a proven regression fix on `main`. Nothing was mocked: every Copilot session, code review, agentic workflow, and check below ran for real, and each step links to it.

A GitHub Copilot agent session drove the run in the repository owner's account. The owner made all nine decisions in the chat with that session, and the session carried each one out in GitHub: it applied a label, posted a review, started a workflow, or merged. It filed each Issue from the command line, with the fields and labels of the accelerator's issue form. In a team, the people who decide make these clicks themselves. All data is synthetic. The Test and Secure defects are those accelerators' labs, planted on purpose on branches that never merge, and the incident is the Operate accelerator's sample report.

- **What came out:** a brief and an epic with four tasks, ADR 0001, the routing confirmation feature, a proven fix and a proven repair on their labs, release [`demo-v1.0.0`](https://github.com/melabadi/ai-sdlc-landing-zone/releases/tag/demo-v1.0.0), and a proven fix for the incident.
- **Time:** 5 hours 22 minutes from the first Issue to the last merge. 3 hours 7 minutes of that was waiting for the owner's decisions on the feature and the release; the rest of the cycle took about 2 hours 15 minutes, with five phases running in parallel.
- **Cost:** about 524 AI credits: 48.3 for eight Copilot cloud agent sessions, 398.5 for five Copilot code reviews, and about 77 for four agentic workflows. 212.7 minutes of GitHub-hosted runners, free on this public repository.
- **What it found:** [seven things](#what-the-run-found) that a single accelerator's run doesn't show, such as whose name Copilot's pull requests carry, and a package path that collided with the source repository's.

Present it from this page: each step shows what happened, its screenshots, and what to observe. Nothing needs to be started. Times are UTC.

## The run at a glance

```mermaid
gantt
  title One release cycle, 17 November 2026 (UTC)
  dateFormat HH:mm
  axisFormat %H:%M
  todayMarker off
  section 1 Plan
    Copilot drafts the brief :p1, 13:37, 13:42
    Validate, decide, publish, merge :p2, 13:42, 13:47
  section 2 Design
    Design review and ADR :d1, 13:47, 13:54
    Code review, revision, re-review :d2, 13:54, 14:15
    Decide, merge :d3, 14:15, 14:28
  section 3 Develop
    Copilot builds the feature :v1, 13:47, 14:14
    Reviewer test, Copilot fix :v2, 14:14, 14:37
    Waiting for the owner :crit, v3, 14:37, 16:22
  section 4 Test
    Tests first, then the fix :t1, 13:38, 13:49
    Proof, evidence, decide :t2, 13:49, 13:56
  section 5 Secure
    Review and CodeQL find it :s1, 13:39, 13:44
    Copilot repairs it :s2, 13:46, 14:00
    Replay, rescan, decide :s3, 14:00, 14:24
  section 6 Release
    Candidate, fix, candidate :r1, 16:23, 16:41
    Agentic summary :r2, 16:41, 16:50
    Waiting for the approver :crit, r3, 16:50, 18:11
    Approve, publish, verify :r4, 18:11, 18:15
  section 7 Operate
    Agentic triage :o1, 18:15, 18:21
    Copilot writes the test and fix :o2, 18:26, 18:39
    Proof, decide, merge :o3, 18:41, 18:59
```

| Phase | Started with | Copilot produced | What decided it was complete | The owner decided |
| --- | --- | --- | --- | --- |
| [1. Plan](#1-plan-notes-to-a-published-backlog-in-8-minutes) | Issue [#13](https://github.com/melabadi/ai-sdlc-landing-zone/issues/13), in the Plan form's format | A brief and a backlog that cite the notes, [#14](https://github.com/melabadi/ai-sdlc-landing-zone/pull/14) | *Validate the brief*: VALID | 13:44 approve, publish, merge: epic [#18](https://github.com/melabadi/ai-sdlc-landing-zone/issues/18), tasks #19 to #22 |
| [2. Design](#2-design-a-reviewed-and-accepted-adr) | Issue [#28](https://github.com/melabadi/ai-sdlc-landing-zone/issues/28), for task #19, and `/design-review` | The standards that apply; ADR 0001, [#29](https://github.com/melabadi/ai-sdlc-landing-zone/pull/29) | *ADR checks* and *API contract compatibility* | 14:00 send the review back; 14:20 accept, with an added open question |
| [3. Develop](#3-develop-the-feature-and-a-reviewers-test-that-caught-a-defect) | Issue [#26](https://github.com/melabadi/ai-sdlc-landing-zone/issues/26), for task #21 | The feature and its tests, [#27](https://github.com/melabadi/ai-sdlc-landing-zone/pull/27) | *Feature stays within its bounds* and CI, with the reviewer's test | 16:22 approve and merge |
| [4. Test](#4-test-a-defect-fixed-test-first-and-a-red-ci-run-explained) | Issue [#15](https://github.com/melabadi/ai-sdlc-landing-zone/issues/15), on a lab branch | Failing tests, then the fix, [#16](https://github.com/melabadi/ai-sdlc-landing-zone/pull/16) | The proof: 4 of 4 tests fail before the fix and pass after it | 13:55 approve the fix, which stays on the lab |
| [5. Secure](#5-secure-an-injection-found-twice-and-a-repair-proven-by-a-replay) | Lab pull request [#17](https://github.com/melabadi/ai-sdlc-landing-zone/pull/17), then Issue [#23](https://github.com/melabadi/ai-sdlc-landing-zone/issues/23) | The finding; the regression, then the repair, [#24](https://github.com/melabadi/ai-sdlc-landing-zone/pull/24) | The trusted replay and a CodeQL rescan | 14:23 approve the repair; close the lab |
| [6. Release](#6-release-a-release-that-waited-for-its-approver) | `release-github-candidate.yml`, version 1.0.0 | The release summary | The candidate's gates, and the approval's checks | 18:11 approve and publish `demo-v1.0.0` |
| [7. Operate](#7-operate-from-an-incident-to-a-proven-fix-in-28-minutes) | Incident [#32](https://github.com/melabadi/ai-sdlc-landing-zone/issues/32), the sample report | The triage and follow-up [#33](https://github.com/melabadi/ai-sdlc-landing-zone/issues/33); the test and the fix, [#34](https://github.com/melabadi/ai-sdlc-landing-zone/pull/34) | *Prove the regression test*: PROVEN | 18:26 send the follow-up to Copilot; 18:57 approve and merge |

Plan, Test, and Secure started together. Design and Develop started from the backlog Plan published, Release from `main` once the feature merged, and Operate once the release was out.

## Step by step

### 1. Plan: notes to a published backlog in 8 minutes

At 13:37:19 the session filed Issue [#13](https://github.com/melabadi/ai-sdlc-landing-zone/issues/13) in the *Plan: refine requirements with Copilot* form's format, and assigned it to Copilot with the `plan-github` agent. It asks Copilot to refine the assisted request triage requirements from the workshop notes in [`planning/inputs/`](../../planning/inputs/).

![Issue #13, "Plan: refine assisted-triage requirements", asking Copilot to refine the RequestHub assisted request triage requirements with the requirements-traceability skill](images/01-plan-1-issue.png)

Copilot opened draft pull request [#14](https://github.com/melabadi/ai-sdlc-landing-zone/pull/14) 7 seconds later. Its session ran from 13:37:31 to 13:41:59, 4 minutes 28 seconds, on GPT-6 Luna, and used 1.9 AI credits. It changed only `planning/brief/`: the brief, and `backlog.json`, where every statement cites a transcript paragraph or a policy.

![Copilot's session for the brief, listing planning/brief/brief.md and planning/brief/backlog.json among its changes](images/01-plan-2b-session.png)

Copilot's push started no workflow until the session approved the four waiting runs, at 13:42:42. *Validate the brief* then reported `VALID - 4 tasks, 4 open questions, 1/2 conflicts unresolved`: the brief left one of the two conflicts in the notes, and four questions, for people to settle instead of inventing answers.

![The "Validate the brief" job of the Plan workflow on pull request #14: the brief validation summary](images/01-plan-3-validate.png)

![The planning/brief folder in the repository: backlog.json and brief.md, next to the inputs](images/01-plan-4-brief.png)

**The owner's decision, at 13:44:30:** approve the brief. The session applied the `brief-approved` label at 13:44:40, which started the publisher ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44095785412)). At 13:45:28, 48 seconds later, the epic [#18](https://github.com/melabadi/ai-sdlc-landing-zone/issues/18) and its tasks [#19](https://github.com/melabadi/ai-sdlc-landing-zone/issues/19) to [#22](https://github.com/melabadi/ai-sdlc-landing-zone/issues/22) were Issues, each with its source excerpts. The brief merged at 13:46:20 as [`29ba488`](https://github.com/melabadi/ai-sdlc-landing-zone/commit/29ba488), and #13 closed.

![Pull request #14, merged: the comment "Backlog published after review", listing the epic and its four tasks](images/01-plan-5-published.png)

![Pull request #14, "Refine assisted-triage requirements backlog", merged into main from Copilot's branch](images/01-plan-2-pull-request.png)

![Epic #18, "[Plan/Copilot] Assisted request triage", published from planning/brief/backlog.json, with its four tasks linked as sub-issues](images/01-plan-6-epic.png)

**What to observe:** 8 minutes 9 seconds from the request to a published backlog that traces every task to its source, the lead time the Plan accelerator tracks. The brief kept what it couldn't settle open for people, and only a person's label published it.

### 2. Design: a reviewed and accepted ADR

At 13:47:18 the session filed Issue [#28](https://github.com/melabadi/ai-sdlc-landing-zone/issues/28) in the *Design: architecture decision with Copilot* form's format. It names backlog task #19 and asks how RequestHub should add a live AI triage provider. The session commented `/design-review` at 13:47:22, and assigned the Issue to Copilot with `design-github`.

![Issue #28, "Design: how should RequestHub add a live AI triage provider?", naming backlog item #19, with the labels ai-sdlc, phase:design, and standards-conflict](images/02-design-1-issue.png)

The agentic design review answered at 13:51:41, 4 minutes 19 seconds after the command ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44096244741)). It listed the architecture standards that apply, each with its version and scope, and added the labels `adr-needed` and `standards-conflict`. Its footer reports about 22 AI credits, plus about 1 for threat detection.

![The agentic design review on Issue #28: the standards that apply, quoted with their identifiers, versions, and scopes](images/02-design-2-review.png)

Copilot's session ran from 13:47:33 to 13:53:26, 5 minutes 53 seconds, and used 3.5 AI credits. Its pull request, [#29](https://github.com/melabadi/ai-sdlc-landing-zone/pull/29), adds one file, ADR 0001, which compares the options against the standards. *ADR checks* and *API contract compatibility* passed.

![The ADR checks run on pull request #29: ADR checks and API contract compatibility passed](images/02-design-3-adr-checks.png)

Copilot code review, requested at 13:53:56, recommended changes at 13:59:39, with three findings. In the enterprise profile, the sequence diagram sent the policy tool's output straight to Foundry, past API Management. A field allowlist didn't keep personal data out of the free-text title and description. And a task deleted the small-team profile's AI audit entries after 90 days, a limit the standard sets only for recommendations.

![Copilot code review on the ADR: "Changes recommended", with its findings, starting with enterprise policy-tool traffic bypassing APIM](images/02-design-4-code-review.png)

**The owner's first decision, at 14:00:31:** send the findings back to Copilot. The session posted them with `@copilot`. Copilot's revision session used 2 AI credits. It pushed [`fcb8601`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/29/commits/fcb8601), said in one comment how it addressed each finding, and ended at 14:04:43.

![Copilot's comment on the revision: each finding, and how fcb8601 addresses it, starting with the enterprise sequence, which now routes both model exchanges through APIM](images/02-design-5-revision.png)

The re-review, at 14:14:34, found no open issues, and raised one point the first review had missed: the ADR left earlier tool-calling responses untracked, so it must require failure-resilient per-call correlation.

![Copilot's re-review: "Needs a closer look", because the ADR leaves earlier tool-calling responses untracked and must require failure-resilient per-call correlation](images/02-design-6-re-review.png)

**The owner's second decision, at 14:20:30:** accept the ADR, with per-call correlation added as its open question 10, and the owner named as the decider. The session pushed [`fe8c098`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/29/commits/fe8c098) with the status Accepted, and the checker passed. The ADR merged at 14:27:36 as [`b24d777`](https://github.com/melabadi/ai-sdlc-landing-zone/commit/b24d777), and #28 closed.

![The accepted ADR, docs/architecture/adr/0001-live-ai-triage-provider.md, on main after commit b24d777](images/02-design-7-accepted.png)

**What to observe:** the standards arrived in 4 minutes, before anyone wrote the ADR. Two reviews found four gaps in it, and each was fixed or recorded as an open question before a person accepted it by name: 33 minutes from the question to the decision. Read it: [`0001-live-ai-triage-provider.md`](../architecture/adr/0001-live-ai-triage-provider.md).

### 3. Develop: the feature, and a reviewer's test that caught a defect

At 13:46:58 the session filed Issue [#26](https://github.com/melabadi/ai-sdlc-landing-zone/issues/26) in the *Develop: bounded feature for Copilot* form's format, from the accelerator's [`feature-issue.md`](https://github.com/melabadi/adept-assessment-northstars/blob/main/solutions/03-develop-github/feature-issue.md): a reviewer confirms the recommended routing department. It names backlog task #21, and the session assigned it to Copilot with `develop-github`.

![Issue #26, "Develop: reviewer confirms the recommended routing department", naming backlog item #21 and tracing to transcript decisions and a governance policy](images/03-develop-1-issue.png)

Copilot's session ended at 14:14:00, after about 27 minutes on GPT-6 Luna, and used 21.9 AI credits. After its plan, it pushed five commits to [#27](https://github.com/melabadi/ai-sdlc-landing-zone/pull/27): the feature, then a failing test for a problem it found itself, a race between a confirmation and a change to the request, and its fix, then a failing test for tool-call audits being lost on stale results, and its fix. The session started the runs of the head commit, and every check passed, *Feature stays within its bounds* among them.

![Copilot's session summary for the feature: the tests by acceptance criterion, starting with roles and access](images/03-develop-2-session.png)

![The commits of pull request #27: the plan, the feature, a failing regression test for the confirmation race, its fix, a failing regression for audit preservation, and its fix](images/03-develop-3-commits.png)

![The feature bounds check on pull request #27: Feature stays within its bounds passed](images/03-develop-4-bounds.png)

The 03 README has the reviewer add their own test. The session, as the reviewer, wrote a browser test from acceptance criteria 1, 2, 3, 4, and 7, [`confirm-routing.spec.ts`](../../app/web/e2e/confirm-routing.spec.ts), and pushed it at 14:24:31 as [`7030a99`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/27/commits/7030a99). CI's *Browser tests* failed at 14:27:50, at line 37. After Ben confirmed a recommendation that moved a misrouted request to IT, the panel showed **Confirmed by Ben Okafor** and also **Stale: request was rerouted since this suggestion**, though that reroute was the confirmation itself. The 8 other browser tests passed.

![The CI run on commit 7030a99: Browser tests failed, while API and worker tests and Web UI checks passed](images/03-develop-5-reviewer-test-failed.png)

![The failing browser test's output: 1 failed and 8 passed, with the failure at line 37 of the reviewer's test](images/03-develop-5b-reviewer-test-output.png)

At 14:28:27 the session handed the finding back with `@copilot`: fix the code, never the test.

![The comment to @copilot: the reviewer's browser test fails at line 37 because the triage panel shows both "Confirmed by Ben Okafor" and "Stale: request was rerouted since this suggestion"; fix the code, never the test](images/03-develop-6-finding.png)

Copilot's fix session took 4 minutes 26 seconds and used 3.3 AI credits. Its commit, [`5bf93b8`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/27/commits/5bf93b8), hides the stale notice once the routing is confirmed: 4 lines in `TriagePanel.tsx`, and its unit test. It left the reviewer's test untouched. CI passed at 14:37, with 9 of 9 browser tests.

![The CI run on the fix: API and worker tests, Web UI checks, and Browser tests passed](images/03-develop-7-fixed.png)

**The owner's decision, at 16:22:26:** approve and merge. The feature merged a second later as [`0a7f181`](https://github.com/melabadi/ai-sdlc-landing-zone/commit/0a7f181), and #26 closed.

![The owner's decision on pull request #27: approved and merged into main, with what was checked](images/03-develop-8-decision.png)

**What to observe:** Copilot's own tests caught two problems in its first draft, and the reviewer's test, written from the criteria, caught a third that they missed. Copilot fixed it in under 5 minutes without touching the test. The decision then waited 1 hour 45 minutes for the owner.

### 4. Test: a defect fixed test-first, and a red CI run explained

The Test accelerator works on a lab: a branch with a planted defect, which never merges. At 13:38:00 the session pushed `lab/test-duplicate-decision`: `main`, plus the accelerator's lab patch, which lets a request be decided more than once, and the defect's scenario. At 13:38:29 it filed Issue [#15](https://github.com/melabadi/ai-sdlc-landing-zone/issues/15) in the *Test: defect to fix test-first with Copilot* form's format, and assigned it to Copilot with `test-github`, with the lab branch as the base.

![Issue #15, "Test: a request can be decided more than once", describing the observed behavior on the lab branch](images/04-test-1-issue.png)

Copilot's session ended at 13:48:30, on GPT-6 Luna, using 5 AI credits. It reproduced the defect with the scenario, and then pushed two commits to [#16](https://github.com/melabadi/ai-sdlc-landing-zone/pull/16): the failing tests on their own, [`20d3b2f`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/16/commits/20d3b2f), then the fix, [`8df47e9`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/16/commits/8df47e9). After the fix, the scenario reported "Not reproduced".

![Copilot's session for the defect, analyzing the request decision behavior](images/04-test-2-session.png)

![The commits of pull request #16: the plan, "Add failing regression tests for #15", then the fix](images/04-test-3-commits.png)

The proof ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44095944784)) ran the tests at each commit: all 4 new tests fail at the tests-only commit and pass with the fix. Copilot code review, at 13:52:18, recommended approval, with no open issues.

![The test-first proof on pull request #16: regression tests fail before the fix and pass after it](images/04-test-4-proof.png)

At 13:54:22 the session posted the review evidence, which keeps the deterministic acceptance apart from the review comments.

![The review evidence for #16: a table of deterministic acceptance checks, all passing, before the review comments](images/04-test-5-evidence.png)

**The owner's decision, at 13:55:05:** approve the fix. It stays on its pull request into the lab branch, unmerged, as the lab requires.

![The owner's decision on pull request #16: approved, with the proof, CI, the bounds check, and Copilot code review checked; the fix stays unmerged on the lab](images/04-test-6-decision.png)

The accelerator's second half explains a red CI run. At 13:49:34 the session opened [#30](https://github.com/melabadi/ai-sdlc-landing-zone/pull/30) with the regression tests and no fix. CI failed, and at 13:54:30 the agentic CI failure investigation ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44096808233), about 14 AI credits plus 1) labeled it `ci:defect-reproduced`, with the failing tests and the next step: the tests reproduce a defect, and the run isn't flaky.

![Pull request #30, "Decide a request only once: regression tests first", labeled ci:defect-reproduced, with the CI failure investigation's comment](images/04-test-7-ci-investigation.png)

**What to observe:** the tests existed, and failed, before the fix, and a reviewer sees that commit by commit and in the proof's table. A red CI run was explained 5 minutes after the pull request opened, without anyone reading the logs.

### 5. Secure: an injection found twice, and a repair proven by a replay

The Secure lab is a pull request that never merges. At 13:38:55 the session opened [#17](https://github.com/melabadi/ai-sdlc-landing-zone/pull/17), whose one commit replaces RequestHub's safe search with SQL built by string concatenation, into a lab base branch, and requested Copilot code review. CodeQL flagged it at 13:40:52: a SQL query built from user-controlled sources. Copilot code review flagged it at 13:43:07, and added a second comment about keeping the literal `LIKE` semantics.

![Copilot code review on pull request #17: the search concatenates text without parameterization, so a value with a quote becomes SQL logic rather than search text](images/05-secure-1-finding.png)

![CodeQL's alert on pull request #17: this query depends on a user-provided value](images/05-secure-2-codeql.png)

At 13:46:38 the session filed the finding in the *Secure: remediate* form's format as Issue [#23](https://github.com/melabadi/ai-sdlc-landing-zone/issues/23), and assigned it to Copilot with `secure-github`, on the lab branch.

![Issue #23, "Secure: parameterize the lab search, tests first", describing the unsafe search on the undeployed lab branch](images/05-secure-3-issue.png)

Copilot's session ran for 12 minutes 8 seconds and used 5.4 AI credits. It pushed the supplied regression tests first, [`2298b1e`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/24/commits/2298b1e), then the repair, [`ae5ce36`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/24/commits/ae5ce36), to [#24](https://github.com/melabadi/ai-sdlc-landing-zone/pull/24).

![Copilot's session for the repair: implementing secure parameterization for the lab search, and its tests](images/05-secure-4-session.png)

![The commits of pull request #24, "Parameterize request search and preserve literal LIKE semantics": the plan, the regression tests, then the repair](images/05-secure-5-commits.png)

The acceptance doesn't rely on Copilot's word. The trusted replay runs from `main` ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44098557895)). It checks that Copilot's regression is exactly the reference in [`solutions/05-secure-github/regression/`](../../solutions/05-secure-github/regression/), then runs it on isolated copies of the code before and after the repair. It passed at 14:02:20, in 1 minute 16 seconds: 6 of the 10 cases failed before the repair, and all 10, and the full suite, passed after it. A CodeQL scan of the repair branch that expects the alert to be gone passed at 14:13 ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44100119817)). Copilot code review of the repair found no open issues, and still asked for a closer look: "The required human-run trusted replay and CodeQL rescan of the repaired head remain pending".

![The trusted replay of the remediation, run from main: the deterministic replay summary, with a total duration of 1 minute 16 seconds](images/05-secure-6-replay.png)

**The owner's decision, at 14:23:31:** approve the repair. #17 and #24 closed unmerged, as the lab requires, and #24 stays the reference repair for the nightly replay (`SECURE_REPLAY_PR=24`). #23 closed as completed.

**What to observe:** two independent detectors flagged the injection within 5 minutes of the push. The repair was proven by cases Copilot didn't write, replayed from `main`: 21 minutes from CodeQL's finding to a proven repair.

### 6. Release: a release that waited for its approver

At 16:22:59, once the feature had merged, the session requested candidate 1.0.0 ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44125102015)). It failed at 16:24:03. Pushing `ghcr.io/melabadi/requesthub-worker` was denied (`permission_denied: read_package`): the owner's account already had that package, from the source repository's releases, and it belongs to that repository.

![The first release candidate run: preflight and the tests passed, then the image jobs failed](images/06-release-0-first-candidate-failed.png)

The session fixed it in [#31](https://github.com/melabadi/ai-sdlc-landing-zone/pull/31): release images now go under `ghcr.io/<owner>/<repository>/`, with a unit test that fails on the old path, and a note in the README. It merged at 16:37:43 once the six required checks had passed. The second candidate ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44127979515)) passed at 16:40:32, in 2 minutes 29 seconds: the test gate, the two images, a deployment check on the images by digest, and the draft release with its manifest and checksums.

![The second release candidate run: preflight, API and worker tests, web UI tests, both images, the deployment check on the release images, and the draft release all passed](images/06-release-1-candidate.png)

The agentic release summary started 4 seconds later ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44128460713)), and added its summary to the draft at 16:49:45, using about 14 AI credits plus 1.

![The agentic release summary run: activation, agent, threat detection, and safe outputs jobs](images/06-release-2-summary-run.png)

![The draft release RequestHub demo-v1.0.0: a demo release note, the candidate run, the commit, and the release evidence](images/06-release-3-draft.png)

Then the gate held. An approval started from a branch other than `main`, `demo/not-main`, was refused by the environment in 21 seconds ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44128532557)).

![The approval run from demo/not-main: Verify the evidence passed, then Record the approval and publish failed, in 21 seconds in total](images/06-release-4-refused-branch.png)

**The owner's decision, at 18:11:41:** approve and publish. The session started the approval workflow from `main` ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44145178997)). It verified the evidence again, then waited for the `release-github` environment's required reviewer.

![The approval run from main: Verify the evidence passed, and the run waits for a review to deploy to release-github](images/06-release-5-waiting-for-reviewer.png)

At 18:13:47 the session applied the owner's approval as that reviewer, and `demo-v1.0.0` was published at 18:13:56.

![The approval run after the review: Verify the evidence and Record the approval and publish both passed](images/06-release-6-approved.png)

![The published release RequestHub demo-v1.0.0, on commit 8d5f10f, with its release evidence](images/06-release-7-published.png)

`release_evidence.py verify --expect published` then passed 8 checks, skipped 1, and failed none. The skipped check reads the image digests, which needs a token with access to packages.

![Terminal output of release_evidence.py verify for demo-v1.0.0 with --expect published: 8 passed, 1 skipped, 0 failed](images/06-release-8-verify.png)

**What to observe:** the evidence was checked at the candidate and again at the approval, and the publish waited for a person in the environment's reviewer list. The first failure was a real adoption problem, fixed with a test 14 minutes after it appeared.

### 7. Operate: from an incident to a proven fix in 28 minutes

At 18:14:55 the session filed the accelerator's sample incident, unchanged, in the *Operate: report an incident* form's format: Issue [#32](https://github.com/melabadi/ai-sdlc-landing-zone/issues/32), INC-2041, a synthetic staging incident dated 20 October 2026, in which reviewers got notifications late and repeatedly.

![Incident #32, "INC-2041: reviewers notified late and repeatedly (staging)", with the incident form's fields](images/07-operate-1-incident.png)

The agentic incident triage commented at 18:20:44, 5 minutes 49 seconds later ([run](https://github.com/melabadi/ai-sdlc-landing-zone/actions/runs/44145780113), about 23 AI credits plus 1). It gave severity 3, area worker, status Mitigated. Its UTC timeline names a source on every row. It keeps the observed facts apart from three hypotheses, and rules out the third with a log line. It lists the missing evidence, and added the labels `severity:3` and `area:worker`. Its line citations are close: the `try` that opens the catch is at line 77, as cited, and `SaveChangesAsync` is at line 105, not 100.

![The incident triage: severity 3, area worker, status Mitigated; a timeline with a source for every row; observed facts; three hypotheses with their support and confidence; missing evidence; and the follow-up](images/07-operate-2-triage.png)

It opened one bounded follow-up as a sub-issue, [#33](https://github.com/melabadi/ai-sdlc-landing-zone/issues/33): count a timed-out delivery as a failed attempt instead of stalling the queue. It has six acceptance criteria, and a scope of one test file, plus one production file only if the test fails.

![Follow-up #33, labeled incident-followup, with the incident as its parent: why, the failure mode to reproduce, six acceptance criteria, the scope, and the evidence from the incident](images/07-operate-3-follow-up.png)

**The owner's first decision, at 18:26:08:** send the follow-up to Copilot. The session assigned it with the `operate-github` agent and the base branch `main`, and Copilot opened [#34](https://github.com/melabadi/ai-sdlc-landing-zone/pull/34) 3 seconds later. Its session ran from 18:26:43 to 18:38:46, 12 minutes 3 seconds, on GPT-6 Luna, and used 5.3 AI credits. It pushed four commits: the tests first, [`94f0995`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/34/commits/94f0995), then the one-line fix, [`b9cf04e`](https://github.com/melabadi/ai-sdlc-landing-zone/pull/34/commits/b9cf04e), then two that only clean up the tests' data, with no assertion changed. Its summary includes the proof it ran itself.

![Copilot's session for the follow-up: its summary, a proof table with three tests that fail before the fix and pass with it, 83 tests passed, and GPT-6 Luna with 5.3 AI credits](images/07-operate-4-session.png)

Copilot's push started nothing on its own: the five workflows on its last commit waited for a person.

![Pull request #34 with Copilot's description and commits, and the merge box: 5 workflows awaiting approval, with the Approve workflows to run button](images/07-operate-5-approve-workflows.png)

The session started them at 18:41:42. *Prove the regression test* reported PROVEN at 18:42:57: exactly the three new timeout tests fail on the code before the change and pass with it, with 80 passed and 3 failed before and 83 passed after. The fourth new test, which checks that a shutdown still cancels the work, isn't listed: it guards what the old code already did. Every check had passed by 18:44:01.

![The regression proof: PROVEN, three timeout tests that failed before the change and passed with it, 80 passed and 3 failed before the change, and 83 passed at the head](images/07-operate-6-proof.png)

The production change is one line, in the catch filter:

![Files changed on pull request #34: in NotificationProcessor.cs, the catch filter becomes "ex is not OperationCanceledException || !ct.IsCancellationRequested"; below it, the test file](images/07-operate-7-diff.png)

**The owner's second decision, at 18:57:33:** approve and merge. Marking the pull request ready for review ran the proof again, with the same result. It merged at 18:59:25 as [`2399b96`](https://github.com/melabadi/ai-sdlc-landing-zone/commit/2399b96), and #33 closed. The incident stays open: the triage listed two more follow-ups it didn't create, for a person to decide.

![Pull request #34, merged: the owner's decision comment, the ready-for-review event, and the merge commit 2399b96 with 13 checks passed](images/07-operate-8-decision.png)

**What to observe:** 28 minutes 2 seconds from the incident to a proven regression test, the metric the Operate accelerator tracks. The proof's table, not Copilot's description, says which tests catch the defect. This time they agreed.

## What it cost

| What ran | How many | AI credits | Runner minutes |
| --- | --- | --- | --- |
| Copilot cloud agent sessions, on GPT-6 Luna | 8 | 48.3 | 77.5 |
| Copilot code reviews, at balanced review effort | 5 | 398.5 | 18.8 |
| Agentic workflows, on auto (Claude Sonnet 5.5) | 4 | about 73, plus about 4 for threat detection | 23.7 |
| CI, CodeQL, and the accelerators' deterministic checks | | none | 92.7 |
| **Total** | | **about 524** | **212.7** |

<details>
<summary>Each session, review, and agentic workflow</summary>

| Copilot cloud agent session | AI credits |
| --- | --- |
| Plan: the brief, #14 | 1.9 |
| Test: the tests, then the fix, #16 | 5 |
| Secure: the regression, then the repair, #24 | 5.4 |
| Design: the ADR, #29 | 3.5 |
| Design: the revision after code review, #29 | 2 |
| Develop: the feature, #27 | 21.9 |
| Develop: the fix for the reviewer's test, #27 | 3.3 |
| Operate: the regression test and the fix, #34 | 5.3 |

| Copilot code review | AI credits |
| --- | --- |
| The Secure lab's unsafe search, #17 | 89.8 |
| The Test fix, #16 | 58.5 |
| The Secure repair, #24 | 32.3 |
| ADR 0001, first review, #29 | 133.2 |
| ADR 0001, re-review, #29 | 84.7 |

| Agentic workflow | AI credits, agent plus threat detection |
| --- | --- |
| Design review, #28 | about 22 + 1 |
| CI failure investigation, #30 | about 14 + 1 |
| Release summary, `demo-v1.0.0` | about 14 + 1 |
| Incident triage, #32 | about 23 + 1 |

</details>

Each Copilot session page and each review's session page reports its AI credits; the agentic workflows' footers report theirs, rounded. The runner minutes add up the jobs of the 202 workflow runs started during the run, measured from the Actions API. They are free on a public repository. In a private one, each job is rounded up to a whole minute, so they would count as 356 minutes of your plan's included usage.

## Where the time went

| Phase | Started | Last decision | Elapsed | Copilot's sessions |
| --- | --- | --- | --- | --- |
| 1. Plan | 13:37:19 | 13:44:30 | 7 min 11 s | 4 min 28 s |
| 2. Design | 13:47:18 | 14:20:30 | 33 min 12 s | 5 min 53 s, then a revision of about 4 min |
| 3. Develop | 13:46:58 | 16:22:26 | 2 h 35 min, 1 h 45 min of it waiting for the decision | about 27 min, then 4 min 26 s for the fix |
| 4. Test | 13:38:00 | 13:55:05 | 17 min 5 s | about 10 min |
| 5. Secure | 13:38:55 | 14:23:31 | 44 min 36 s | 12 min 8 s |
| 6. Release | 16:22:59 | 18:11:41 | 1 h 49 min, 1 h 22 min of it waiting for the decision | none; the agentic summary took 9 min |
| 7. Operate | 18:14:55 | 18:57:33 | 42 min 38 s | 12 min 3 s |

The two long waits were the owner's availability, not the tooling, and both were on the critical path: Release started from `main` 32 seconds after the feature merged, and Operate a minute after the release was published. Every other wait for a person, such as starting the workflows of Copilot's commits, took minutes.

## What the run found

1. **Copilot's pull requests carry the name of whoever assigns Copilot.** Copilot cloud agent opened every pull request and pushed every commit in the owner's account, with Copilot as co-author: "Copilot started work on behalf of melabadi". GitHub doesn't let authors approve their own pull requests, so the owner recorded each decision as a comment review that starts "Decision:". The Test accelerator's review evidence counts only approvals and requested changes, so it shows the decision as pending. In a team, the reviewer who decides should be someone other than the person who assigned Copilot.
2. **A reviewer's own test is still worth writing.** In Develop, a browser test written from the acceptance criteria found a defect that Copilot's tests, its own race and audit regressions included, had missed. Copilot fixed the code and left the test alone.
3. **Copilot code review was most of the AI cost, and earned it.** Five reviews used 398.5 of about 524 AI credits; the ADR's first review alone used 133.2. They found the injection, three policy gaps in the ADR, and a fourth gap on re-review. On the repair, the review found no issues and still deferred to the trusted replay and the CodeQL rescan rather than to Copilot's own tests. Request reviews where their findings can change a decision.
4. **Start only the head commit's waiting runs.** On #24, starting every waiting run of the branch started older commits' runs last, and their concurrency group cancelled the head commit's runs, so the session ran those again. The Operate README's command starts only the head commit's runs, which avoids it.
5. **Release images can collide with another repository's packages.** The Release accelerator pushed its images as `ghcr.io/<owner>/requesthub-*`, and the owner's account already had a `requesthub-worker` package, which belongs to the source repository. [#31](https://github.com/melabadi/ai-sdlc-landing-zone/pull/31) puts them under the repository's own path. Any repository whose owner already has `requesthub-*` packages elsewhere would hit it.
6. **One web test is flaky.** On `fe8c098`, a commit that changed only the ADR, *Web UI checks* failed although every test passed: Vitest reported an unhandled `ReferenceError: window is not defined` during the teardown of `DecisionPanel.test.tsx`. Running the job again passed.
7. **Check the triage's citations.** One of its line numbers was 5 lines off. Its timeline, facts, and hypotheses held, and the proof confirmed the first hypothesis.

## Run it again

The run changed this repository. `main` now has the brief, ADR 0001, the routing confirmation, the release image path, and the timeout fix. Before you repeat a phase:

- **Plan, Design, and Develop:** to start again from the same notes, question, or feature, give Copilot a base branch made from `a60b162`, `main` before the run.
- **Test and Secure:** their labs start from `main` as their READMEs describe. Close this run's Test lab, Issue #15 and pull requests #16 and #30, as the Test README's reset does.
- **Release:** request a new version, such as `1.0.1`: `demo-v1.0.0` is published.
- **Operate:** the timeout defect is fixed on `main`, so a follow-up from the sample incident would now get COVERAGE, not PROVEN. To see PROVEN, revert `2399b96` on a branch, and give that branch to Copilot as the base.

The backlog, #18 to #22, and the incident, #32, stay open on purpose: the backlog is the team's, and the incident's two remaining follow-ups are a person's call.
