---
name: git-workflow
description: 'Git add, commit and push workflow for BuscaMedicos. Streamlined commands with CI env vars for non-interactive Git operations.'
license: MIT
---

# Git Workflow Skill

## Overview

Streamlined git workflow for committing and pushing changes. Uses CI-friendly environment variables to avoid interactive prompts.

## When to Use

Use this skill when:
- Making commits in CI/CD environments
- Avoiding interactive Git prompts (merge conflicts, editor, etc.)
- Quick commit + push cycle

## Quick Commands

### Check Status
```bash
git status
```

### Add All Changes
```bash
git add <files>           # Add specific files
git add .                # Add all changes
git add -A               # Add everything including untracked
```

### Commit
```bash
git commit -m "your message"
```

### Push
```bash
git push
```

## CI-Friendly Environment Variables

Add these before git commands to avoid interactive prompts:

```bash
export CI=true
export GIT_TERMINAL_PROMPT=0
export GIT_EDITOR=':'
export GIT_SEQUENCE_EDITOR=':'
export GIT_MERGE_AUTOEDIT=no
export GIT_PAGER=cat
export PAGER=cat
```

## Complete Workflow

```bash
# 1. Check what changed
git status

# 2. Stage specific files
git add path/to/file1 path/to/file2

# 3. Commit with message
git commit -m "feat: add new feature"

# 4. Push
git push
```

## Common Patterns

### Stage and Commit in One Line
```bash
git add <files> && git commit -m "message"
```

### Amend Last Commit (if not pushed)
```bash
git commit --amend -m "new message"
```

### Force Push (use carefully)
```bash
git push --force-with-lease
```

## Gotchas

- **Windows**: Git Bash handles env vars differently - use `$env:VAR='value'` format
- **Never force push main/master**: Always warn user if they request it
- **Check `git status` first**: Before adding, see what's changed
- **Large files**: Add `.gitignore` patterns or use Git LFS for files > 50MB

## Typical Commit Message Format

```
<type>: <short description>

- <change 1>
- <change 2>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat: add user authentication endpoints

- Add login endpoint
- Add register endpoint
- Add JWT token validation
```
