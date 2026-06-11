# Token Efficiency Skill

## What is this?

**Token Efficiency Skill** is an efficiency optimization toolkit for AI Agents.

When agents work on complex multi-step tasks, only 10%-20% of tokens are relevant to the current task. The remaining 80%-90% go to re-reading files, replaying history, and redundant analysis. This skill stops that waste.

## Problems Solved

Repeated file reads, growing conversation history, full project re-scans, endless analysis of resolved issues, overkill full reads for simple queries, and continuing after task completion - all solved.

## Compatible Agents

All LLM-based agents supporting Skill/Plugin mechanisms: **Codex** (primary), **Claude**, **Cursor**, **Windsurf**, **Cline**, and any agent that loads Markdown instruction files.

## 10 Core Capabilities

1. History Compression - Summarize instead of re-reading.
2. File Cache - Track hash + summary, skip unchanged files.
3. Incremental Analysis - Only new/changed/task-relevant files.
4. Context Pruning - Drop completed tasks and stale discussions.
5. Loop Prevention - Stop after 3 identical conclusions.
6. Read Budget - 10 files/5000 lines/50 KB per turn.
7. Context Memory - Remember project structure and known facts.
8. Action-First - Execute > search > cache > summary > full read.
9. Cost Awareness - Estimate before large operations, auto-downgrade.
10. Stop Conditions - Stop when done, sufficient, or too costly.

## Core Principle

Every token must create value. No repeated reads, reasoning, summaries, or scans. Priority: Cache -> Summary -> Incremental -> Execute.

## Installation

### Git Clone
```
git clone https://github.com/cheche089/token-efficiency-skill.git
```

macOS / Linux:
```
cp -r token-efficiency-skill ~/.codex/skills/token-efficiency
```

Windows (PowerShell):
```
Copy-Item -Path ".\token-efficiency-skill\" -Destination "$env:USERPROFILE\.codex\skills\token-efficiency" -Recurse -Force
```

### Manual Download
Visit GitHub repo -> Code -> Download ZIP -> Extract and copy to Skills directory.

### Verify Installation
```
~/.codex/skills/token-efficiency/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/
```

## Usage

Reference in prompt: $token-efficiency Analyze this project.

Or auto-triggers for long-running tasks.

## File Structure

```
token-efficiency/
  SKILL.md              - Core protocol
  README.md             - This file
  agents/openai.yaml    - Metadata
  references/           - 3 reference files
  scripts/              - 3 helper scripts
```
