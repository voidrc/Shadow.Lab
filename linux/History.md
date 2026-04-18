# Command History

> **Previous:** [The Terminal & Shell](CLI.md) | **Next:** [Users & Root](Users.md)

Every command you type is saved in a history file (`~/.bash_history` or `~/.zsh_history`). Knowing how to use it saves time and aids auditing.

---

## Core Commands

| Command      | Action                                              |
| ------------ | --------------------------------------------------- |
| `history`    | List all recorded commands with their numbers       |
| `!<number>`  | Re-run command by its history number                |
| `!-2`        | Re-run the second-most-recent command               |
| `!grep`      | Re-run the most recent command starting with `grep` |
| `!grep:p`    | Print that command without running it               |
| `history -c` | Clear the entire history for this session           |

---

## Search History

| Shortcut   | Action                                                           |
| ---------- | ---------------------------------------------------------------- |
| `CTRL + R` | Reverse incremental search — start typing to find a past command |
| `CTRL + G` | Exit search mode without running anything                        |

---

## Controlling What Gets Saved

Prefix a command with a **space** to stop it from being recorded:

```bash
 secret-command --password=hunter2
```

This behavior is controlled by `HISTCONTROL`:

| Value         | Effect                              |
| ------------- | ----------------------------------- |
| `ignorespace` | Skip commands prefixed with a space |
| `ignoredups`  | Skip consecutive duplicate commands |
| `ignoreboth`  | Both of the above                   |

Set it in your shell config (e.g. `~/.zshrc` or `~/.bashrc`):

```bash
HISTCONTROL=ignoreboth
```

---

## Timestamps

Add timestamps to every history entry so you can audit when commands were run:

```bash
HISTTIMEFORMAT="%d/%m/%Y %T "
```

Example output:

```
120  22/10/2025 11:04:12 ls -la
121  22/10/2025 11:05:01 ranger
```

Add this to your shell config to persist it.

---

## What to Read Next

| You want to...            | Go here                        |
| ------------------------- | ------------------------------ |
| Understand users and sudo | [Users & Root](Users.md)       |
| Go back to command basics | [The Terminal & Shell](CLI.md) |
