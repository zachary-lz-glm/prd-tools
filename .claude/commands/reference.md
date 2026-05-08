---
description: Build or update the project reference knowledge base before PRD distillation.
---

# /reference

Use this command before `/prd-distill`, or when the project knowledge base needs to be created, checked, updated, or backfilled after a delivered PRD.

Run the `reference` workflow with the smallest mode that matches the user's intent:

1. First adoption: Mode F context collection, then Mode A full build.
2. Existing project check: Mode B2 health check.
3. Source or contract changes: Mode B incremental update.
4. Release readiness: Mode C quality gate.
5. Post-PRD learning: Mode E feedback ingest.

Keep the reference single-repo authoritative. Cross-repo facts stay `needs_confirmation` unless there is owner or source evidence.
