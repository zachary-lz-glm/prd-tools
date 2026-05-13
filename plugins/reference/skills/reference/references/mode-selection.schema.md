# Mode Selection YAML Schema

Written into `_prd-tools/build/reference-workflow-state.yaml` during the mode selection step.

## Schema

```yaml
human_checkpoints:
  mode_selection:
    status: approved                  # enum: pending, approved, skipped
    confirmed_at: "2026-05-12T..."   # ISO-8601 timestamp (auto)
    selected_mode: "F_then_A"        # enum: F_then_A, F_only, A_only, B, B2, C, E, T, T2
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | `approved` (user confirmed), `pending` (awaiting), `skipped` (chat mode) |
| `confirmed_at` | string | auto | ISO-8601 timestamp, set by `set_human_checkpoint()` |
| `selected_mode` | enum | yes | One of: `F_then_A`, `F_only`, `A_only`, `B`, `B2`, `C`, `E`, `T`, `T2` |

## Modes

| Mode | Description |
|------|-------------|
| `F_then_A` | Full reference build, then AI distill |
| `F_only` | Full reference build only |
| `A_only` | AI distill only (no reference) |
| `B` | Lightweight reference scan |
| `B2` | Lightweight + cross-validation |
| `C` | Contract-only reference |
| `E` | Emergency minimal scan |
| `T` | Team aggregation — aggregate member repos' reference into team repo |
| `T2` | Team inheritance — inherit team-common knowledge into member repo |
