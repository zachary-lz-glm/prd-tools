# Mode Selection YAML Schema

Written into `_prd-tools/build/reference-workflow-state.yaml` during the mode selection step.

## Schema

```yaml
human_checkpoints:
  mode_selection:
    status: approved                  # enum: pending, approved, skipped
    confirmed_at: "2026-05-12T..."   # ISO-8601 timestamp
    selected_mode: "F_then_A"        # enum: F_then_A, F_only, A_only, B, B2, C, E, T, T2
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | `approved` (user confirmed), `pending` (awaiting), `skipped` (chat mode) |
| `confirmed_at` | string | auto | ISO-8601 timestamp |
| `selected_mode` | enum | yes | One of: `F_then_A`, `F_only`, `A_only`, `B`, `B2`, `C`, `E`, `T`, `T2` |

## Modes

| Mode | Description |
|------|-------------|
| `F_then_A` | Full reference build with context collection |
| `F_only` | Context collection only |
| `A_only` | Full build without context collection |
| `B` | Incremental update based on git diff |
| `B2` | Health check |
| `C` | Quality gate |
| `E` | Feedback ingest |
| `T` | Team aggregation — aggregate member repos' reference into team repo |
| `T2` | Team inheritance — inherit team-common knowledge into member repo |
