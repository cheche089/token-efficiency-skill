# Stop Conditions — Decision Guide

Detailed rules for when to stop analyzing and when to stop entirely.

---

## Stop Condition Levels

### Level 1: Task Complete (Hard Stop)
```
[STOP] Task objective achieved: {description}
```
The task is done. All criteria met. No additional context needed.

**Examples:**
- User asked "Change the port from 3000 to 4000" → change made → [STOP]
- User asked "Find the config file" → location reported → [STOP]
- User asked "What ORM is this project using" → answer found → [STOP]

### Level 2: Information Sufficient (Soft Stop)
```
[STOP] Info sufficient: {what was needed} → {what was found}
```
You have enough information to proceed, even if you could theoretically learn more.

**Examples:**
- Found `DATABASE_URL=postgresql://...` in `.env` → don't need to read the full config parser too
- Found `from fastapi import APIRouter` → don't need to verify it's not Flask elsewhere just to answer this question
- Found a `react` dependency in package.json → don't need to scan every component file for JSX

**Rule of thumb:** If the answer is unambiguous and the source is authoritative, stop. Only continue if findings are contradictory or incomplete.

### Level 3: Loop Detected (Forced Stop)
```
[STOP] Loop detected: {topic} — same conclusion {N} rounds
```
After 3 consecutive turns with the same finding, stop analyzing and execute.

**Examples:**
- 3 turns analyzing the same function signature → implement it
- 3 turns re-reading the same error trace → fix it based on what you know
- 3 turns discussing the same architecture question → pick the first viable option

### Level 4: Cost Exceeds Value
```
[STOP] Cost exceeds value: {estimated_cost} > {expected_value}
```
When the token cost of continued investigation exceeds the expected benefit.

**Examples:**
- 20000 tokens to understand a module when you only need one function → stop, grep for the function
- Full project scan to find a config value → stop, grep for the config key
- Reading 10 files to understand one integration → stop, read only the integration point

---

## Before-Action Stop Check

Before any significant action, ask:

1. **Is the task already done?** Files modified? Answer given? Objective met?
2. **Do I already have the information?** In cache? In memory? In compressed summaries?
3. **Have I been going in circles?** Same files? Same conclusions? Same dead ends?
4. **Is this next read worth its tokens?** What will I learn? Do I need it?
5. **What is the minimum I need to proceed?** One grep? One cache lookup? One summary?

If you can answer YES to "can proceed" at any point, stop. Do not do more work.

---

## Common Anti-Patterns

**"Just one more read" syndrome:**
- "Let me also check the test file to be sure..." → Already confirmed the answer in the source
- "Let me read the whole module for context..." → The function signature is sufficient
- "Let me see what changed in git log..." → Not relevant to the current task

**"Perfect understanding" fallacy:**
- "I need to understand every dependency..." → Not unless the task requires it
- "Let me trace through every code path..." → Only if debugging a specific issue
- "Let me read the whole spec first..." → Start with the minimum viable understanding

**"Safety" over-analysis:**
- "Let me double-check by reading it again..." → Check cache, hash hasn't changed
- "Let me verify by scanning similar files..." → The answer was clear from the first source
- "Let me re-read the conversation to make sure..." → Use [CONTEXT] and compressed summaries

---

## Stop Condition Quick Reference

| Situation | Stop? | Action |
|-----------|-------|--------|
| Code change made, diff looks correct | YES | Report, [STOP] |
| Found the answer to a direct question | YES | Report, [STOP] |
| Same grep result 3 times | YES | Stop analyzing, use result |
| File read would cost >1000 tokens for a trivial answer | YES | Grep instead, [STOP] search |
| User asks a question about the project | After finding answer | [STOP] |
| User asks "what would happen if X" | After analysis + answer | [STOP] |
| User asks to make a change | After change is implemented | [STOP] |
| User asks to "analyze the whole codebase" | After one scan cached | Restrict to task scope |
