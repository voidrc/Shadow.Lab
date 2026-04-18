# 🛠️ Tools & Setup

> Build your offensive and defensive security environment.

---

## Reading Order

| #   | Guide                                                          | What it covers                 |
| --- | -------------------------------------------------------------- | ------------------------------ |
| 1   | [Lab Environment Setup](README.md) ← you are here              | Pick an OS, set up a VM        |
| 2   | [VirtualBox on Arch](VirtualBox_Arch.md) / [QEMU/KVM](Qemu.md) | Hypervisor setup on Arch       |
| 3   | [VM Quality of Life](QOL-VM.md)                                | Tune your VM                   |
| 4   | [Starter Tools](Starter-Tools.md)                              | Install core tools             |
| 5   | [General Security Tools](GeneralSecurity-Tools.md)             | Full tool reference            |
| 6   | [Red Team Tools](RedTeam-Tools.md)                             | Offensive tooling              |
| 6   | [Blue Team Tools](BlueTeam-Tools.md)                           | Defensive tooling              |
| 7   | [Docker Setup](Docker.md)                                      | Run lab services in containers |
| 8   | [Arch Quality of Life](Arch-QOL.md)                            | Tune your Arch host            |
| 9   | [GPG](GPG.md)                                                  | Encrypt files and keys         |
| 10  | [Backups](BackUps.md)                                          | Protect your work              |

---

## 🖥️ Lab Environment Setup

> **New here?** Don't worry — this section walks you through everything step by step. No experience needed.

When learning security, you don't want to practice on your real computer. Instead, you set up a **virtual machine (VM)** — think of it as a computer inside your computer. You can break it, reset it, or delete it without touching your actual system.

---

### Step 1 — Pick an Operating System

Security tools mostly run on **Linux**. You don't need to install Linux on your real machine — you'll run it inside a VM (explained in Step 2).

**If you're a complete beginner → start with Kali Linux.** It comes with everything preinstalled.

| OS                                                    | Best for                                                            | Download       |
| ----------------------------------------------------- | ------------------------------------------------------------------- | -------------- |
| [Kali Linux](https://www.kali.org)                    | Beginners — 600+ security tools preinstalled, tons of guides online | ISO / VM image |
| [Parrot OS](https://parrotsec.org)                    | Beginners who want something lighter than Kali                      | ISO / VM image |
| [BlackArch](https://www.blackarch.org/downloads.html) | Experienced users — 3000+ tools, Arch-based                         | ISO / VM image |
| [Garuda Linux](https://garudalinux.org/)              | Arch users who want a nice desktop and can add BlackArch tools      | ISO            |
| [Arch Linux](https://archlinux.org/download/)         | Advanced users who want to build everything from scratch            | ISO / VM image |

---

### Step 2 — Set Up a Virtual Machine

A **virtual machine** lets you run a second operating system (like Kali Linux) as a window on your current computer. Your real system is never touched.

**Pick the VM software for your computer:**

| Software                                                                       | Your computer runs... | Cost            | Best for                                 |
| ------------------------------------------------------------------------------ | --------------------- | --------------- | ---------------------------------------- |
| [VirtualBox](https://www.virtualbox.org/)                                      | Windows, macOS, Linux | Free            | Beginners — easiest to get started       |
| [VMware Workstation Pro](https://www.vmware.com/products/workstation-pro.html) | Windows, Linux        | Free (personal) | Slightly faster than VirtualBox          |
| [VMware Fusion](https://www.vmware.com/products/fusion.html)                   | macOS                 | Free (personal) | Mac users on Intel chips                 |
| [Parallels Desktop](https://www.parallels.com/)                                | macOS                 | Paid            | Mac users on Apple Silicon (M1/M2/M3)    |
| [GNOME Boxes](https://apps.gnome.org/Boxes/)                                   | Linux                 | Free            | Linux users who want the simplest option |
| [Virt-Manager / KVM](https://virt-manager.org/)                                | Linux                 | Free            | Linux users who want maximum performance |

> **Not sure which to pick?** Use **VirtualBox** — it's free, runs on Windows/macOS/Linux, and has thousands of tutorials.

#### Installing VirtualBox

**On Windows:** Download the installer from [virtualbox.org](https://www.virtualbox.org/wiki/Downloads) and run it like any other program.

**On macOS:**

```bash
brew install --cask virtualbox
```

_(If you don't have Homebrew yet: [brew.sh](https://brew.sh))_

**On Ubuntu / Debian Linux:**

```bash
sudo apt update && sudo apt install -y virtualbox
```

**On Arch / Garuda / BlackArch:**

```bash
sudo pacman -S virtualbox virtualbox-host-modules-arch
```

#### Creating your first VM (Kali Linux example)

1. [Download the Kali Linux VirtualBox image](https://www.kali.org/get-kali/#kali-virtual-machines) — pick the **VirtualBox** version (`.ova` file).
2. Open VirtualBox → **File → Import Appliance** → select the `.ova` file → click Import.
3. Select the new VM and click **Start**.

That's it — Kali boots up in a window. Default login: `kali` / `kali`.

#### Recommended settings (adjust after importing)

Right-click your VM → **Settings:**

| Setting                        | What to set                    | Why                                     |
| ------------------------------ | ------------------------------ | --------------------------------------- |
| System → Memory                | 4096 MB (4 GB) or more         | Less than 4 GB and tools will be slow   |
| System → Processors            | 2 CPUs                         | Keeps things responsive                 |
| Storage → Disk                 | 60 GB+ (dynamically allocated) | Tools take up space quickly             |
| Network → Adapter 1            | NAT                            | Gives the VM internet access            |
| General → Advanced → Clipboard | Bidirectional                  | Lets you copy/paste between VM and host |

#### Snapshots — your "undo" button

Before you install tools or start experimenting, take a snapshot. If anything goes wrong, you can roll back instantly.

In VirtualBox: **Machine → Take Snapshot** → name it `clean-base`.

To restore: **Machine → Restore Snapshot → clean-base**.

---

### Step 3 — Bare-Metal Install (Optional)

If you want to install Linux directly on a physical computer instead of a VM:

1. Download the ISO for your chosen OS.
2. Flash it to a USB drive using [Balena Etcher](https://etcher.balena.io/) — just pick the ISO and your USB stick, click Flash.
3. Reboot the computer, boot from USB (usually press F12 or F2 at startup), and follow the on-screen installer.
4. After installation, open a terminal and run:

```bash
sudo apt update && sudo apt full-upgrade -y && sudo reboot
```

This updates all software before you start.

---

## What to Read Next

| You want to...                 | Go here                                  |
| ------------------------------ | ---------------------------------------- |
| Set up VirtualBox on Arch      | [VirtualBox on Arch](VirtualBox_Arch.md) |
| Use KVM for better performance | [QEMU/KVM Setup](Qemu.md)                |
| Tune your VM after setup       | [VM Quality of Life](QOL-VM.md)          |
| Install your first tools       | [Starter Tools](Starter-Tools.md)        |
