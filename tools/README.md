# 🛠️ Tools & Setup

> Build your offensive and defensive security environment.

---

## Environment

A dedicated Linux VM or WSL2 setup keeps your host system clean and lets you run potentially unsafe binaries safely. For malware analysis, use a fully isolated internal-only VM with no host network access.

**Recommended OS:**
- **Red Team / General:** Kali Linux, Parrot OS
- **Blue Team / DFIR:** REMnux, Ubuntu 22.04+ with Sysmon + Elastic/Splunk
- **Malware Analysis:** FlareVM (Windows), REMnux (Linux)

---

## 🔴 Red Team Tools

### Reconnaissance & OSINT
| Tool | Purpose | Install |
|---|---|---|
| `nmap` | Network port scanner | `apt install nmap` |
| `masscan` | Fast mass port scanner | `apt install masscan` |
| `subfinder` | Passive subdomain enumeration | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| `amass` | Subdomain enumeration and mapping | `apt install amass` |
| `theHarvester` | Email/domain OSINT | `apt install theharvester` |
| `sherlock` | Username search across platforms | `pip install sherlock-project` |

### Web Exploitation
| Tool | Purpose | Install |
|---|---|---|
| Burp Suite Pro | HTTP proxy, scanner, intruder | [portswigger.net](https://portswigger.net/burp/pro) |
| `ffuf` | Web fuzzing | `go install github.com/ffuf/ffuf/v2@latest` |
| `sqlmap` | SQL injection automation | `apt install sqlmap` |
| `nuclei` | Template-based vulnerability scanner | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| `nikto` | Web vulnerability scanner | `apt install nikto` |

### Active Directory & Network Attacks
| Tool | Purpose | Install |
|---|---|---|
| `impacket` | AD/SMB attack suite (psexec, secretsdump, etc.) | `pip install impacket` |
| `bloodhound-python` | BloodHound data collection | `pip install bloodhound` |
| BloodHound | AD attack path visualisation | [GitHub](https://github.com/BloodHoundAD/BloodHound) |
| `evil-winrm` | WinRM shell | `gem install evil-winrm` |
| `responder` | LLMNR/NBT-NS poisoning | `apt install responder` |
| `crackmapexec` | AD Swiss-army knife | `apt install crackmapexec` |
| `kerbrute` | Kerberos user enumeration and bruteforce | [GitHub](https://github.com/ropnop/kerbrute) |

### Post-Exploitation & C2
| Tool | Purpose | Install |
|---|---|---|
| Metasploit | Exploitation and post-exploitation framework | `apt install metasploit-framework` |
| [Sliver](https://github.com/BishopFox/sliver) | Open-source C2 framework | GitHub releases |
| `msfvenom` | Payload generation | bundled with Metasploit |
| `chisel` | TCP/UDP tunnel over HTTP | `go install github.com/jpillora/chisel@latest` |
| `ligolo-ng` | Tunneling for pivoting | [GitHub](https://github.com/nicocha30/ligolo-ng) |

### Privilege Escalation
| Tool | Purpose | Install |
|---|---|---|
| `linpeas` | Linux privilege escalation enumeration | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `winpeas` | Windows privilege escalation enumeration | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `mimikatz` | Windows credential dumping | [GitHub](https://github.com/gentilkiwi/mimikatz) |
| `Rubeus` | Kerberos manipulation | [GitHub](https://github.com/GhostPack/Rubeus) |

---

## 🔵 Blue Team Tools

### SIEM & Log Analysis
| Tool | Purpose | Install |
|---|---|---|
| [Elastic Stack (ELK)](https://www.elastic.co) | Log ingestion, search, and visualisation | Docker / APT |
| [Splunk Free](https://www.splunk.com/en_us/download.html) | SIEM with 500MB/day free tier | Installer |
| [Wazuh](https://wazuh.com) | Open-source SIEM + HIDS | [Install guide](https://documentation.wazuh.com/) |
| `sigma` | Convert generic detection rules to SIEM queries | `pip install sigma-cli` |

### Endpoint Detection & Forensics
| Tool | Purpose | Install |
|---|---|---|
| [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) | Detailed Windows event logging | Windows |
| [Velociraptor](https://github.com/Velocidex/velociraptor) | DFIR and endpoint monitoring | GitHub releases |
| [Volatility 3](https://github.com/volatilityfoundation/volatility3) | Memory forensics | `pip install volatility3` |
| [Eric Zimmerman Tools](https://ericzimmerman.github.io) | Windows forensics utilities (PECmd, MFTECmd, etc.) | Windows |
| `autopsy` | Digital forensics GUI | [autopsy.com](https://www.autopsy.com/) |

### Network Monitoring & Analysis
| Tool | Purpose | Install |
|---|---|---|
| [Zeek (Bro)](https://zeek.org) | Network traffic analysis and logging | `apt install zeek` |
| [Suricata](https://suricata.io) | Network IDS/IPS | `apt install suricata` |
| Wireshark / `tshark` | PCAP analysis | `apt install wireshark` |
| `zeek-cut` | Zeek log field extractor | bundled with Zeek |

### Malware Analysis
| Tool | Purpose | Install |
|---|---|---|
| [REMnux](https://remnux.org) | Linux malware analysis distro | VM download |
| [FlareVM](https://github.com/mandiant/flare-vm) | Windows malware analysis toolkit | Windows setup script |
| `FLOSS` | Extract obfuscated strings from malware | `pip install flare-floss` |
| `pestudio` | PE file static analysis | [winitor.com](https://www.winitor.com/) |
| `YARA` | Pattern-matching for malware detection | `apt install yara` |
| [Any.run](https://app.any.run) | Interactive online sandbox | Browser |
| [Hybrid-Analysis](https://www.hybrid-analysis.com) | Automated online sandbox | Browser |

### Threat Intelligence
| Tool | Purpose | Install |
|---|---|---|
| [MISP](https://www.misp-project.org) | Threat intel sharing platform | [Install guide](https://www.misp-project.org/download/) |
| [OpenCTI](https://www.opencti.io) | Threat intel management | Docker |

---

## General Security Tools by Category

### General
| Tool | Purpose | Install |
|---|---|---|
| `file` | Identify file type | built-in |
| `strings` | Extract printable strings from binary | built-in |
| `xxd` / `hexdump` | Hex viewer | built-in |
| `binwalk` | Firmware/archive analysis and extraction | `pip install binwalk` |
| `exiftool` | Read/write file metadata | `apt install libimage-exiftool-perl` |
| `foremost` | File carving | `apt install foremost` |
| `7z` / `unzip` | Archive extraction | `apt install p7zip-full` |
| CyberChef | Browser-based encode/decode/transform | [gchq.github.io/CyberChef](https://gchq.github.io/CyberChef/) |

### Web
| Tool | Purpose | Install |
|---|---|---|
| Burp Suite | HTTP proxy & scanner | [portswigger.net](https://portswigger.net/burp) |
| `curl` / `wget` | HTTP requests from CLI | built-in |
| `ffuf` | Web fuzzing (dirs, params, vhosts) | `go install github.com/ffuf/ffuf/v2@latest` |
| `gobuster` | Directory/DNS brute-force | `apt install gobuster` |
| `sqlmap` | Automated SQL injection | `apt install sqlmap` |
| `nikto` | Web vulnerability scanner | `apt install nikto` |
| Wappalyzer | Technology fingerprinting | browser extension |

### Cryptography
| Tool | Purpose | Install |
|---|---|---|
| `openssl` | Swiss-army crypto tool | built-in |
| `hashcat` | GPU password cracking | `apt install hashcat` |
| `john` | CPU password cracking (John the Ripper) | `apt install john` |
| SageMath | Math-heavy crypto scripting | [sagemath.org](https://www.sagemath.org/) |
| CyberChef | Quick encode/decode | browser |
| `RsaCtfTool` | RSA attack automation | [GitHub](https://github.com/RsaCtfTool/RsaCtfTool) |

### Forensics
| Tool | Purpose | Install |
|---|---|---|
| Wireshark / `tshark` | PCAP analysis | `apt install wireshark` |
| Volatility 3 | Memory forensics | [GitHub](https://github.com/volatilityfoundation/volatility3) |
| Autopsy | Digital forensics GUI | [autopsy.com](https://www.autopsy.com/) |
| `scalpel` | File carving | `apt install scalpel` |
| `NetworkMiner` | Passive network sniffer/forensics | [netresec.com](https://www.netresec.com/) |

### Reverse Engineering
| Tool | Purpose | Install |
|---|---|---|
| Ghidra | NSA decompiler (free) | [ghidra-sre.org](https://ghidra-sre.org/) |
| IDA Free | Industry-standard disassembler | [hex-rays.com](https://hex-rays.com/ida-free/) |
| Binary Ninja | Modern disassembler/decompiler | [binary.ninja](https://binary.ninja/) |
| `gdb` + `pwndbg` | Debugger with exploit helpers | `apt install gdb` + [pwndbg](https://github.com/pwndbg/pwndbg) |
| `strace` / `ltrace` | Syscall / library call tracing | built-in |
| `objdump` | Object file disassembly | built-in |
| `radare2` | Reverse engineering framework | `apt install radare2` |

### PWN / Binary Exploitation
| Tool | Purpose | Install |
|---|---|---|
| `pwntools` | CTF exploit development framework | `pip install pwntools` |
| `ROPgadget` | ROP chain finder | `pip install ROPgadget` |
| `checksec` | Check binary security flags | `pip install checksec.sh` |
| `one_gadget` | Find one-shot RCE gadgets in libc | `gem install one_gadget` |
| `patchelf` | Modify ELF binary interpreter/RPATH | `apt install patchelf` |
| `glibc-all-in-one` | Multiple libc versions for local testing | [GitHub](https://github.com/matrix1001/glibc-all-in-one) |

### Steganography
| Tool | Purpose | Install |
|---|---|---|
| `steghide` | Embed/extract data in images/audio | `apt install steghide` |
| `stegsolve` | Image stego analysis GUI | [GitHub](https://github.com/eugenekolo/sec-tools/tree/master/stego/stegsolve) |
| `zsteg` | PNG/BMP steganography detector | `gem install zsteg` |
| `outguess` | Stego in JPEG | `apt install outguess` |
| `audacity` | Audio spectrogram analysis | `apt install audacity` |
| `sox` | Audio processing CLI | `apt install sox` |

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

---

## Security Workflow Checklist

```
Initial Assessment:
[ ] Identify the target/asset type
[ ] Run `file` on any attachment or sample
[ ] Run `strings` and look for obvious clues
[ ] Run `exiftool` on files with metadata
[ ] Run `binwalk` on binaries/archives
[ ] Check known hash reputation (VirusTotal, MalwareBazaar)
[ ] Document all findings with timestamps
[ ] Ask a teammate before spending more than 1 hour stuck
```

---

## Useful One-Liners

```bash
# Find all strings in a binary, longer than 8 chars
strings -n 8 binary_file

# Hex dump first 256 bytes
xxd file | head -16

# Extract embedded files
binwalk -e suspicious_file

# Identify hash type
hashid 'hash_value_here'

# Crack MD5 hash with rockyou
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt

# Base64 decode
echo "SGVsbG8=" | base64 -d

# ROT13
echo "Uryyb" | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```
