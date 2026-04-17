# 🛠️ Tools & Setup

> Get your CTF environment up and running.

---

## Environment

A dedicated Linux VM or WSL2 setup keeps your host system clean and lets you run potentially unsafe binaries safely.

**Recommended OS:** Kali Linux, Parrot OS, or Ubuntu 22.04+

---

## Essential Tools by Category

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
  curl wget gobuster sqlmap nikto \
  wireshark tshark gdb strace ltrace \
  radare2 steghide outguess audacity \
  john hashcat patchelf

# Python tools
pip install pwntools ROPgadget

# Ruby tools
gem install one_gadget zsteg
```

---

## CTF Workflow Checklist

```
[ ] Read the challenge description fully
[ ] Note the flag format (flag{...}, CTF{...}, etc.)
[ ] Run `file` on any attachment
[ ] Run `strings` and look for obvious clues
[ ] Run `exiftool` on images/documents
[ ] Run `binwalk` on binaries/archives
[ ] Check if it's a known CTF challenge (Google the title)
[ ] Document all findings in notes
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
