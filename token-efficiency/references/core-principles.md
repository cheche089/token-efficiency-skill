# Core Principles — Deep Dive

This reference provides detailed guidance for each of the 10 Token Efficiency rules with concrete examples and edge-case handling.

---

## 1. History Compression

### When to compress
Compress when a conversation block has reached a natural conclusion — a task is done, a decision is made, a file is analyzed.

### Compression format
```
[TASK] {short label} — {one-line description}
[DECISION] {topic} → {conclusion} (reason: {key rationale})
[FILE] {path} [{hash[:8]}] → {key finding}
[PROGRESS] {task} | {done|pending|blocked} | {blocker if any}
```

### Example
```
Before (full history — ~500 tokens):
"Let me look at the auth module. First I checked config.py and found..."
[DECISION] Use JWT with RS256, keys stored in Vault
[FILE] src/auth/config.py [a1b2c3d4] → JWT signing config, RS256
[FILE] src/auth/middleware.py [e5f6g7h8] → Token validation, 3 dependencies
[PROGRESS] Auth verification | done | none

After (compressed — ~80 tokens):
[TASK] Auth module security audit
[DECISION] Auth method → JWT RS256 with Vault keys
[FILE] src/auth/config.py [a1b2c3d4], middleware.py [e5f6g7h8]
[PROGRESS] Auth verification | done | none
```

### Multi-step tasks
For complex tasks spanning many turns, maintain a running compressed summary at the end of each turn. When you would normally re-read earlier history, read only the most recent compressed summary block. Only decompress (read full history) if the summary lacks information needed for the current decision.

---

## 2. File Cache

### Cache data structure
Store cache in memory during a session. Persist to `{workspace}/.codex/token-cache.json` if available.

```json
{
  "files": {
    "src/main.py": {
      "hash": "sha256:abc123...",
      "size": 15300,
      "mtime": "2026-06-11T12:00:00Z",
      "summary": "Entry point. Reads config, starts server.",
      "key_findings": [
        "Entry point at main()",
        "Calls config.init() then server.start()"
      ],
      "imports": ["config", "server", "cli"],
      "classes": ["App"],
      "functions": ["main", "setup_logging"],
      "last_read": "2026-06-11T12:00:00Z",
      "read_count": 1
    }
  },
  "structure": {
    "src/": {
      "type": "dir",
      "files": ["main.py", "config.py", "models/"]
    },
    "src/models/": {
      "type": "dir",
      "files": ["user.py", "order.py"]
    }
  }
}
```

### Hash comparison
When encountering a file, compute its hash (first 8 chars of sha256, or file size + mtime if hash is expensive). If unchanged:
```
[CACHE:HIT] src/main.py [abc1234] → summary + key_findings used
```
If changed:
```
[CACHE:MISS] src/main.py [abc1234 → def5678] → re-reading
```

### Cache hygiene
- Evict entries when the underlying file is deleted
- Update entries when re-reading a modified file
- Never cache files > 100 KB without summarizing first
- Track read_count — if a file has been read 5+ times, flag it as "frequently accessed — consider keeping high-level summary always in context"

---

## 3. Incremental Analysis

### Scope types
| Scope | Meaning | Action |
|-------|---------|--------|
| `[SCOPE:new]` | File discovered not in cache | Full read |
| `[SCOPE:mod]` | Hash changed since cache | Re-read, update cache |
| `[SCOPE:task]` | Directly required by current task | Full read (if not cached) |
| `[SCOPE:skip]` | File exists, cached, unchanged | Skip entirely |

### Project scanning protocol
When asked to "look at the project" or "scan the codebase":
1. First check if `structure` exists in cache
2. If yes, show cached structure (`[CACHE:HIT] project structure`)
3. If no, do one shallow scan (list dirs, key files) and cache it
4. From the structure, only read files relevant to the current task
5. Mark all other files as `[SCOPE:skip]`

