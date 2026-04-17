# Shadow.Wiki

> _See. Understand. Control._

A comprehensive knowledge base for the **Shadow.Lab** security research team. This repo is the single source of truth for techniques, tools, and resources across **Red Teaming**, **Blue Teaming**, and the foundational disciplines that underpin them.

Shadow.Lab operates in the **Grey Hat** space — skilled researchers who understand both sides of the fence: how attackers think and operate, and how defenders detect, respond, and harden systems.

---

## 📂 Knowledge Base

### 🔴 Red Team — Offensive Security

| Area                                         | Description                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------ |
| [🎯 Red Teaming](red-team/README.md)         | Network pentesting, AD attacks, post-exploitation, C2, phishing, evasion |
| [🌐 Web Application Security](web/README.md) | SQLi, XSS, SSRF, LFI/RFI, deserialization, auth bypass                   |
| [💥 Binary Exploitation](pwn/README.md)      | Buffer overflows, ROP chains, heap exploitation, shellcoding             |
| [🔬 Reverse Engineering](rev/README.md)      | Static/dynamic analysis, decompiling, patching, anti-debug, malware RE   |

### 🔵 Blue Team — Defensive Security

| Area                                   | Description                                                                 |
| -------------------------------------- | --------------------------------------------------------------------------- |
| [🛡️ Blue Teaming](blue-team/README.md) | Threat detection, SIEM, incident response, malware analysis, threat hunting |
| [🔍 Forensics](forensics/README.md)    | File carving, memory forensics, network forensics, log analysis             |
| [🖼️ Steganography](stego/README.md)    | Covert channel analysis, image/audio stego, hidden data extraction          |

### 🔩 Foundations

| Area                                            | Description                                                                       |
| ----------------------------------------------- | --------------------------------------------------------------------------------- |
| [🔐 Cryptography](crypto/README.md)             | Classical ciphers, modern crypto attacks, hash cracking, protocol weaknesses      |
| [👁️ OSINT & Recon](osint/README.md)             | Passive recon, metadata, geolocation, threat intelligence                         |
| [🛠️ Tools & Setup](tools/README.md)             | Environment setup, essential tools, cheatsheets                                   |
| [💻 Programming Languages](languages/README.md) | C, Python, Bash, PowerShell, Assembly, Rust, Go, JS, Java — exploit dev & tooling |
| [🎲 Miscellaneous](misc/README.md)              | Scripting, unusual encodings, research utilities                                  |

> 💡 New here or haven't set up your environment yet? Start with [🛠️ Tools & Setup](tools/README.md).

---

## 🔘 Grey Hat Principles

- **Understand both sides** — the best defenders think like attackers; the best attackers understand defenses
- **Responsible disclosure** — report vulnerabilities through proper channels; do not cause harm
- **Authorised scope only** — never test systems you do not have explicit written permission to test
- **Document everything** — reproducible findings, clear timelines, and clean write-ups matter
- **Continuous learning** — the threat landscape evolves; so must you
- **Operate ethically** — Grey Hat does not mean lawless; it means deeply informed

---

## 🤝 Contributing

1. Branch off `main` and add your guide or improvement
2. Keep guides practical — commands, real-world examples, and tool references
3. Tag content as `[RED]`, `[BLUE]`, or `[BOTH]` where the context isn't obvious
4. Use consistent Markdown formatting
5. Submit a PR

---

## <img src="https://cdn.simpleicons.org/discord/5865F2" width="22" height="22" alt="Discord" style="vertical-align:middle"/> Discord Server

Join the Shadow.Lab community — share findings, ask questions, and collaborate with the team.

[![Discord](https://img.shields.io/badge/Discord-Join%20Shadow.Lab-5865F2?logo=discord&logoColor=white)](https://discord.gg/FpdPbJU6JE)
