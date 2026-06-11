---
name: token-efficiency
description: "Optimize token consumption and prevent context bloat during Codex agent execution. Use this skill whenever an agent is working on: (1) Long-running multi-step tasks that risk accumulating stale context, (2) Complex codebase exploration that could trigger repeated full-scans, (3) Tasks requiring file analysis where caching and incremental updates would reduce overhead, (4) Any session where token burn rate concerns are raised. This skill provides compression, caching, incremental analysis, context pruning, loop detection, read budgeting, context memory, action-first bias, cost-awareness, and stop-condition rules."
---

# Token Efficiency Protocol

Every token must create value. No repeated reads, no repeated reasoning, no context bloat.

## Core Workflow

Before every action, run this checklist in order:

```
□ CACHE CHECK → File in cache? Hash unchanged? Use cache, don't re-read.
□ CONTEXT PRUNE → Drop completed tasks, resolved issues, stale discussion.
□ LOOP CHECK → Same conclusion 3+ rounds? Stop analyzing. Execute.
□ BUDGET CHECK → Under read budget? If over, justify before reading.
□ COST CHECK → Token cost > expected value? Use rg/grep/summary instead.
□ STOP CHECK → Task done? Info sufficient? No new value? STOP.
```

## Critical Tools (Use These First)

### rg (ripgrep) — Your Primary Weapon
Before reading any file, ask: "Can I rg this?" rg is 10-100x cheaper than reading a file because:
- rg pattern returns only matching lines (~10 tokens)
- A file read returns the entire file (200-5000+ tokens)

**Rules:**
- Need a function signature? `rg '^def |^class ' file.py`
- Need to find a string? `rg 'PATTERN' --include='*.py'`
- Need to understand a module? `rg '^(def |class |import |from )' module.py` — returns structure in ~50 tokens
- Only do full file reads when you need to modify code or understand exact logic.

### Parallel Reads via multi_tool_use.parallel
When you MUST read multiple files, read them in parallel, not sequentially. Each tool call has overhead (~100+ tokens of system framing). Reading 5 files sequentially = 5x overhead. Reading 5 files in parallel = 1x overhead.

### Tool Call Overhead Awareness
Every shell_command, cat, or file read tool call burns tokens before returning any data:
- Tool call framing: ~50-100 tokens per call
- Output rendering: depends on output size
- **Cost = framing_tokens + output_tokens**

Minimize tool calls, not just file content. One rg call returning 5 lines is cheaper than 5 separate rg calls each returning 1 line.

### Minimize Round Trips
Each conversation turn with the user has a large fixed token cost (system prompt + tool definitions + conversation history). When you can batch multiple operations into one tool call, do it. One multi_tool_use.parallel with 5 reads is cheaper than 5 sequential turns.

---

## The 10 Rules

### 1. History Compression
When you've understood a conversation block, don't re-read it. Generate and use only:
- **Task Summary**: `[TASK]` — What was being done.
- **Decision Summary**: `[DECISION]` — What was decided.
- **File Summary**: `[FILE]` — What files were analyzed and key findings.
- **Progress Summary**: `[PROGRESS]` — What's done, what's pending.

Use `scripts/file_cache.py` to manage file-level summaries persistently.

### 2. File Cache
Track every file you read. Structure:
```
{
  "hash": "a1b2c3d4", "summary": "Config class with DB logic.",
  "key_findings": ["Config at line 10", "DB URL from env"]
}
```
If hash matches on next encounter → **do not re-read**. Use `summary` + `key_findings`.

Use `scripts/file_cache.py` to manage cache:
```
python file_cache.py update src/main.py --summary "..." --findings "finding1|finding2"
python file_cache.py check src/main.py
```

### 3. Incremental Analysis
Never re-scan unchanged files. Only analyze:
- New files (not in cache)
- Modified files (hash changed)
- Files directly required by current task

Track scope with `[SCOPE] {type:new|modified|task} {path}`.

### 4. Context Pruning
At the start of each turn, drop:
- Completed task blocks >2 turns old
- Superseded decisions
- Full conversation dumps — keep only summaries
- Dead-end reasoning chains

**Retain**: Final conclusions, current task state, relevant file summaries.

### 5. Loop Prevention
Track conclusions per topic:
```
[LOOP:topic] round=3 → same conclusion → STOP analyzing → EXECUTE
```
If the same conclusion repeats 3 consecutive turns on the same topic, stop analyzing and execute immediately. No fourth analysis.

### 6. Read Budget
Per turn default limits:
- **10 files** max read
- **5000 lines** max read
- **50 KB** max read
- **1 full project scan** per 10 turns max

Use `scripts/budget_check.py` to track:
```
python budget_check.py new-turn
python budget_check.py track file.py 150 4096
python budget_check.py check --files 2 --lines 500
```

If you need to exceed any limit: `[BUDGET_OVERRIDE] {reason} {estimated_cost}`

### 7. Context Memory
Maintain a `[CONTEXT]` block that persists across turns:
```
[CONTEXT]
PROJECT: web-app-monorepo — Next.js + FastAPI + Postgres
COMPLETED_TASKS: ["auth flow", "API routes"]
KNOWN_ISSUES: ["rate limiter needs tuning"]
CONFIRMED: ["DB_URL is env var based", "auth uses JWTs"]
```
Consult this before any exploration. If the answer is here, don't go looking.

### 8. Action-First
Priority ladder (descending):
1. **Execute** — Make the change. Run the command.
2. **rg/search** — quick targeted query (cost: ~10-50 tokens)
3. **Cache hit** — existing summary (cost: ~0 tokens)
4. **Read summary** — from cache or index
5. **Read structure** — rg for def/class/import lines
6. **Full read** — last resort (cost: 200-5000+ tokens)

Default to the highest-action item possible.

### 9. Cost Awareness
Before any large operation, estimate:
```
[COST_ESTIMATE] action: "Full read" → estimated: 25000 tokens
cheaper: rg 'DATABASE_URL' → ~50 tokens
→ Choose cheaper
```

Token cost reference:
| Operation | Est. tokens |
|-----------|------------|
| rg pattern across project | ~10-50 |
| Single file >200 lines | ~500-2000 |
| 10 file reads | ~5000-25000 |
| Tool call overhead | ~50-100/call |

Use `scripts/estimate_token_cost.py` for pre-read estimation.

### 10. Stop Conditions
Stop immediately when ANY of these is true:
- Task achieved → `[STOP]`
- Info in cache/context → `[STOP]`
- 3+ same-conclusion loops → `[STOP]`
- Cost exceeds value with no path forward → `[STOP]`

---

## Token Conservation Markers

| Marker | Meaning |
|--------|---------|
| `[CACHE:HIT]` | Using cached data |
| `[CACHE:MISS]` | File not cached |
| `[PRUNE]` | Dropped stale context |
| `[LOOP:n]` | Loop at round n |
| `[BUDGET:x/y]` | Read budget x of y used |
| `[CONTEXT:MEM]` | Answer from memory |
| `[STOP]` | Stop condition met |
| `[SCOPE:new/mod/task]` | Incremental scope |

## Reference Files

For detailed guidance on each capability:
- **[references/core-principles.md](references/core-principles.md)** — Deep walkthrough of all 10 rules
- **[references/compression-protocols.md](references/compression-protocols.md)** — Compression formats
- **[references/stop-conditions.md](references/stop-conditions.md)** — Stop decision tree

Load these only when you need detailed examples for ambiguous situations.
