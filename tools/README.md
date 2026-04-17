# 🛠️ Tools & Setup

> Build your offensive and defensive security environment.

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

### Step 4 — Install Starter Tools

Once you're inside your Linux VM, open the **Terminal** (search for it in the app menu) and run these commands one section at a time.

> **What is the terminal?** It's a text-based window where you type commands. Don't be intimidated — you're just telling the computer what to install.

> **What is `sudo`?** It means "run this as administrator". Linux will ask for your password the first time.

#### System essentials — core tools every developer and security person needs

```bash
sudo apt install -y \
  git curl wget vim neovim tmux \
  build-essential gcc g++ make cmake \
  python3 python3-pip python3-venv \
  net-tools dnsutils ncat socat \
  unzip p7zip-full jq tree htop \
  golang-go ruby-full default-jdk
```

Copy the whole block, paste it into the terminal, hit Enter, and wait. It will install everything automatically.

#### VS Code — a beginner-friendly text/code editor

```bash
# Download and install
wget -qO /tmp/vscode.deb "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
sudo dpkg -i /tmp/vscode.deb
sudo apt install -f -y

# Install useful extensions
code --install-extension ms-vscode.hexeditor
code --install-extension ms-python.python
code --install-extension redhat.vscode-yaml
code --install-extension streetsidesoftware.code-spell-checker
```

#### Git — saves and tracks your work

Git is how developers save their code and share it. Think of it like "save history" for your files.

```bash
# Replace with your actual name and email
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global core.editor "vim"
git config --global init.defaultBranch main

# Create an SSH key — this is your ID card for GitHub/GitLab
ssh-keygen -t ed25519 -C "you@example.com"
# Press Enter through all prompts to accept defaults

# Show your public key — copy this and add it to GitHub → Settings → SSH Keys
cat ~/.ssh/id_ed25519.pub
```

#### Python — needed for most security tools

```bash
pip install --upgrade pip
pip install pwntools requests beautifulsoup4 scapy impacket
```

#### Go — needed for some tools (subfinder, ffuf, nuclei, etc.)

```bash
# Make Go tools available in your terminal (add this to your shell config)
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.zshrc
source ~/.zshrc
```

---

## 🔴 Red Team Tools

### Reconnaissance & OSINT

| Tool           | Purpose                           | Install                                                                    |
| -------------- | --------------------------------- | -------------------------------------------------------------------------- |
| `nmap`         | Network port scanner              | `apt install nmap`                                                         |
| `masscan`      | Fast mass port scanner            | `apt install masscan`                                                      |
| `subfinder`    | Passive subdomain enumeration     | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| `amass`        | Subdomain enumeration and mapping | `apt install amass`                                                        |
| `theHarvester` | Email/domain OSINT                | `apt install theharvester`                                                 |
| `sherlock`     | Username search across platforms  | `pip install sherlock-project`                                             |

### Web Exploitation

