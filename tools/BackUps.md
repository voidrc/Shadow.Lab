# Backups

A resilient operator maintains at least two backup layers. Working with exploits, unstable tools, and live payloads makes system breakage inevitable — a proper backup strategy enables fast rollback and recovery.

---

## Approaches

| Method            | Tools                          | Best For                    |
| ----------------- | ------------------------------ | --------------------------- |
| Snapshots         | Snapper, Timeshift, ZFS        | Instant OS rollbacks        |
| Encrypted backups | BorgBackup, Restic, Duplicity  | Long-term secure storage    |
| GUI helpers       | Pika-Backup, KBackup, Déjà Dup | Beginner-friendly workflows |
| Cloud / sync      | Syncthing, Nextcloud, Rclone   | Multi-device resilience     |
| Disk imaging      | Clonezilla, Rescuezilla, dd    | Full forensic clones        |

---

## Snapshot-Based

Freeze OS state; roll back instantly when an experiment breaks the system.

### Snapper

- Snapshot manager for btrfs/LVM.
- Integrates with GRUB — bootable into older snapshots.
- Automatic pre/post hooks for `pacman -Syu`.
- Requires btrfs or LVM.

### Timeshift

- System snapshot tool (rsync or btrfs mode).
- Simple UI with scheduled snapshots.
- Focuses on system files only, not home directory.
- Beginner-friendly; good for post-update rollbacks.

### ZFS Auto-Snapshot

- Automated snapshots for ZFS pools.
- Built-in compression and strong resilience.
- Higher RAM usage; licensing complications on Linux.
- Best suited for servers or large storage arrays.

---

## Encrypted Backup Tools

Long-term, portable, and secure backups.

### BorgBackup

- Deduplicating, compressing, and encrypting backup tool.
- Strong encryption; highly space-efficient.
- Proven in production environments.
- CLI-heavy; recommended for ops laptops backing up to encrypted drives or a VPS.

### Restic

- Modern backup tool; simpler configuration than Borg.
- Fast restores; supports cloud backends (S3, GDrive, and others).
- Deduplication is less aggressive than Borg.
- Good for personal cloud backups with minimal setup.

### Duplicity

- Incremental encrypted backups using rsync and GPG.
- Strong encryption via GPG keys.
- Slower than Borg or Restic.
- Suitable if GPG is already a core part of your workflow.

---

## GUI-Based

Accessible interfaces for common backup workflows.

### Pika-Backup

- GNOME application wrapping BorgBackup.
- Provides Borg’s power without the CLI.
- Best for daily home-folder and documents backups.

### KBackup

- KDE-native backup tool.
- Simple folder backups; less capable than Borg or Restic.
- Suited for KDE users needing quick config backups.

### Déjà Dup

- GNOME frontend for Duplicity.
- Very beginner-friendly; one-click cloud backup.
- Limited configuration; slower than alternatives.

---

## Cloud / Sync

Keep files mirrored across devices.

### Syncthing

- Peer-to-peer file synchronisation; no central server.
- End-to-end encrypted.
- Not a true backup — accidental deletions propagate to all peers.
- Best for syncing notes and scripts between a laptop and VPS.

### Nextcloud

- Self-hosted cloud storage (Dropbox alternative).
- Full ecosystem: calendar, contacts, web and mobile clients.
- Requires a server; heavier setup.
- Suited for private cloud storage and team collaboration.

### Rclone

- CLI tool for syncing to cloud providers.
- Supports nearly every backend (S3, GDrive, Mega, and others).
- Advanced users syncing encrypted repositories to cloud storage.

---

## Forensic / Full-Disk Imaging

Last-resort recovery: clone an entire disk bit by bit.

### Clonezilla

- Partition and disk imaging tool.
- Reliable and fast; not incremental.
- Used for creating a golden OS image before hacking labs.

### Rescuezilla

- Clonezilla with a graphical interface.
- Easier and safer for infrequent use.
- Slightly slower than CLI Clonezilla.

### dd

- Raw block-level copy tool built into Linux.
- Extreme power: one incorrect argument can wipe the entire target disk.
- Reserved for forensic imaging by experienced operators.

---

## Notes

- Combine at least two layers (e.g., snapshots + encrypted backup).
- Test restores regularly — an untested backup is not a backup.
- Store encrypted backup keys separately from the backup itself.

---

## Related Guides

|                      | Guide                               |
| -------------------- | ----------------------------------- |
| Encrypt your backups | [GPG](GPG.md)                       |
| Back to host setup   | [Arch Quality of Life](Arch-QOL.md) |