### Example
```
User: "Look at this project and understand the API routes."
Agent: [SCOPE:new] project structure (caching)
  → src/api/v1/users.py, src/api/v1/orders.py
  → tests/api/test_users.py, tests/api/test_orders.py
  → All other directories: [SCOPE:skip]

Next turn, user asks: "Now look at the database models."
Agent: [SCOPE:mod] let me check hash of models/
  → src/models/user.py (unchanged) [CACHE:HIT]
  → src/models/order.py (unchanged) [CACHE:HIT]
  → src/models/payment.py (new) [SCOPE:new]
  → Only reading payment.py fresh
```

---

## 4. Context Pruning

### Pruning checklist
At the start of each turn, ask:
1. **Is this block marked [COMPLETED] and >2 turns old?** → Drop it, keep only final summary line.
2. **Is this discussion resolved?** → Keep final decision only.
3. **Is this reasoning a dead end?** → Drop entirely.
4. **Is this a detailed trace/error log that was already analyzed?** → Keep only the root cause conclusion.
5. **Is this a file read from 5+ turns ago?** → Keep only the cache entry, remove the full content from context.

### What to always retain
- Current task objective
- Active decisions
- Relevant file summaries (from cache)
- Next action / todo list

### Example before pruning
```
Turn 12 context contains:
- Turn 1: User request "Add pagination to user list"
- Turn 2-3: Analysis of existing user routes (full file reads of users.py)
- Turn 4: Decision to use page/page_size query params
- Turn 5-6: Implementation work (full file reads, diffs)
- Turn 7: Bug fix — off-by-one in pagination
- Turn 8: Review of test file
- Turn 9-11: Additional feature request "Add sort options"
- Turn 12 current state
```

### After pruning
```
[TASK] Add pagination (done) and sort options (in progress)
[DECISION] Pagination → page/page_size with limit 100
[DECISION] Sort → sort_by + order query params
[FILE] src/api/users.py [abc123] → original + pagination diff
[FILE] src/api/users_test.py [def456] → pagination tests added
[PROGRESS] Pagination | done | none
[PROGRESS] Sort options | in_progress | implementing sort_by, order params
[CONTEXT] User request per turn 12: "Add sort options to user list endpoint"
```

---

## 5. Loop Prevention

### Detection pattern
```
Turn N: [ANALYSIS] Found structure X, conclusion Y
Turn N+1: [ANALYSIS] Same structure X, same conclusion Y
Turn N+2: [ANALYSIS] Same structure X, same conclusion Y
→ [LOOP:3] topic="structure X analysis" — no new info in 3 rounds
→ [STOP analyzing] → [START executing]
```

### False positive prevention
Only trigger loop detection when:
- The topic is the same (same files, same question)
- The conclusion is materially identical
- No new information was discovered
- No new files were read

If any of these is new, reset the counter.

### Remediation
When a loop is detected:
1. `[LOOP:N]` — Declare the loop with round count
2. State the repeated conclusion
3. If the conclusion is actionable → **execute it now**
4. If the conclusion is not actionable → identify blocking question, ask once
5. Never re-enter analysis on the same topic

---

## 6. Read Budget

### Budget tracking
Maintain a running counter per turn:
```
[BUDGET:files=3/10 lines=1200/5000 bytes=45KB/50KB]
```

Reset at the start of each turn.

### Override protocol
Only approve a budget override if:
1. The task explicitly requires analyzing many files (e.g., "refactor all modules")
2. Override provides clear benefit vs. cost
3. There is no incremental/cheaper alternative

Example override:
```
[BUDGET_OVERRIDE] Need to read 15 files to understand full auth chain.
Alternative: grep auth-related imports across all files (~20 token query).
→ Chose grep instead. Budget preserved.
```

### Full project scan budget
Full project scans have a separate, stricter budget: maximum 1 full scan per 10 turns. Any scan that touches more than 50% of files counts as "full". Track with:
```
[BUDGET:FULL_SCAN] count=1/10 — last_full=T12 — remaining=9
```

