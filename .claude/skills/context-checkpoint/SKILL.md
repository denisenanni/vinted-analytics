---
name: context-checkpoint
description: Strategic context window management to prevent information loss. Use when context usage approaches 60-70%, before auto-compact triggers at 95%. Creates structured checkpoints that capture session state, decisions, and next steps for seamless session handoffs. Triggers on phrases like "checkpoint", "save context", "preserve state", "before compact", "session handoff".
---

# Context Checkpoint Skill

This skill enables strategic context management to preserve critical information before auto-compact triggers.

## Why This Matters

- Auto-compact triggers at ~95% context usage (25% remaining)
- Auto-compact is automatic and non-optimal—you don't control what's preserved
- Manual checkpointing at 60-70% gives you control over what's preserved
- Proper checkpoints enable seamless session continuation

## Checkpoint Strategy

### When to Checkpoint

1. **Proactive (Recommended)**: At 60-70% context usage
2. **Logical Breakpoints**: Feature complete, tests passing, PR ready
3. **Before Complex Tasks**: Large refactors, multi-file operations
4. **Session End**: Before stopping work for the day

### How to Check Context Usage

```bash
# In Claude Code, run:
/context
```

This shows current context usage percentage.

## Creating a Checkpoint

### Step 1: Create Checkpoint Directory

```bash
mkdir -p .claude/checkpoints
```

### Step 2: Generate Checkpoint

Create a file at `.claude/checkpoints/[TIMESTAMP].md`:

```markdown
# Checkpoint: [Date Time]

## Session Summary
[2-3 sentences describing what was accomplished]

## Work State

### ✅ Completed
- [Completed item 1]
- [Completed item 2]

### 🔄 In Progress
- [Current task with specific details]
- [Relevant file: path/to/file.ts:line]

### 📋 Next Steps
1. [Priority 1 - specific action]
2. [Priority 2 - specific action]
3. [Priority 3 - specific action]

## Key Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| [What] | [Why] | [Files affected] |

## Technical Context

### Modified Files
| File | Change Type | Notes |
|------|-------------|-------|
| path/to/file | Added/Modified/Refactored | [Brief description] |

### Important Discoveries
- [Non-obvious solution or pattern found]
- [Gotcha or edge case discovered]

### Blockers/Issues
- [Unresolved problem 1]
- [Question that needs answering]

## Resume Commands

```bash
# Quick context restoration
git status
git diff --stat

# Key files to read
cat path/to/important/file.ts
```

## Notes for Future Self
[Anything that would help resume this work]
```

### Step 3: Verify Checkpoint

After creating:
1. Read the checkpoint to confirm completeness
2. Ensure someone with no context could continue from it

## Restoring from Checkpoint

### After /clear or New Session

1. Find the latest checkpoint:
   ```bash
   ls -la .claude/checkpoints/
   ```

2. Read the checkpoint:
   ```bash
   cat .claude/checkpoints/[latest].md
   ```

3. Follow the "Resume Commands" section

4. Read the files mentioned in "Modified Files"

5. Continue from "Next Steps"

## Alternative: Document & Clear Method

For complex tasks, use the "Document & Clear" pattern:

1. **Document**: Ask Claude to dump its plan and progress to a `.md` file
2. **Clear**: Run `/clear` to reset context
3. **Resume**: Start new session by reading the `.md` file

This gives more control than `/compact` for complex work.

## Best Practices

- Checkpoint at logical breakpoints, not arbitrary moments
- Keep checkpoints concise but complete
- Include specific file paths and line numbers
- Note environment-specific issues
- Don't checkpoint trivial or obvious information
- Version control checkpoints for team sharing (optional)