# The Filesystem

> **Previous:** [Users & Root](Users.md) | **Next:** [File Manipulation](Files.md)

The filesystem defines how data is organised, stored, and retrieved on a storage device. It is the logical structure that manages files and directories within a partition.

---

## Everything Is a File

Linux treats almost everything as a file:

- Regular documents and executables are files.
- Devices (USB drives, disks, network adapters) appear as files under `/dev`.
- Directories are a special type of file containing references to other files.
- If something isn't a file, it's a **process**.

This unified approach lets Linux manage hardware and software resources consistently through file operations.

---

## Tree Structure

The filesystem starts at the **root directory `/`**. All other directories branch out from it:

```
/
├── bin
├── etc
├── home
│   └── user
├── var
└── usr
```

> `~` is a shortcut for the current user's home directory (`/home/<username>`).

### "Folder" vs "Directory"

- **Directory** — the traditional UNIX/Linux term, used in the terminal.
- **Folder** — a GUI term referring to the same concept.

They are interchangeable in meaning.

---

## Filesystem Hierarchy Standard (FHS)

| Directory | Purpose                                                 |
| --------- | ------------------------------------------------------- |
| `/`       | Root — top of the hierarchy                             |
| `/bin`    | Essential user executables available to all users       |
| `/sbin`   | System/admin binaries (superuser)                       |
| `/boot`   | Bootloader files and the Linux kernel                   |
| `/home`   | Home directories for regular users                      |
| `/root`   | Home directory for root                                 |
| `/dev`    | Device files (hardware and peripherals)                 |
| `/etc`    | System-wide configuration files                         |
| `/lib`    | Shared libraries for essential binaries                 |
| `/lib64`  | 64-bit libraries (architecture-specific)                |
| `/media`  | Mount points for removable media (USB, external drives) |
| `/mnt`    | Temporary mount point for filesystems                   |
| `/tmp`    | Temporary files — often cleared on reboot               |
| `/proc`   | Virtual filesystem exposing process and kernel info     |
| `/sys`    | Virtual filesystem for kernel objects and hardware      |
| `/srv`    | Data served by system services (web, FTP, etc.)         |
| `/run`    | Runtime process data stored in RAM                      |
| `/usr`    | User applications, binaries, libraries, documentation   |
| `/var`    | Variable data — logs, caches, spool files               |

> Quick probe: `cat /proc/cpuinfo` shows detailed CPU information directly from the kernel.

---

## What to Read Next

| You want to...                       | Go here                       |
| ------------------------------------ | ----------------------------- |
| Create, view, copy, and delete files | [File Manipulation](Files.md) |
| Go back to users and permissions     | [Users & Root](Users.md)      |