---

## 7. Context Memory

### Memory structure
```
[CONTEXT]
PROJECT: {name} — {tech stack summary}
ARCHITECTURE: {key architectural decisions}
COMPLETED_TASKS: ["task1", "task2", ...]
KNOWN_ISSUES: ["issue1: description", ...]
CONFIRMED: ["fact1: source", "fact2: source", ...]
ACTIVE_TASK: {current task}
```

### Memory usage rules
1. Always consult `[CONTEXT]` before any file read or codebase exploration
2. If the answer is in memory, use it — `[CONTEXT:MEM] {fact}`
3. Update memory after each completed task or confirmed finding
4. If memory conflicts with new evidence, update and note the change

### Example
```
User: "Check if we're using JWT for auth."
Agent: [CONTEXT:MEM] Auth method confirmed as JWT RS256 in earlier analysis.
  → Skipping file read. Answer: Yes, JWT RS256 with Vault keys.
```

---

## 8. Action-First

### Decision matrix
```
| Situation | Default Action |
|-----------|---------------|
| Need to know a function's signature | grep for def/function name |
| Need to understand a module | Read summary from cache, or grep key classes/functions |
| Need to find where X is used | grep for X across project |
| Need to make a code change | Make the change, don't re-read full context first |
| Need to understand a bug | Read only the buggy function + its immediate dependencies |
| Unsure about project structure | Check cache, then shallow ls, then task-specific reads only |
```

### Anti-patterns
- ❌ "Let me first read the entire project to understand it fully" → ✅ "Let me check the project structure from cache and grep for key patterns"
- ❌ "Let me analyze all possible approaches before deciding" → ✅ "Let me pick the simplest viable approach and implement it"
- ❌ "Let me re-read the conversation history for context" → ✅ "Let me check my [CONTEXT] block and [DECISION] summaries"

---

## 9. Cost Awareness

### Token estimation guide
| Operation | Estimated Tokens |
|-----------|-----------------|
| grep pattern across project | ~50-100 |
| Read single file < 50 lines | ~200-500 |
| Read single file 50-200 lines | ~500-2000 |
| Read single file 200+ lines | ~2000-5000+ |
| Read 10 files | ~5000-25000+ |
| Full project scan (50+ files) | ~25000-100000+ |
| Reasoning/analysis output | ~200-1000 per paragraph |

### Cost/Value decision tree
```
Operation needed
├─ Cost < 100 tokens → Just do it
├─ Cost 100-1000 → Do it, maybe grep first
├─ Cost 1000-5000 → Must have grep/cheaper alternative
└─ Cost > 5000 → Must have override + clear justification
```

### Always prefer
1. **grep** (0-50 tokens) for targeted queries
2. **Cached summaries** (0 tokens — already in context)
3. **Context memory** (0 tokens — already in context)
4. **Incremental reads** of only changed files
5. **Last resort**: Full file reads

---

## 10. Stop Conditions

### Decision tree
```
Continue?
├─ Is task objective achieved? → YES → [STOP]
├─ Is all required info already known? → YES → [STOP]
├─ Same conclusion 3+ times? → YES → [STOP, execute]
├─ Cost > value with no path forward? → YES → [STOP, report]
├─ Clear action to take? → YES → Execute
└─ Analysis needed but not looped? → Continue with budget check
```

### Examples
```
[SITUATION] User asked "Find the DB config file."
Agent reads config.py, finds DB settings.
→ [STOP] because task is done. Report findings.

[SITUATION] User asked "Is the project using React or Vue?"
Agent greps package.json, finds "react": "^18.0.0"
→ [STOP] because info is sufficient.

[SITUATION] User asked "Why is the test failing?"
Agent reads test file → needs to check implementation.
Reads implementation → already cached from earlier, hash unchanged.
→ [CACHE:HIT] No re-read needed. Use cached summary.
→ Info sufficient? Yes. [STOP] and report root cause.
```
