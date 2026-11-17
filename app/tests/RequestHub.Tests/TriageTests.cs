using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using RequestHub.Core.Data;
using RequestHub.Core.Domain;
using RequestHub.Core.Services;
using RequestHub.Core.Triage;

namespace RequestHub.Tests;

public sealed class TriageTests(ApiFixture api) : IClassFixture<ApiFixture>
{
    [Fact]
    public async Task Sample_recommendation_is_labelled_cites_a_policy_and_changes_nothing()
    {
        await ResetDemoAsync();
        var before = await (await api.As("u-ben").GetAsync("/api/requests/REQ-1001")).Read<RequestDetailDto>();
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1001/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var rec = await response.Read<RecommendationDto>();
        Assert.True(rec.IsSample);
        Assert.Equal("sample-rules", rec.Provider);
        Assert.Equal("IT", rec.SuggestedDepartmentId);
        Assert.Contains(rec.PolicyRefs, p => p.PolicyId == "POL-ROUTE-001" && p.Version == "1.2");

        var after = await (await api.As("u-ben").GetAsync("/api/requests/REQ-1001")).Read<RequestDetailDto>();
        Assert.Equal(before.Status, after.Status);
        Assert.Equal(before.DepartmentId, after.DepartmentId);
        Assert.Null(after.Decision);
    }

    [Fact]
    public async Task Conflicting_policies_are_flagged_for_human_review()
    {
        await ResetDemoAsync();
        var rec = await (await api.As("u-ben").PostAsync("/api/requests/REQ-1012/triage-recommendations", null)).Read<RecommendationDto>();
        Assert.True(rec.NeedsHumanReview);
        Assert.Contains(rec.PolicyRefs, p => p.PolicyId == "POL-ROUTE-004");
    }

    [Fact]
    public async Task Requesters_cannot_request_triage()
    {
        await ResetDemoAsync();
        var response = await api.As("u-ava").PostAsync("/api/requests/REQ-1001/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    [Fact]
    public async Task Policies_endpoint_lists_versioned_policies()
    {
        await ResetDemoAsync();
        var policies = await (await api.As("u-ben").GetAsync("/api/policies")).Read<List<PolicyDto>>();
        Assert.Contains(policies, p => p.Id == "POL-GOV-001");
        Assert.All(policies, p => Assert.False(string.IsNullOrWhiteSpace(p.Version)));
    }

    [Fact]
    public async Task Reviewer_confirms_a_different_department_and_preserves_request_priority_and_decision()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");
        await SetSuggestedDepartmentAsync(recommendation.Id, "FAC");
        var initial = await ReadDetailAsync("REQ-1001");

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var detail = await response.Read<RequestDetailDto>();
        Assert.Equal("FAC", detail.DepartmentId);
        Assert.Equal("InReview", detail.Status);
        Assert.Equal(initial.Priority, detail.Priority);
        Assert.Equal(initial.Decision, detail.Decision);
        Assert.Equal("Confirmed", detail.LatestRecommendation!.Status);
        Assert.Equal("u-ben", await ConfirmedByIdAsync(detail.Id));

        var events = await ReadConfirmationEventsAsync("REQ-1001");
        var audit = Assert.Single(events);
        using var details = JsonDocument.Parse(audit.Details);
        Assert.Equal(recommendation.Id.ToString(), details.RootElement.GetProperty("recommendationId").GetString());
        Assert.Equal("IT", details.RootElement.GetProperty("from").GetString());
        Assert.Equal("FAC", details.RootElement.GetProperty("to").GetString());
        Assert.Equal(recommendation.Provider, details.RootElement.GetProperty("provider").GetString());
        Assert.Contains(details.RootElement.GetProperty("policyRefs").EnumerateArray(),
            item => item.GetString() == "POL-ROUTE-001@1.2");
        Assert.True(await CountRoutedNotificationsAsync("REQ-1001") > 0);
    }

    [Fact]
    public async Task Reviewer_confirms_same_department_without_rerouting()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1005");
        var before = await ReadDetailAsync("REQ-1005");

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1005", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var detail = await response.Read<RequestDetailDto>();
        Assert.Equal(before.DepartmentId, detail.DepartmentId);
        Assert.Equal(before.Status, detail.Status);
        Assert.Equal(before.Priority, detail.Priority);
        Assert.Equal("Confirmed", detail.LatestRecommendation!.Status);
        Assert.Equal("u-ben", await ConfirmedByIdAsync(detail.Id));
        Assert.Single(await ReadConfirmationEventsAsync("REQ-1005"));
        Assert.Equal(0, await CountRoutedNotificationsAsync("REQ-1005"));
    }

