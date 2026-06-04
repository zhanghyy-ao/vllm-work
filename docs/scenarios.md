# Scenario Notes

This homework project models browser-control tasks with a deterministic harness.

## Original scenarios

- `comparison_recommendation`
- `form_filling`
- `research`

## Added scenarios

- `booking_reservation`: booking, reservation, ticketing, hotel drafts
- `lead_collection`: structured lead extraction and CSV export
- `monitoring_alerts`: page baselining, tracked changes, alert setup
- `qa_regression`: page checks, regression assertions, issue reports

These scenarios share the same runtime loop:

1. Observe page
2. Route goal to a scenario plan
3. Execute browser tools
4. Verify each step
5. Record traces and metrics
