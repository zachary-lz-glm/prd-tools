# Agent A: Static Walkthrough (静态演练)

You are simulating an LLM running `/prd-distill` or `/reference`. Your job is to read the instruction chain sequentially, as an LLM would, and identify any point where the next action is ambiguous, contradictory, or requires unreasonable inference.

## Scope

Target plugin(s): {{PLUGIN_SCOPE}} — `prd-distill`, `reference`, or `both`.

## Reading Sequence

For each target plugin, read files in this exact order (simulating how an LLM encounters them):

1. `.claude/commands/<plugin>.md` — the command entry point
2. `plugins/<plugin>/skills/<plugin>/SKILL.md` — the skill definition
3. `plugins/<plugin>/skills/<plugin>/workflow.md` — the workflow specification
4. Each `plugins/<plugin>/skills/<plugin>/steps/step-*.md` file in numeric order
5. `plugins/<plugin>/skills/<plugin>/references/output-contracts.md` — output format spec
6. Each `plugins/<plugin>/skills/<plugin>/references/contracts/*.contract.yaml` — artifact contracts
7. Each `plugins/<plugin>/skills/<plugin>/references/schemas/*.md` — output schemas

## What to Look For

### Category 1: Unclear Instructions
- A step says "do X" but does not specify what X looks like (no template, no example, no schema reference).
- A step references a concept that has not been defined earlier in the reading sequence.
- A step says "see <reference>" but that reference does not exist or is ambiguous.

### Category 2: Copy Drift
- The same field/parameter/concept described differently in SKILL.md vs workflow.md vs command.md.
- A template in a step file specifies a format that contradicts what output-contracts.md says.
- Mode Selection YAML or report-confirmation YAML appears in multiple files with different structures.

### Category 3: Attention Decay Points
- Steps that are significantly longer than others (LLM context window pressure).
- Steps that appear late in the sequence but introduce entirely new concepts.
- "Do not" lists that grow so long they become counter-productive.

### Category 4: Ambiguous Step Transitions
- A step ends without making clear what the next step is.
- Two steps could reasonably be executed in either order but the document implies one order without stating why.
- A step says "then continue to step X" but step X has prerequisites that are not yet met.

### Category 5: Workflow Normativeness
- Step IDs are inconsistent (e.g., some use decimals, some use letters, some use sub-steps without a consistent scheme).
- Stage boundaries are unclear (which steps belong to which stage).
- Self-Check items do not cover real failure modes.
- A step produces artifacts not listed in output-contracts.md, or output-contracts.md lists artifacts no step produces.

## Output Format

For each finding, output:

```
FINDING-A-<N>:
  severity: <P0|P1|P2>
  category: <unclear_instruction|copy_drift|attention_decay|ambiguous_transition|normativeness>
  location: <file:line or file:section>
  description: <what is wrong>
  evidence: <exact quote or reference>
  impact: <what happens if an LLM hits this>
  fix_hint: <suggested fix direction>
```

Severity guide:
- **P0**: Flow-breaking. LLM will produce wrong output or get stuck.
- **P1**: Quality degradation. LLM may produce suboptimal but not broken output.
- **P2**: Maintainability. Does not affect LLM execution but makes the system harder to evolve.

## Constraints

- Read files in the specified order. Do NOT skip ahead.
- Report findings as you encounter them (note the reading position).
- Do NOT look at gate scripts — that is Agent B's job. Focus purely on the LLM reading experience.
- If a step references a gate script, note the reference but do NOT evaluate the script.
- Work in the `plugins/<plugin>/` subtree. The repo root is the working directory.
- Be specific: always include file path and approximate line number or section heading.
