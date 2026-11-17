# Requirements brief: assisted request triage

> Scenario `assisted-triage-brief` · produced by **GitHub Copilot (plan-github agent)** · every line cites the transcript paragraph (Tnn) or policy it comes from.
> Review this brief before publishing issues: it is a draft, not a decision record.

## Problem

Requests can reach the wrong department and sit there before anyone notices; reviewers report frequent manual rerouting, but its rate has not been measured. _(T01, T02)_

## Goals

- Reduce the time requests wait before reaching the right team. _(T01)_
- Give reviewers advisory department and priority suggestions with an explanation of the routing policies used. _(T03, T08)_

## Requirements

| ID | Priority | Requirement | Sources |
| --- | --- | --- | --- |
| R1 | must | For each new request, provide a suggested department and priority. | T03 |
| R2 | must | Show a short rationale and the IDs and versions of the routing policies used for each suggestion. | T08 |
| R3 | must | Send the AI service only the request title, description, category, approved routing policies, and requester department; do not send attachments or other personal data. | T09 |
| R4 | must | Support English and French requests. | T11 |
| R5 | must | When a request is rerouted after a suggestion, show that the suggestion is stale. | T10 |
| R6 | must | Audit each recommendation and each assistant lookup, including who asked, when, and what was returned. | T13 |
| R7 | must | If the AI service is unavailable, clearly show that it is unavailable and let reviewers continue routing manually. | T14 |
| R8 | should | A confidence score may be shown, but confidence must not be used to sort or filter suggestions in this release. | T15 |
| R9 | must | A double click on routing confirmation must not create duplicate audit entries or notifications. | T16 |
| R10 | must | Safety hazards route to Facilities with Urgent priority regardless of the request category. | T17, POL-ROUTE-006 |
| R11 | must | Recommendations remain advisory and require reviewer confirmation for routing; only an authorized approver may approve or reject a request. | T04, T19, POL-GOV-001 |

## Decisions

- **D1** For the first release, triage recommendations are advisory and routing requires reviewer confirmation; only an authorized approver may approve or reject. _(T04, T19, POL-GOV-001)_

## Conflicts

- **C1** The request for automatic routing without review conflicts with the requirement that routing recommendations remain advisory and reviewer-confirmed. _(T04, T05, POL-GOV-001)_ → resolved: The first release provides recommendations plus reviewer confirmation; automatic routing is deferred for reconsideration after data is available. (T19)
- **C2** The spend-threshold policy says requests above 5,000 route to Finance, while the statement about computing equipment says IT owns it regardless of cost; no precedence is specified for expensive computing equipment. _(T06, T07, POL-ROUTE-001, POL-ROUTE-004)_ → **unresolved — needs a decision**

## Open questions

- **Q1** What response-time target defines "fast" for the assistant? _(T12)_
- **Q2** What confidence threshold, if any, should determine whether a suggestion is hidden or shown? No threshold or hide behavior has been agreed. _(T15)_
- **Q3** (blocking) Who may override a suggestion: reviewers only, or approvers as well? _(T21)_
- **Q4** (blocking) How long should recommendations and related suggestion data be retained? _(T22)_

## Out of scope

- Automatic routing without reviewer confirmation in this release. _(T19)_
- Automatic approval of any kind and email notifications to requesters. _(T20)_

## Success measures

- Measure the share of requests rerouted after triage, collecting a two-week baseline before enabling the assistant. _(T23)_

## Engineering backlog: Assisted request triage

Provide policy-grounded, advisory routing suggestions that reviewers can understand and confirm, while preserving manual routing, approval authority, privacy, and an auditable workflow. _(T03, T08, T10, T13, T14, T16, T19, POL-GOV-001)_

### TASK-1 · Generate policy-grounded recommendations safely

Generate advisory department and priority suggestions with rationale and policy ID/version references, while enforcing the approved input-data boundary and supported routing rules. Do not encode precedence between POL-ROUTE-001 and POL-ROUTE-004 for expensive computing equipment until a human decision is recorded. _(T03, T08, T09, T11, T17, T06, T07, POL-ROUTE-006, POL-ROUTE-007, POL-ROUTE-001, POL-ROUTE-004)_

- **Owner role:** Backend engineer
- **Depends on:** none
- **Acceptance criteria:**
  - [ ] Given a new request and the approved routing policies, When a recommendation is generated, Then it includes a suggested department, priority, short rationale, and the IDs and versions of the policies it used.
  - [ ] Given a recommendation is requested, When request data is sent to the AI service, Then only the title, description, category, approved routing policies, and requester department are sent, with no attachments or other personal data.
  - [ ] Given a request reports a safety hazard, When its recommendation is generated, Then it suggests Facilities and Urgent priority regardless of category.
  - [ ] Given a request lacks information needed to identify its owning department, When a recommendation is generated, Then it keeps the current department, flags the request for human review, and asks one clarifying question.
  - [ ] Given a request is submitted in English or French, When a recommendation is generated, Then the assistant supports that language.

### TASK-2 · Present recommendations and manual fallback

Show reviewers the recommendation details and state in the request workflow, including stale recommendations, confidence without confidence-based sorting or filtering, and clear manual-routing behavior when the assistant is unavailable. _(T08, T10, T11, T12, T14, T15)_

- **Owner role:** Frontend engineer
- **Depends on:** TASK-1
- **Acceptance criteria:**
  - [ ] Given a request has a recommendation, When a reviewer views it, Then the suggested department, priority, rationale, policy IDs and versions are visible, and any confidence score is not used to sort or filter suggestions.
  - [ ] Given a request has been rerouted after a recommendation, When a reviewer views the recommendation, Then the interface identifies it as stale.
  - [ ] Given the AI service is unavailable, When a reviewer attempts triage, Then the interface clearly reports unavailability and allows the reviewer to route the request manually.
  - [ ] Given a reviewer uses the interface in English or French, When recommendation details are displayed, Then the workflow supports that language.

### TASK-3 · Confirm routing once with reviewer authority

Connect reviewer confirmation to the request-routing workflow without allowing the recommendation to make a decision, and make repeated confirmation safe against duplicate audit entries and notifications. _(T04, T16, T19, POL-GOV-001)_

- **Owner role:** Full-stack engineer
- **Depends on:** TASK-1, TASK-2
- **Acceptance criteria:**
  - [ ] Given an advisory routing suggestion is displayed, When a reviewer confirms it, Then the request is routed only after that reviewer action and the suggestion does not approve or reject the request.
  - [ ] Given a user is not authorized to confirm routing, When they attempt to confirm a suggestion, Then the routing is not changed.
  - [ ] Given a reviewer double-clicks confirmation, When the action is processed, Then it creates no more than one audit entry and no more than one notification.
  - [ ] Given a request is awaiting an approval decision, When a recommendation or routing confirmation is processed, Then only an authorized approver can approve or reject it.

### TASK-4 · Audit assistant activity and establish the baseline

Record recommendation and assistant lookup activity with the requested actor, time, and returned information, and capture the specified pre-launch rerouting baseline and ongoing share-of-rerouted measure without assuming a retention period. _(T13, T22, T23)_

- **Owner role:** Backend engineer
- **Depends on:** TASK-1, TASK-3
- **Acceptance criteria:**
  - [ ] Given the assistant generates a recommendation or performs a lookup, When the activity completes, Then an audit record captures who asked, when, and what was returned.
  - [ ] Given the assistant has not yet been enabled, When the team establishes the success-measure baseline, Then it measures the share of requests rerouted after triage for two weeks before enablement.
  - [ ] Given routing outcomes are available after enablement, When the success measure is reported, Then it reports the share of requests rerouted after triage.