    [Fact]
    public async Task Requester_cannot_confirm_a_recommendation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");

        var response = await api.As("u-ava").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Approver_without_reviewer_role_cannot_confirm_a_recommendation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");

        var response = await api.As("u-chloe").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Reviewer_without_access_to_current_department_cannot_confirm_a_recommendation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");

        var response = await api.As("u-grace").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Reviewer_without_access_to_suggested_department_cannot_confirm_a_recommendation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");
        await SetSuggestedDepartmentAsync(recommendation.Id, "HR");

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Superseded_recommendation_cannot_be_confirmed()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");
        await CreateRecommendationAsync("REQ-1001");

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
        Assert.Equal("recommendation.stale", await response.Code());
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Recommendation_cannot_be_confirmed_after_request_department_changes()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1001");
        var reroute = await api.As("u-ben").PutAsJsonAsync("/api/requests/REQ-1001/routing", new { departmentId = "FAC", reason = "Manual reroute." });
        Assert.Equal(HttpStatusCode.OK, reroute.StatusCode);

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1001", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
        Assert.Equal("recommendation.stale", await response.Code());
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1001"));
    }

    [Fact]
    public async Task Repeated_confirmation_returns_already_confirmed_without_a_second_audit()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1005");
        var first = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1005", recommendation.Id), null);
        Assert.Equal(HttpStatusCode.OK, first.StatusCode);

        var repeated = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1005", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Conflict, repeated.StatusCode);
        Assert.Equal("recommendation.already_confirmed", await repeated.Code());
        Assert.Single(await ReadConfirmationEventsAsync("REQ-1005"));
    }

    [Fact]
    public async Task Admin_can_confirm_a_recommendation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1005");

        var response = await api.As("u-dan").PostAsync(ConfirmPath("REQ-1005", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var detail = await response.Read<RequestDetailDto>();
        Assert.Equal("u-dan", await ConfirmedByIdAsync(detail.Id));
    }

    [Fact]
    public async Task Terminal_request_rejects_recommendation_confirmation()
    {
        await ResetDemoAsync();
        var recommendation = await CreateRecommendationAsync("REQ-1005");
        await SetRequestStatusAsync("REQ-1005", RequestStatus.Approved);

        var response = await api.As("u-ben").PostAsync(ConfirmPath("REQ-1005", recommendation.Id), null);

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
        Assert.Equal("request.terminal", await response.Code());
        Assert.Empty(await ReadConfirmationEventsAsync("REQ-1005"));
    }

    private static string ConfirmPath(string requestId, Guid recommendationId) =>
        $"/api/requests/{requestId}/triage-recommendations/{recommendationId}/confirm";

    private async Task ResetDemoAsync()
    {
        var response = await api.As("u-dan").PostAsync("/api/admin/reset", null);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    private async Task<RecommendationDto> CreateRecommendationAsync(string requestId)
    {
        var response = await api.As("u-ben").PostAsync($"/api/requests/{requestId}/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        return await response.Read<RecommendationDto>();
    }

    private async Task SetSuggestedDepartmentAsync(Guid recommendationId, string departmentId)
    {
        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var recommendation = await db.Recommendations.SingleAsync(r => r.Id == recommendationId);
        recommendation.SuggestedDepartmentId = departmentId;
        await db.SaveChangesAsync();
    }

    private async Task SetRequestStatusAsync(string requestId, RequestStatus status)
    {
        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var number = int.Parse(requestId.AsSpan(4));
        var request = await db.Requests.SingleAsync(r => r.Number == number);
        request.Status = status;
        await db.SaveChangesAsync();
    }

    private async Task<RequestDetailDto> ReadDetailAsync(string requestId) =>
        await (await api.As("u-ben").GetAsync($"/api/requests/{requestId}")).Read<RequestDetailDto>();

    private async Task<string?> ConfirmedByIdAsync(string requestId)
    {
        using var doc = JsonDocument.Parse(await (await api.As("u-ben").GetAsync($"/api/requests/{requestId}")).Content.ReadAsStringAsync());
        return doc.RootElement.GetProperty("latestRecommendation").GetProperty("confirmedBy").GetProperty("id").GetString();
    }

    private async Task<List<AuditEvent>> ReadConfirmationEventsAsync(string requestId)
    {
        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var number = int.Parse(requestId.AsSpan(4));
        var requestIdValue = await db.Requests.Where(r => r.Number == number).Select(r => r.Id).SingleAsync();
        return await db.AuditEvents.Where(e => e.RequestId == requestIdValue && e.Action == "triage.confirmed").ToListAsync();
    }

    private async Task<int> CountRoutedNotificationsAsync(string requestId)
    {
        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var number = int.Parse(requestId.AsSpan(4));
        var requestIdValue = await db.Requests.Where(r => r.Number == number).Select(r => r.Id).SingleAsync();
        return await db.Notifications.CountAsync(n => n.RequestId == requestIdValue && n.Type == "request.routed");
    }
}

public sealed class TriageRecommendationConcurrencyTests(BlockingTriageFixture api) : IClassFixture<BlockingTriageFixture>
{
    [Fact]
    public async Task In_flight_recommendation_cannot_supersede_a_confirmation_that_rerouted_the_request()
    {
        var reset = await api.As("u-dan").PostAsync("/api/admin/reset", null);
        Assert.Equal(HttpStatusCode.OK, reset.StatusCode);

        var recommendationId = Guid.NewGuid();
        await using (var scope = api.Factory.Services.CreateAsyncScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
            var request = await db.Requests.SingleAsync(r => r.Number == 1001);
            db.Recommendations.Add(new TriageRecommendation
            {
                Id = recommendationId,
                RequestId = request.Id,
                Provider = "sample-rules",
                IsSample = true,
                SuggestedDepartmentId = "FAC",
                SuggestedPriority = RequestPriority.Normal,
                Rationale = "Facilities policy applies.",
                PolicyRefs = ["POL-ROUTE-003@2.1"],
                Confidence = 0.9,
                DepartmentAtRecommendation = "IT",
                CreatedById = "u-ben",
                CreatedAt = DateTimeOffset.UtcNow,
            });
            await db.SaveChangesAsync();
        }

        BlockingTriageProvider.Reset();
        var recommendationRequest = api.As("u-ben").PostAsync("/api/requests/REQ-1001/triage-recommendations", null);

        try
        {
            await BlockingTriageProvider.WaitUntilStartedAsync(TimeSpan.FromSeconds(10));
            var confirmation = await api.As("u-ben").PostAsync(
                $"/api/requests/REQ-1001/triage-recommendations/{recommendationId}/confirm", null);
            Assert.Equal(HttpStatusCode.OK, confirmation.StatusCode);
            var confirmedDetail = await confirmation.Read<RequestDetailDto>();
            Assert.Equal("FAC", confirmedDetail.DepartmentId);
            Assert.Equal("Confirmed", confirmedDetail.LatestRecommendation!.Status);

            BlockingTriageProvider.Release(new TriageResult(
                "IT", "Normal", "The original request context suggested IT.", ["POL-ROUTE-001"], 0.8, false));
            var recommendationResponse = await recommendationRequest;
            var responseCode = await recommendationResponse.Code();
            var current = await (await api.As("u-ben").GetAsync("/api/requests/REQ-1001")).Read<RequestDetailDto>();
            await using var verifyScope = api.Factory.Services.CreateAsyncScope();
            var verifyDb = verifyScope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
            var requestId = await verifyDb.Requests.Where(r => r.Number == 1001).Select(r => r.Id).SingleAsync();
            var recommendationCount = await verifyDb.Recommendations.CountAsync(r => r.RequestId == requestId);
            Assert.True(
                recommendationResponse.StatusCode == HttpStatusCode.Conflict
                && responseCode == "recommendation.stale"
                && current.DepartmentId == "FAC"
                && current.LatestRecommendation?.Id == recommendationId
                && current.LatestRecommendation.Status == "Confirmed"
                && current.LatestRecommendation.ConfirmedBy?.Id == "u-ben"
                && recommendationCount == 1,
                $"Expected the blocked recommendation to be refused without overwriting confirmation. Got HTTP {(int)recommendationResponse.StatusCode} ({responseCode}), department {current.DepartmentId}, latest recommendation {current.LatestRecommendation?.Id} ({current.LatestRecommendation?.Status}), count {recommendationCount}.");
        }
        finally
        {
            BlockingTriageProvider.Release(new TriageResult(
                "IT", "Normal", "The original request context suggested IT.", ["POL-ROUTE-001"], 0.8, false));
        }
    }
}

/// <summary>A provider that misbehaves on purpose, to prove the app's guards (not the model) decide what is accepted.</summary>
public sealed class MisbehavingTriageProvider : ITriageProvider
{
    public static string Mode { get; set; } = "approval-claim";

    public string Id => "test-misbehaving";

    public bool IsSample => false;

    public async Task<TriageResult> RecommendAsync(TriageContext context, CancellationToken cancellationToken)
    {
        switch (Mode)
        {
            case "approval-claim":
                return new TriageResult("IT", "Normal", "This request is approved and can proceed.", ["POL-ROUTE-001"], 0.9, false);
            case "unknown-policy":
                return new TriageResult("IT", "Normal", "Routing by an invented rule.", ["POL-MADE-UP-9"], 0.9, false);
            case "conflict-unflagged":
                return new TriageResult("FIN", "Normal", "The spend threshold applies.", ["POL-ROUTE-001", "POL-ROUTE-004"], 0.9, false);
            case "below-threshold-citation":
                return new TriageResult("IT", "Normal", "Software routes to IT; the cost is below the spend threshold.", ["POL-ROUTE-002", "POL-ROUTE-004"], 0.9, false);
            case "cross-request":
                var other = await context.Tools.GetRequestAsync("REQ-1006", cancellationToken);
                var own = await context.Tools.GetRequestAsync(context.RequestId, cancellationToken);
                Assert.Contains("not_permitted", other);
                Assert.Contains(context.Title, own);
                // Data minimization: comments and people data never reach the AI service.
                Assert.DoesNotContain("comments", own);
                Assert.DoesNotContain("requester", own, StringComparison.OrdinalIgnoreCase);
                return new TriageResult("IT", "Normal", "Read only the permitted request.", ["POL-ROUTE-001"], 0.8, false);
            case "slow":
                await Task.Delay(TimeSpan.FromSeconds(30), cancellationToken);
                throw new InvalidOperationException("unreachable");
            default:
                throw new TriageUnavailableException("Provider offline.");
        }
    }
}

public sealed class BlockingTriageProvider : ITriageProvider
{
    private static TaskCompletionSource<bool> started = NewSignal();
    private static TaskCompletionSource<TriageResult> resultGate = NewResultGate();

    public string Id => "blocking-test";
    public bool IsSample => false;

    public static void Reset()
    {
        started = NewSignal();
        resultGate = NewResultGate();
    }

    public static Task WaitUntilStartedAsync(TimeSpan timeout) => started.Task.WaitAsync(timeout);

    public static void Release(TriageResult result) => resultGate.TrySetResult(result);

    public Task<TriageResult> RecommendAsync(TriageContext context, CancellationToken cancellationToken)
    {
        started.TrySetResult(true);
        return resultGate.Task.WaitAsync(cancellationToken);
    }

    private static TaskCompletionSource<bool> NewSignal() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    private static TaskCompletionSource<TriageResult> NewResultGate() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);
}

public sealed class BlockingTriageFixture : ApiFixture
{
    protected override void ConfigureTestServices(IServiceCollection services)
    {
        services.RemoveAll<ITriageProvider>();
        services.AddSingleton<ITriageProvider, BlockingTriageProvider>();
    }
}

public sealed class GuardedTriageFixture : ApiFixture
{
    protected override void ConfigureTestServices(IServiceCollection services)
    {
        services.RemoveAll<ITriageProvider>();
        services.AddSingleton<ITriageProvider, MisbehavingTriageProvider>();
        services.Configure<TriageOptions>(o => o.TimeoutSeconds = 2);
    }
}

public sealed class TriageGuardTests(GuardedTriageFixture api) : IClassFixture<GuardedTriageFixture>
{
    [Fact]
    public async Task Recommendation_claiming_approval_is_rejected()
    {
        MisbehavingTriageProvider.Mode = "approval-claim";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1002/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.BadGateway, response.StatusCode);
        Assert.Equal("triage.invalid_output", await response.Code());
    }

    [Fact]
    public async Task Recommendation_citing_unknown_policy_is_rejected()
    {
        MisbehavingTriageProvider.Mode = "unknown-policy";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1002/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.BadGateway, response.StatusCode);
    }

    [Fact]
    public async Task Conflicting_citations_are_escalated_even_when_the_provider_does_not_flag_them()
    {
        MisbehavingTriageProvider.Mode = "conflict-unflagged";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1012/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var rec = await response.Read<RecommendationDto>();
        Assert.True(rec.NeedsHumanReview);
        Assert.Contains("human review required", rec.Rationale);
    }

    [Fact]
    public async Task Citing_the_spend_policy_below_its_threshold_is_not_a_conflict()
    {
        MisbehavingTriageProvider.Mode = "below-threshold-citation";
        var rec = await (await api.As("u-ben").PostAsync("/api/requests/REQ-1005/triage-recommendations", null)).Read<RecommendationDto>();
        Assert.False(rec.NeedsHumanReview);
    }

    [Fact]
    public async Task Tools_only_expose_the_request_being_triaged_and_are_audited()
    {
        MisbehavingTriageProvider.Mode = "cross-request";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1014/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);

        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var toolCalls = await db.AuditEvents.Where(a => a.Action == "triage.tool_call").Select(a => a.Details).ToListAsync();
        Assert.Contains(toolCalls, d => d.Contains("denied") && d.Contains("REQ-1006"));
        Assert.Contains(toolCalls, d => d.Contains("\"ok\"") && d.Contains("REQ-1014"));
    }

    [Fact]
    public async Task Slow_provider_times_out_with_clear_error()
    {
        MisbehavingTriageProvider.Mode = "slow";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1002/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.GatewayTimeout, response.StatusCode);
        Assert.Equal("triage.timeout", await response.Code());
    }

    [Fact]
    public async Task Unavailable_provider_returns_service_unavailable()
    {
        MisbehavingTriageProvider.Mode = "offline";
        var response = await api.As("u-ben").PostAsync("/api/requests/REQ-1002/triage-recommendations", null);
        Assert.Equal(HttpStatusCode.ServiceUnavailable, response.StatusCode);
        Assert.Equal("triage.unavailable", await response.Code());
    }
}

public sealed class FoundryOutputParsingTests
{
    private const string Answer = """{"suggestedDepartmentId":"FIN","suggestedPriority":"Normal","rationale":"r","policyIds":["POL-ROUTE-007"],"confidence":0.6,"needsHumanReview":true,"clarifyingQuestion":"q"}""";

    [Fact]
    public void Single_answer_is_parsed()
    {
        var output = RequestHub.Api.Triage.FoundryTriageProvider.ParseOutput(Answer, out var answers);
        Assert.Equal(1, answers);
        Assert.Equal("FIN", output!.SuggestedDepartmentId);
    }

    [Fact]
    public void Repeated_answer_uses_the_last_object()
    {
        var output = RequestHub.Api.Triage.FoundryTriageProvider.ParseOutput(Answer.Replace("FIN", "HR", StringComparison.Ordinal) + Answer, out var answers);
        Assert.Equal(2, answers);
        Assert.Equal("FIN", output!.SuggestedDepartmentId);
    }

    [Fact]
    public void Non_json_text_is_rejected() =>
        Assert.ThrowsAny<System.Text.Json.JsonException>(() => RequestHub.Api.Triage.FoundryTriageProvider.ParseOutput("Routing: IT", out _));
}
