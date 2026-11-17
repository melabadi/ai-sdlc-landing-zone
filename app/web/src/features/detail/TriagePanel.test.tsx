import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { callsTo, detail, mockApi, noPermissions, problem, recommendation, renderApp } from '../../test/utils';

describe('TriagePanel', () => {
  it('labels sample-rule recommendations as not AI and shows policy citations with their text', async () => {
    mockApi({
      'GET /api/requests/REQ-1003': () =>
        detail({
          id: 'REQ-1003',
          title: 'Badge access to Building C lab',
          departmentId: 'FAC',
          latestRecommendation: recommendation(),
          permissions: { ...noPermissions, canTriage: true },
        }),
      'GET /api/requests/REQ-1003/history': () => [],
    });
    const user = userEvent.setup();

    renderApp('/requests/REQ-1003', { persona: 'u-ben' });

    const panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(within(panel).getByText('Sample rules — not AI')).toBeInTheDocument();
    expect(within(panel).queryByText(/AI recommendation/)).not.toBeInTheDocument();

    const citations = within(panel).getByRole('list', { name: 'Policy citations' });
    const chip = within(citations).getByText('POL-ROUTE-003 v2.1');
    expect(chip).toHaveAttribute('title', expect.stringContaining('Workplace and building services'));

    await user.click(within(panel).getByText('Read the cited policies'));
    expect(within(panel).getByText(/building access badges route to Facilities/)).toBeVisible();

    expect(within(panel).getByText('60%')).toBeInTheDocument();
    expect(within(panel).getByText('Recommendations are advisory. Only an approver can approve or reject.')).toBeInTheDocument();
    expect(within(panel).getByRole('button', { name: 'Get recommendation' })).toBeInTheDocument();
    // Applying a recommendation is intentionally not part of the UI.
    expect(within(panel).getAllByRole('button')).toHaveLength(1);
  });

  it('labels AI recommendations with the provider and trace id, and flags stale or uncertain suggestions', async () => {
    mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          departmentId: 'FAC',
          latestRecommendation: recommendation({
            provider: 'foundry-agent',
            isSample: false,
            providerTraceId: 'resp_abc123',
            suggestedDepartmentId: 'IT',
            departmentAtRecommendation: 'IT',
            needsHumanReview: true,
            policyRefs: [{ policyId: 'POL-ROUTE-001', version: '1.2' }],
          }),
        }),
      'GET /api/requests/REQ-1001/history': () => [],
    });

    renderApp('/requests/REQ-1001', { persona: 'u-ava' });

    const panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(within(panel).getByText('AI recommendation · foundry-agent')).toBeInTheDocument();
    expect(within(panel).getByText('Provider trace: resp_abc123')).toBeInTheDocument();
    expect(within(panel).queryByText('Sample rules — not AI')).not.toBeInTheDocument();
    expect(within(panel).getByText('Stale: request was rerouted since this suggestion')).toBeInTheDocument();
    expect(within(panel).getByText('Needs human review')).toBeInTheDocument();
    expect(
      within(panel).getByText('The assistant flagged this recommendation for a person. A reviewer should confirm the routing.'),
    ).toBeInTheDocument();
    expect(within(panel).queryByRole('button')).not.toBeInTheDocument();
  });

  it('shows a translated, accessible error when the triage provider is unavailable', async () => {
    mockApi({
      'GET /api/requests/REQ-1001': () => detail({ permissions: { ...noPermissions, canTriage: true } }),
      'GET /api/requests/REQ-1001/history': () => [],
      'POST /api/requests/REQ-1001/triage-recommendations': () =>
        problem(503, 'triage.unavailable', 'The triage assistant is unavailable. Route the request manually.'),
    });
    const user = userEvent.setup();

    renderApp('/requests/REQ-1001', { persona: 'u-ben' });

    const panel = await screen.findByRole('region', { name: 'Triage assistant' });
    await user.click(within(panel).getByRole('button', { name: 'Get recommendation' }));

    const alert = await within(panel).findByRole('alert');
    expect(alert).toHaveTextContent("We couldn't get a recommendation.");
    expect(alert).toHaveTextContent('The triage assistant is unavailable right now. Route the request manually.');
    expect(alert).toHaveTextContent('Details: The triage assistant is unavailable. Route the request manually.');
    expect(within(panel).getByRole('button', { name: 'Get recommendation' })).toBeEnabled();
  });

  it('lets a permitted reviewer confirm only a fresh proposed recommendation', async () => {
    mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          latestRecommendation: recommendation({ departmentAtRecommendation: 'IT' }),
          permissions: { ...noPermissions, canConfirmRecommendation: true },
        }),
      'GET /api/requests/REQ-1001/history': () => [],
    });

    renderApp('/requests/REQ-1001', { persona: 'u-ben' });

    const panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(await within(panel).findByRole('button', { name: 'Confirm routing' })).toBeInTheDocument();
  });

  it('hides confirmation for requesters, stale recommendations, and already confirmed recommendations', async () => {
    mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          latestRecommendation: recommendation({
            status: 'Proposed',
            departmentAtRecommendation: 'FAC',
          }),
          departmentId: 'IT',
          permissions: { ...noPermissions, canConfirmRecommendation: true },
        }),
      'GET /api/requests/REQ-1001/history': () => [],
    });
    const { unmount } = renderApp('/requests/REQ-1001', { persona: 'u-ben' });
    let panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(within(panel).queryByRole('button', { name: 'Confirm routing' })).not.toBeInTheDocument();
    unmount();

    mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          latestRecommendation: recommendation({ departmentAtRecommendation: 'IT' }),
          permissions: { ...noPermissions, canConfirmRecommendation: true },
        }),
      'GET /api/requests/REQ-1001/history': () => [],
    });
    const requesterView = renderApp('/requests/REQ-1001', { persona: 'u-ava' });
    panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(within(panel).queryByRole('button', { name: 'Confirm routing' })).not.toBeInTheDocument();
    requesterView.unmount();

    mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          latestRecommendation: recommendation({
            status: 'Confirmed',
            departmentAtRecommendation: 'IT',
            confirmedBy: { id: 'u-ben', displayName: 'Ben Okafor' },
          }),
          permissions: { ...noPermissions, canConfirmRecommendation: false },
        }),
      'GET /api/requests/REQ-1001/history': () => [],
    });

    renderApp('/requests/REQ-1001', { persona: 'u-ava' });
    panel = await screen.findByRole('region', { name: 'Triage assistant' });
    expect(within(panel).queryByRole('button', { name: 'Confirm routing' })).not.toBeInTheDocument();
    expect(within(panel).getByText('Confirmed by Ben Okafor')).toBeInTheDocument();
  });

  it('confirms through the additive endpoint, refreshes detail and history, and localizes the confirmation', async () => {
    let confirmed = false;
    const fetchMock = mockApi({
      'GET /api/requests/REQ-1001': () =>
        detail({
          departmentId: confirmed ? 'FAC' : 'IT',
          status: confirmed ? 'InReview' : 'Submitted',
          latestRecommendation: recommendation({
            status: confirmed ? 'Confirmed' : 'Proposed',
            departmentAtRecommendation: 'IT',
            confirmedBy: confirmed ? { id: 'u-ben', displayName: 'Ben Okafor' } : null,
          }),
          permissions: { ...noPermissions, canConfirmRecommendation: !confirmed },
        }),
      'GET /api/requests/REQ-1001/history': () =>
        confirmed
          ? [
              {
                id: 501,
                action: 'triage.confirmed',
                actor: { id: 'u-ben', displayName: 'Ben Okafor' },
                occurredAt: '2026-10-26T06:25:00Z',
                details: { recommendationId: '7d2c1f00-0000-4000-8000-000000000001', from: 'IT', to: 'FAC' },
                correlationId: null,
              },
            ]
          : [],
      'POST /api/requests/REQ-1001/triage-recommendations/7d2c1f00-0000-4000-8000-000000000001/confirm': () => {
        confirmed = true;
        return detail({
          departmentId: 'FAC',
          status: 'InReview',
          latestRecommendation: recommendation({
            status: 'Confirmed',
            departmentAtRecommendation: 'IT',
            confirmedBy: { id: 'u-ben', displayName: 'Ben Okafor' },
          }),
        });
      },
    });
    const user = userEvent.setup();

    const frenchView = renderApp('/requests/REQ-1001', { persona: 'u-ben', locale: 'fr' });

    const panel = await screen.findByRole('region', { name: 'Assistant de triage' });
    await user.click(await within(panel).findByRole('button', { name: "Confirmer l'acheminement" }));

    expect(await within(panel).findByText('Confirmée par Ben Okafor')).toBeInTheDocument();
    expect(await screen.findByText('Acheminement confirmé : Installations')).toBeInTheDocument();
    expect(callsTo(fetchMock, 'POST', '/api/requests/REQ-1001/triage-recommendations/7d2c1f00-0000-4000-8000-000000000001/confirm')).toHaveLength(1);
    expect(callsTo(fetchMock, 'GET', '/api/requests/REQ-1001')).toHaveLength(2);
    expect(callsTo(fetchMock, 'GET', '/api/requests/REQ-1001/history')).toHaveLength(2);
    expect(within(panel).queryByRole('button', { name: "Confirmer l'acheminement" })).not.toBeInTheDocument();
    frenchView.unmount();

    renderApp('/requests/REQ-1001', { persona: 'u-ben', locale: 'en' });
    expect(await screen.findByText('Routing confirmed: Facilities')).toBeInTheDocument();
    expect(await screen.findByText('Confirmed by Ben Okafor')).toBeInTheDocument();
  });
});
