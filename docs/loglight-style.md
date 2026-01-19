# LogLight Script Logging Style

## What is LogLight?

LogLight is a simple way to make script logs clear and easy to read. Use it for short scripts that run once or a few times.

## Core Rules

### Use these markers only:

**Boundary markers** (show start and end of sections)
- Start: `[=] Section Name Start`
- End: `[=] Section Name Complete`
- Always use in pairs

**Process markers** (show normal steps)
- Format: `[-] Action description`
- Use verb phrases

**Interaction markers** (show ongoing work)
- Format: `[*] Doing something...`
- Add `...` when waiting or working
- Can show simple counts: `[*] Processing file 5 of 10`

**Status markers** (show results)

*Discovery marker*
- Format: `[+] Found something`
- Shows positive finds or created items

*Error marker*
- Format: `[!] Error details`
- Use for critical problems
- Script may stop after this

*Warning marker*
- Format: `[?] Warning details`
- Use for non-critical issues
- Script continues after this

## Structure Rules

### Nesting order
1. Boundary markers first
2. Process markers second
3. Interaction markers third
4. Status markers last

### Depth limit
- Maximum 3 levels of nesting
- Use 2 spaces for each level

### Content rules
- Keep messages short (under 60 characters when possible)
- Be specific (include exact numbers, names, or sizes)
- Use clear words, not clever words
- Show actions with verbs, show sections with nouns

## Format Rules

### Visual design
- Use blank lines between major sections
- No blank lines between related steps
- Keep same formatting through whole script
- Use only basic ASCII symbols

### Pairing rules
- Every `[=] Start` must have matching `[=] Complete`
- Start and end names should match

## Example

```bash
#!/bin/bash

[=] System Cleanup Start

[-] Find temporary files
[*] Scanning /tmp...
[+] Found 150 files (1.5 GB)
[?] Note: 2 files are in use

[-] Remove old files
[*] Deleting files...
[!] Error: Cannot delete /tmp/lock.pid
[+] Removed 148 files

[=] System Cleanup Complete
[+] Result: 148 files removed, 1.5 GB free
```

## When to Use

### Good for:
- One-time scripts
- Quick automation
- Test runners
- Setup scripts
- Diagnostic tools

### Not for:
- Long-running services
- Production systems
- High-frequency logging
- Machine-parsed logs
- Audit logs

## Check Before Finish

Before final script, check:

- [ ] All `[=]` markers have pairs
- [ ] `[-]` markers describe actions
- [ ] `[*]` markers show ongoing work
- [ ] Status markers report results, not processes
- [ ] Messages are short and clear
- [ ] No more than 3 nesting levels
- [ ] Output tells clear story

## Common Mistakes to Avoid

1. **Too much nesting** - Keep it simple
2. **Wrong markers** - Use `[!]` only for errors, `[?]` for warnings
3. **Too many words** - Keep messages brief
4. **Different formats** - Use same style everywhere
5. **Missing ends** - Always close `[=]` sections

## Simple Design Principles

### One job, one marker
Each marker type does one clear job.

### Works with pipes
Output works with standard tools like `grep`.

### Clear to see
Script flow is easy to follow.

### Simple to use
No setup needed, just start writing.

### No surprises
Markers work as expected.

## Remember

LogLight helps people understand:
- What is happening now
- What comes next
- What matters most

Each line should help the user follow the script's work.

---

*LogLight v1.0 | Made for clear logs in short scripts*
