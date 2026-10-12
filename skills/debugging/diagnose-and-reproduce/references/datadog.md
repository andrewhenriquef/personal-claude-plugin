# Datadog as the source of the report

Use in Step 1 of `diagnose-and-reproduce`, and in `confirm-root-cause` when an experiment needs production data. This file covers reading evidence about a bug. For reviewing a diff against Datadog setup (tracing, tags, monitors), see `reliability-analysis/references/datadog.md`.

Sources: [Datadog MCP Server tools](https://docs.datadoghq.com/mcp_server/tools.md), [Datadog MCP Server setup](https://docs.datadoghq.com/mcp_server/setup.md), [Error Tracking for backend services](https://docs.datadoghq.com/tracing/error_tracking/), [Unified service tagging](https://docs.datadoghq.com/getting_started/tagging/unified_service_tagging/), and the [Datadog MCP Server announcement](https://www.datadoghq.com/product/mcp-server/).

## If the tools are not there

Datadog MCP tools may not be in the session. Then write "No Datadog data" in the symptom card and ask the user for the numbers or the redacted artifact you need. Do not ask the user to install a plugin and do not stop the run.

The server groups tools into toolsets. `core` is on by default. `apm`, `error-tracking`, `alerting`, and others need the user to enable them (for example `?toolsets=core,apm,error-tracking`). If a tool you need is missing, say which toolset it needs.

## Read-only rule

Call only tools that read. Never call a tool that creates, updates, deletes, upserts, manages, triggers, steers, or executes. This includes `create_datadog_monitor`, `create_datadog_notebook`, `update_datadog_case`, `update_datadog_error_tracking_issue`, `manage_*`, `upsert_*`, `trigger_*`, `execute_code`, and tools that enable a debugger or a logpoint. If a monitor or a notebook would help, put the suggestion in the report. The user creates it.

State for each call: the tool, the service, the environment, and the time window.

## Question to tool

| Question | Read-only tool | Toolset |
|---|---|---|
| Is this error a known issue? How often? Since when? | `search_datadog_error_tracking_issues`, `get_datadog_error_tracking_issue` | error-tracking |
| Did it start with a version? | `analyze_datadog_error_tracking_errors` (break down by version), `get_datadog_error_tracking_analytics` (daily counts, regressions after a deploy) | error-tracking |
| What did one failing request do, end to end? | `get_datadog_trace`, `apm_query_trace` | core, apm |
| Which requests fail, and what do they share (route, tenant, version, region)? | `search_datadog_spans`, `aggregate_spans` | core |
| Where does the time go? | `apm_latency_bottleneck_summary`, `aggregate_spans` | apm, core |
| What do the logs say around the failure? | `search_datadog_logs`, `analyze_datadog_logs` (counts first, samples second) | core |
| Did a deploy or a config change happen? | `search_datadog_events` | core |
| Is a resource growing (goroutines, threads, heap, queue)? | `search_datadog_metrics`, `get_datadog_metric`, `get_datadog_metric_context` | core |
| Which service or team owns this? What does it call? | `search_datadog_entities` | core |
| Is there an incident or a monitor already? | `search_datadog_incidents`, `get_datadog_incident`, `search_datadog_monitors` | core |
| Front-end errors? | `search_datadog_rum_events`, `aggregate_rum_events` | rum |

## Investigation order

1. **Start narrow.** Service, environment, error class, a time window that holds the first occurrence. Count before you read samples.
2. **Find the first occurrence and the last known good.** The change just before the first occurrence is the top suspect (deploy, flag, data load, dependency). Use `search_datadog_events`.
3. **Compare failing and passing.** Take one failing trace and one passing trace of the same route. The difference is where to look first. This is the "isolate the difference" step of delta debugging.
4. **Find what the failures share.** Group by version, route, tenant, region, input shape. A shared factor is a hypothesis. A factor that every request has is not.
5. **Keep IDs, not bodies.** Write trace IDs, issue IDs, and query text in the symptom card. Redact before you quote a log line or a span tag ([redaction.md](redaction.md)).

## What Datadog data can and cannot prove

- It shows **what happened** on the paths that report to Datadog. A handled error that was not set on the span, or a log line with no trace ID, is missing. "No errors in Datadog" does not prove there were none.
- It does **not** show why. A correlation (errors rise after version X) is a hypothesis for `form-hypotheses`. Only an experiment that could have failed confirms a cause.
- Sampling and retention hide old or rare traces. State the window and the sampling you saw.
- Production numbers are evidence about production, not about the code in the working tree. Check that the commit you debug matches the deployed version (`DD_VERSION` or the deploy event).

## Turning telemetry into a reproduction

Telemetry rarely gives a runnable test by itself. Use it to pick the **seam**, the **input shape**, and the **conditions**:

- The failing span names the function or route where the loop should start.
- The error message and stack give the assertion: the exact symptom the test must show.
- The request shape (redacted, with synthetic values) is the fixture.
- Timing, concurrency, or data size in the failing traces tells `reproduce-bug` whether the bug needs load, parallelism, or a large input.
