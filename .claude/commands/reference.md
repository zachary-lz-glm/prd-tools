# /reference

You are running the PRD Tools `reference` workflow. This command is a thin compatibility wrapper for clients or model gateways that do not reliably auto-trigger Claude Code skills.

Before doing any project analysis, you MUST read and follow:

1. `.claude/skills/reference/SKILL.md`
2. `.claude/skills/reference/workflow.md`

For full builds, you MUST execute the standard ordered workflow:

1. structure scan
2. `steps/step-02a-codebase.md` -> `01-codebase.yaml`
3. `steps/step-02b-coding-rules.md` -> `02-coding-rules.yaml`
4. `steps/step-02c-contracts.md` -> `03-contracts.yaml`
5. `steps/step-02d-routing.md` -> `04-routing-playbooks.yaml`
6. `steps/step-02e-domain-portal.md` -> `05-domain.yaml` + `00-portal.md`
7. render `portal.html` with `.prd-tools/scripts/render-reference-portal.py`
8. build Evidence Index with `.prd-tools/scripts/build-index.py`
9. run `.prd-tools/scripts/reference-quality-gate.py --root .`

Hard gates:

- Do not handwrite `portal.html`.
- Do not skip `_prd-tools/reference/index/`.
- Do not claim `/reference` is complete if index files are missing.
- Do not claim `/reference` is complete if the quality gate exits with code 2.
- The final response must include the index manifest summary when index exists.

Now continue with the user's `/reference` request.