| Tool           | Purpose                              | Install                                                              |
| -------------- | ------------------------------------ | -------------------------------------------------------------------- |
| Burp Suite Pro | HTTP proxy, scanner, intruder        | [portswigger.net](https://portswigger.net/burp/pro)                  |
| `ffuf`         | Web fuzzing                          | `go install github.com/ffuf/ffuf/v2@latest`                          |
| `sqlmap`       | SQL injection automation             | `apt install sqlmap`                                                 |
| `nuclei`       | Template-based vulnerability scanner | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| `nikto`        | Web vulnerability scanner            | `apt install nikto`                                                  |

### Active Directory & Network Attacks

| Tool                | Purpose                                         | Install                                              |
| ------------------- | ----------------------------------------------- | ---------------------------------------------------- |
| `impacket`          | AD/SMB attack suite (psexec, secretsdump, etc.) | `pip install impacket`                               |
| `bloodhound-python` | BloodHound data collection                      | `pip install bloodhound`                             |
| BloodHound          | AD attack path visualisation                    | [GitHub](https://github.com/BloodHoundAD/BloodHound) |
| `evil-winrm`        | WinRM shell                                     | `gem install evil-winrm`                             |
| `responder`         | LLMNR/NBT-NS poisoning                          | `apt install responder`                              |
| `crackmapexec`      | AD Swiss-army knife                             | `apt install crackmapexec`                           |
| `kerbrute`          | Kerberos user enumeration and bruteforce        | [GitHub](https://github.com/ropnop/kerbrute)         |

### Post-Exploitation & C2

| Tool                                          | Purpose                                      | Install                                          |
| --------------------------------------------- | -------------------------------------------- | ------------------------------------------------ |
| Metasploit                                    | Exploitation and post-exploitation framework | `apt install metasploit-framework`               |
| [Sliver](https://github.com/BishopFox/sliver) | Open-source C2 framework                     | GitHub releases                                  |
| `msfvenom`                                    | Payload generation                           | bundled with Metasploit                          |
| `chisel`                                      | TCP/UDP tunnel over HTTP                     | `go install github.com/jpillora/chisel@latest`   |
| `ligolo-ng`                                   | Tunneling for pivoting                       | [GitHub](https://github.com/nicocha30/ligolo-ng) |

### Privilege Escalation

| Tool       | Purpose                                  | Install                                           |
| ---------- | ---------------------------------------- | ------------------------------------------------- |
| `linpeas`  | Linux privilege escalation enumeration   | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `winpeas`  | Windows privilege escalation enumeration | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `mimikatz` | Windows credential dumping               | [GitHub](https://github.com/gentilkiwi/mimikatz)  |
| `Rubeus`   | Kerberos manipulation                    | [GitHub](https://github.com/GhostPack/Rubeus)     |

---

## 🔵 Blue Team Tools

### SIEM & Log Analysis

| Tool                                                      | Purpose                                         | Install                                           |
| --------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| [Elastic Stack (ELK)](https://www.elastic.co)             | Log ingestion, search, and visualisation        | Docker / APT                                      |
| [Splunk Free](https://www.splunk.com/en_us/download.html) | SIEM with 500MB/day free tier                   | Installer                                         |
| [Wazuh](https://wazuh.com)                                | Open-source SIEM + HIDS                         | [Install guide](https://documentation.wazuh.com/) |
| `sigma`                                                   | Convert generic detection rules to SIEM queries | `pip install sigma-cli`                           |

### Endpoint Detection & Forensics

| Tool                                                                      | Purpose                                            | Install                                 |
| ------------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------- |
| [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) | Detailed Windows event logging                     | Windows                                 |
| [Velociraptor](https://github.com/Velocidex/velociraptor)                 | DFIR and endpoint monitoring                       | GitHub releases                         |
| [Volatility 3](https://github.com/volatilityfoundation/volatility3)       | Memory forensics                                   | `pip install volatility3`               |
| [Eric Zimmerman Tools](https://ericzimmerman.github.io)                   | Windows forensics utilities (PECmd, MFTECmd, etc.) | Windows                                 |
| `autopsy`                                                                 | Digital forensics GUI                              | [autopsy.com](https://www.autopsy.com/) |

### Network Monitoring & Analysis

| Tool                            | Purpose                              | Install                 |
| ------------------------------- | ------------------------------------ | ----------------------- |
| [Zeek (Bro)](https://zeek.org)  | Network traffic analysis and logging | `apt install zeek`      |
| [Suricata](https://suricata.io) | Network IDS/IPS                      | `apt install suricata`  |
| Wireshark / `tshark`            | PCAP analysis                        | `apt install wireshark` |
| `zeek-cut`                      | Zeek log field extractor             | bundled with Zeek       |

### Malware Analysis

| Tool                                               | Purpose                                 | Install                                 |
| -------------------------------------------------- | --------------------------------------- | --------------------------------------- |
| [REMnux](https://remnux.org)                       | Linux malware analysis distro           | VM download                             |
| [FlareVM](https://github.com/mandiant/flare-vm)    | Windows malware analysis toolkit        | Windows setup script                    |
| `FLOSS`                                            | Extract obfuscated strings from malware | `pip install flare-floss`               |
| `pestudio`                                         | PE file static analysis                 | [winitor.com](https://www.winitor.com/) |
| `YARA`                                             | Pattern-matching for malware detection  | `apt install yara`                      |
| [Any.run](https://app.any.run)                     | Interactive online sandbox              | Browser                                 |
| [Hybrid-Analysis](https://www.hybrid-analysis.com) | Automated online sandbox                | Browser                                 |

### Threat Intelligence

| Tool                                 | Purpose                       | Install                                                 |
| ------------------------------------ | ----------------------------- | ------------------------------------------------------- |
| [MISP](https://www.misp-project.org) | Threat intel sharing platform | [Install guide](https://www.misp-project.org/download/) |
| [OpenCTI](https://www.opencti.io)    | Threat intel management       | Docker                                                  |

---

## General Security Tools by Category

### General

| Tool              | Purpose                                  | Install                                                       |
| ----------------- | ---------------------------------------- | ------------------------------------------------------------- |
| `file`            | Identify file type                       | built-in                                                      |
| `strings`         | Extract printable strings from binary    | built-in                                                      |
| `xxd` / `hexdump` | Hex viewer                               | built-in                                                      |
| `binwalk`         | Firmware/archive analysis and extraction | `pip install binwalk`                                         |
| `exiftool`        | Read/write file metadata                 | `apt install libimage-exiftool-perl`                          |
| `foremost`        | File carving                             | `apt install foremost`                                        |
| `7z` / `unzip`    | Archive extraction                       | `apt install p7zip-full`                                      |
| CyberChef         | Browser-based encode/decode/transform    | [gchq.github.io/CyberChef](https://gchq.github.io/CyberChef/) |

### Web

| Tool            | Purpose                            | Install                                         |
| --------------- | ---------------------------------- | ----------------------------------------------- |
| Burp Suite      | HTTP proxy & scanner               | [portswigger.net](https://portswigger.net/burp) |
| `curl` / `wget` | HTTP requests from CLI             | built-in                                        |
| `ffuf`          | Web fuzzing (dirs, params, vhosts) | `go install github.com/ffuf/ffuf/v2@latest`     |
| `gobuster`      | Directory/DNS brute-force          | `apt install gobuster`                          |
| `sqlmap`        | Automated SQL injection            | `apt install sqlmap`                            |
| `nikto`         | Web vulnerability scanner          | `apt install nikto`                             |
| Wappalyzer      | Technology fingerprinting          | browser extension                               |

### Cryptography

| Tool         | Purpose                                 | Install                                            |
| ------------ | --------------------------------------- | -------------------------------------------------- |
| `openssl`    | Swiss-army crypto tool                  | built-in                                           |
| `hashcat`    | GPU password cracking                   | `apt install hashcat`                              |
| `john`       | CPU password cracking (John the Ripper) | `apt install john`                                 |
| SageMath     | Math-heavy crypto scripting             | [sagemath.org](https://www.sagemath.org/)          |
| CyberChef    | Quick encode/decode                     | browser                                            |
| `RsaCtfTool` | RSA attack automation                   | [GitHub](https://github.com/RsaCtfTool/RsaCtfTool) |

### Forensics

| Tool                 | Purpose                           | Install                                                       |
| -------------------- | --------------------------------- | ------------------------------------------------------------- |
| Wireshark / `tshark` | PCAP analysis                     | `apt install wireshark`                                       |
| Volatility 3         | Memory forensics                  | [GitHub](https://github.com/volatilityfoundation/volatility3) |
| Autopsy              | Digital forensics GUI             | [autopsy.com](https://www.autopsy.com/)                       |
| `scalpel`            | File carving                      | `apt install scalpel`                                         |
| `NetworkMiner`       | Passive network sniffer/forensics | [netresec.com](https://www.netresec.com/)                     |

### Reverse Engineering

| Tool                | Purpose                        | Install                                                        |
| ------------------- | ------------------------------ | -------------------------------------------------------------- |
| Ghidra              | NSA decompiler (free)          | [ghidra-sre.org](https://ghidra-sre.org/)                      |
| IDA Free            | Industry-standard disassembler | [hex-rays.com](https://hex-rays.com/ida-free/)                 |
| Binary Ninja        | Modern disassembler/decompiler | [binary.ninja](https://binary.ninja/)                          |
| `gdb` + `pwndbg`    | Debugger with exploit helpers  | `apt install gdb` + [pwndbg](https://github.com/pwndbg/pwndbg) |
| `strace` / `ltrace` | Syscall / library call tracing | built-in                                                       |
| `objdump`           | Object file disassembly        | built-in                                                       |
| `radare2`           | Reverse engineering framework  | `apt install radare2`                                          |

### PWN / Binary Exploitation

| Tool               | Purpose                                  | Install                                                  |
| ------------------ | ---------------------------------------- | -------------------------------------------------------- |
| `pwntools`         | CTF exploit development framework        | `pip install pwntools`                                   |
| `ROPgadget`        | ROP chain finder                         | `pip install ROPgadget`                                  |
| `checksec`         | Check binary security flags              | `pip install checksec.sh`                                |
| `one_gadget`       | Find one-shot RCE gadgets in libc        | `gem install one_gadget`                                 |
| `patchelf`         | Modify ELF binary interpreter/RPATH      | `apt install patchelf`                                   |
| `glibc-all-in-one` | Multiple libc versions for local testing | [GitHub](https://github.com/matrix1001/glibc-all-in-one) |

### Steganography

| Tool        | Purpose                            | Install                                                                       |
| ----------- | ---------------------------------- | ----------------------------------------------------------------------------- |
| `steghide`  | Embed/extract data in images/audio | `apt install steghide`                                                        |
| `stegsolve` | Image stego analysis GUI           | [GitHub](https://github.com/eugenekolo/sec-tools/tree/master/stego/stegsolve) |
| `zsteg`     | PNG/BMP steganography detector     | `gem install zsteg`                                                           |
| `outguess`  | Stego in JPEG                      | `apt install outguess`                                                        |
| `audacity`  | Audio spectrogram analysis         | `apt install audacity`                                                        |
| `sox`       | Audio processing CLI               | `apt install sox`                                                             |

---

## Quick Setup Script

```bash
# Update and install base tools
sudo apt update && sudo apt install -y \
  binwalk exiftool foremost p7zip-full \
  curl wget gobuster sqlmap nikto nmap masscan amass \
  wireshark tshark gdb strace ltrace \
  radare2 steghide outguess audacity \
  john hashcat patchelf suricata zeek \
  yara responder

# Python tools
pip install pwntools ROPgadget impacket bloodhound sigma-cli volatility3 flare-floss

# Ruby tools
gem install one_gadget zsteg evil-winrm

# Go tools
go install github.com/ffuf/ffuf/v2@latest
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/jpillora/chisel@latest
```
