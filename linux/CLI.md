# The Terminal & Shell

> **Next:** [Command History](History.md)

You'll hear words like **terminal, console, shell, command** thrown around constantly. To beginners it sounds spooky — the real power lives here. GUIs are fine for comfort, but true control belongs to the CLI.

| Term         | What it means                                                                            |
| ------------ | ---------------------------------------------------------------------------------------- |
| **Terminal** | The app you open to type commands — your window into the system                          |
| **Shell**    | Lives inside the terminal; takes your commands and tells the kernel what to do           |
| **Console**  | Old-school term for a direct system interface — often used interchangeably with terminal |
| **GUI**      | Graphical user interface — point, click, drag                                            |
| **CLI**      | Command line interface — type commands, automate, script                                 |

Common shells: `bash`, `zsh`, `fish`.

---

## Command Structure

```
{command} -option [argument]
```

| Concept                                     | Example         |
| ------------------------------------------- | --------------- |
| Short option                                | `ls -l`         |
| Long option                                 | `tar --verbose` |
| Combine short options                       | `ls -alh`       |
| Short + long together                       | `ls -a --color` |
| Some commands accept argument before option | `grep file -i`  |

---

## Getting Help

### `man` — full manual

```bash
man ls
```

Inside the manual: press `h` for navigation help, `q` to quit.

### `tldr` — practical examples

```bash
tldr tar
```

Community-maintained; shows real-world usage instead of exhaustive reference.

### `--help` — quick summary

```bash
grep --help
```

Most commands support this flag.

### `help` — shell built-ins

```bash
help cd
```

Use `type <command>` to check whether a command is a shell built-in or an external program:

```bash
type echo
type ls
```

---

## Keyboard Shortcuts

| Shortcut     | Action                              |
| ------------ | ----------------------------------- |
| `CTRL + L`   | Clear the screen                    |
| `CTRL + D`   | Exit the current shell session      |
| `CTRL + C`   | Terminate the running command       |
| `CTRL + Z`   | Pause (suspend) the current process |
| `CTRL + A`   | Move cursor to start of line        |
| `CTRL + E`   | Move cursor to end of line          |
| `CTRL + U`   | Clear the current command line      |
| `UP Arrow`   | Recall previous command             |
| `DOWN Arrow` | Navigate to newer command           |

---

## What to Read Next

| You want to...                   | Go here                       |
| -------------------------------- | ----------------------------- |
| Recall and search past commands  | [Command History](History.md) |
| Understand users and permissions | [Users & Root](Users.md)      |
