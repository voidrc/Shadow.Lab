# Users & Root

> **Previous:** [Command History](History.md) | **Next:** [The Filesystem](Filesystem.md)

Linux has two categories of users: **root** (superuser) and **normal users**. Knowing the difference is essential for permissions, security, and daily operations.

---

## User Types at a Glance

| User Type       | Home Directory     | UID    | Privileges             | Common Groups                |
| --------------- | ------------------ | ------ | ---------------------- | ---------------------------- |
| **root**        | `/root`            | `0`    | Full, unrestricted     | `root`, `wheel`, `sudo`      |
| **Normal user** | `/home/<username>` | ≥ 1000 | Limited to owned files | `users`, `sudo` (if granted) |

> Root is powerful but risky — a single mistake can break the system. Operate as a normal user for daily tasks and only escalate when necessary.

---

## Root User

The root account has unrestricted access to all commands, files, and settings. It can modify system configuration, install or remove software, and manage other users.

- **Username:** `root`
- **Home:** `/root`
- **UID:** `0`

### Root Access Groups

Different distributions use different group names for granting sudo access:

| Group   | Used on                    |
| ------- | -------------------------- |
| `sudo`  | Ubuntu, Debian             |
| `wheel` | Fedora, CentOS, RHEL, Arch |

Users added to one of these groups can run administrative commands via `sudo`.

---

## `sudo` — Temporary Elevation

`sudo` (superuser do) runs a single command with elevated privileges without switching fully to the root account. Every action is logged.

```bash
sudo apt update
sudo systemctl restart sshd
```

Configuration lives in `/etc/sudoers`. Always edit it with `visudo` — it validates syntax before saving:

```bash
sudo visudo
```

---

## Switching Users

| Command                        | What it does                      |
| ------------------------------ | --------------------------------- |
| `su -`                         | Switch to root (full login shell) |
| `su <username>`                | Switch to another user            |
| `sudo -u <username> <command>` | Run one command as another user   |
| `whoami`                       | Print the current user            |

The `-` in `su -` loads the target user's full environment (profile, PATH, etc.). Without it you keep the calling user's environment.

---

## What to Read Next

| You want to...                                      | Go here                         |
| --------------------------------------------------- | ------------------------------- |
| Understand how files and directories are structured | [The Filesystem](Filesystem.md) |
| Go back to history commands                         | [Command History](History.md)   |
