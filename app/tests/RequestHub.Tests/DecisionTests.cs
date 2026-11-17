using System.Net;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using RequestHub.Core.Data;
using RequestHub.Core.Services;

namespace RequestHub.Tests;

public sealed class DecisionTests(ApiFixture api) : IClassFixture<ApiFixture>
{
    private static object NewRequest() => new
    {
        title = $"Decision test {Guid.NewGuid():N}",
        description = "A request created for decision regression coverage.",
        category = "equipment",
        departmentId = "IT",
        priority = "Normal",
    };

    private async Task<string> SubmitRequestAsync()
    {
        var response = await api.As("u-ava").PostJson("/api/requests", NewRequest());
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        return (await response.Read<RequestDetailDto>()).Id;
    }

    private async Task AssertSingleDecisionAndNotificationAsync(string id, string outcome, string approver)
    {
        var detail = await (await api.As("u-ava").GetAsync($"/api/requests/{id}")).Read<RequestDetailDto>();
        Assert.Equal(outcome, detail.Status);
        Assert.Equal(outcome, detail.Decision!.Outcome);
        Assert.Equal(approver, detail.Decision.DecidedBy.Id);

        var history = await (await api.As("u-ava").GetAsync($"/api/requests/{id}/history")).Read<List<AuditEventDto>>();
        Assert.Single(history, item => item.Action == "decision.recorded");

        await using var scope = api.Factory.Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<RequestHubDbContext>();
        var number = int.Parse(id["REQ-".Length..]);
        var requestId = await db.Requests.Where(request => request.Number == number).Select(request => request.Id).SingleAsync();
        Assert.Equal(1, await db.Notifications.CountAsync(notification =>
            notification.RequestId == requestId && notification.Type == "request.decided"));
    }

    [Fact]
    public async Task Same_key_retry_returns_original_and_later_decision_conflicts()
    {
        var id = await SubmitRequestAsync();
        var chloe = api.As("u-chloe");
        var first = await chloe.PostJson($"/api/requests/{id}/decisions", new { outcome = "Approved" }, "decision-retry-key");
        var original = await first.Read<DecisionDto>();
        var retry = await chloe.PostJson($"/api/requests/{id}/decisions", new { outcome = "Approved" }, "decision-retry-key");
        var replay = await retry.Read<DecisionDto>();

        Assert.Equal(HttpStatusCode.Created, first.StatusCode);
        Assert.Equal(HttpStatusCode.OK, retry.StatusCode);
        Assert.Equal(original, replay);

        var conflict = await api.As("u-dan").PostJson(
            $"/api/requests/{id}/decisions",
            new { outcome = "Rejected", comment = "Changed my mind." });
        Assert.Equal(HttpStatusCode.Conflict, conflict.StatusCode);
        Assert.Equal("decision.already_decided", await conflict.Code());
        using (var body = JsonDocument.Parse(await conflict.Content.ReadAsStringAsync()))
        {
            var existing = body.RootElement.GetProperty("decision");
            Assert.Equal("Approved", existing.GetProperty("outcome").GetString());
            Assert.Equal("u-chloe", existing.GetProperty("decidedBy").GetProperty("id").GetString());
        }

        await AssertSingleDecisionAndNotificationAsync(id, "Approved", "u-chloe");
    }

    [Fact]
    public async Task Concurrent_same_key_retries_create_one_decision_and_replay_the_rest()
    {
        var id = await SubmitRequestAsync();
        var chloe = api.As("u-chloe");
        var responses = await Task.WhenAll(Enumerable.Range(0, 8).Select(_ =>
            chloe.PostJson($"/api/requests/{id}/decisions", new { outcome = "Approved" }, "parallel-decision-key")));

        Assert.Equal(1, responses.Count(response => response.StatusCode == HttpStatusCode.Created));
        Assert.Equal(7, responses.Count(response => response.StatusCode == HttpStatusCode.OK));
        await AssertSingleDecisionAndNotificationAsync(id, "Approved", "u-chloe");
    }

    [Fact]
    public async Task Concurrent_approvers_record_only_the_first_decision()
    {
        var id = await SubmitRequestAsync();
        var decisions = await Task.WhenAll(
            api.As("u-chloe").PostJson($"/api/requests/{id}/decisions", new { outcome = "Approved" }),
            api.As("u-dan").PostJson($"/api/requests/{id}/decisions", new { outcome = "Rejected", comment = "Not approved." }));

        Assert.Single(decisions, response => response.StatusCode == HttpStatusCode.Created);
        Assert.Single(decisions, response => response.StatusCode == HttpStatusCode.Conflict);
        var conflict = decisions.Single(response => response.StatusCode == HttpStatusCode.Conflict);
        Assert.Equal("decision.already_decided", await conflict.Code());

        var detail = await (await api.As("u-ava").GetAsync($"/api/requests/{id}")).Read<RequestDetailDto>();
        await AssertSingleDecisionAndNotificationAsync(id, detail.Status, detail.Decision!.DecidedBy.Id);
    }

    [Fact]
    public async Task Concurrent_double_click_records_one_decision_and_conflicts_for_the_rest()
    {
        var id = await SubmitRequestAsync();
        var chloe = api.As("u-chloe");
        var responses = await Task.WhenAll(Enumerable.Range(0, 8).Select(_ =>
            chloe.PostJson($"/api/requests/{id}/decisions", new { outcome = "Approved" })));

        Assert.Equal(1, responses.Count(response => response.StatusCode == HttpStatusCode.Created));
        Assert.Equal(7, responses.Count(response => response.StatusCode == HttpStatusCode.Conflict));
        foreach (var response in responses.Where(response => response.StatusCode == HttpStatusCode.Conflict))
        {
            Assert.Equal("decision.already_decided", await response.Code());
        }
        await AssertSingleDecisionAndNotificationAsync(id, "Approved", "u-chloe");
    }
}
