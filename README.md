# Shadow.Lab
> *See. Understand. Control.*

A comprehensive knowledge base for the **Shadow** security research team. This repo is the single source of truth for techniques, tools, and resources across **Red Teaming**, **Blue Teaming**, and the foundational disciplines that underpin them.

Shadow.Lab operates in the **Grey Hat** space — skilled researchers who understand both sides of the fence: how attackers think and operate, and how defenders detect, respond, and harden systems.

---

## 🗺️ Roadmap

### Foundation Path (Start Here)
1. **[Tools & Setup](tools/README.md)** — build your offensive and defensive toolkit
2. **[Cryptography](crypto/README.md)** — encoding, ciphers, hashing, and modern crypto attacks
3. **[Networking & OSINT](osint/README.md)** — recon, domain/IP intelligence, passive reconnaissance
4. **[Web Application Security](web/README.md)** — the attack surface everyone has

### Red Team Path (Offensive Security)
5. **[Red Teaming](red-team/README.md)** — network exploitation, AD attacks, post-exploitation, C2, evasion
6. **[Binary Exploitation / PWN](pwn/README.md)** — memory corruption, ROP, heap exploitation
7. **[Reverse Engineering](rev/README.md)** — static/dynamic analysis, malware reversing, vuln research

### Blue Team Path (Defensive Security)
8. **[Blue Teaming](blue-team/README.md)** — threat detection, SIEM, incident response, threat hunting
9. **[Forensics](forensics/README.md)** — file analysis, memory forensics, network forensics, log analysis
10. **[Steganography](stego/README.md)** — hidden data, covert channels, artefact analysis

### Research & Specialty
- **[Miscellaneous](misc/README.md)** — scripting, unusual encodings, research tooling

---

## 📂 Knowledge Base

### 🔴 Red Team — Offensive Security
| Area | Description |
|---|---|
| [🎯 Red Teaming](red-team/README.md) | Network pentesting, AD attacks, post-exploitation, C2, phishing, evasion |
| [🌐 Web Application Security](web/README.md) | SQLi, XSS, SSRF, LFI/RFI, deserialization, auth bypass |
| [💥 Binary Exploitation](pwn/README.md) | Buffer overflows, ROP chains, heap exploitation, shellcoding |
| [🔬 Reverse Engineering](rev/README.md) | Static/dynamic analysis, decompiling, patching, anti-debug, malware RE |

### 🔵 Blue Team — Defensive Security
| Area | Description |
|---|---|
| [🛡️ Blue Teaming](blue-team/README.md) | Threat detection, SIEM, incident response, malware analysis, threat hunting |
| [🔍 Forensics](forensics/README.md) | File carving, memory forensics, network forensics, log analysis |
| [🖼️ Steganography](stego/README.md) | Covert channel analysis, image/audio stego, hidden data extraction |

### 🔩 Foundations
| Area | Description |
|---|---|
| [🔐 Cryptography](crypto/README.md) | Classical ciphers, modern crypto attacks, hash cracking, protocol weaknesses |
| [👁️ OSINT & Recon](osint/README.md) | Passive recon, metadata, geolocation, threat intelligence |
| [🛠️ Tools & Setup](tools/README.md) | Environment setup, essential tools, cheatsheets |
| [🎲 Miscellaneous](misc/README.md) | Scripting, unusual encodings, research utilities |

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
5. Submit a PR and tag a teammate for review

---

## 📚 External Resources

### Red Team
- [HackTheBox](https://hackthebox.com) — machines, pro labs, and red team simulations
- [TryHackMe](https://tryhackme.com) — guided red/blue team learning paths
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — free web exploitation labs
- [pwn.college](https://pwn.college) — binary exploitation curriculum
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — attack payload reference
- [HackTricks](https://book.hacktricks.xyz) — comprehensive pentesting reference

### Blue Team
- [Blue Team Labs Online](https://blueteamlabs.online) — defensive security challenges
- [LetsDefend](https://letsdefend.io) — SOC analyst training platform
- [Splunk BOTS](https://bots.splunk.com) — boss of the SOC CTF-style SIEM challenges
- [MITRE ATT&CK](https://attack.mitre.org) — adversary tactics and techniques knowledge base
- [Sigma Rules](https://github.com/SigmaHQ/sigma) — generic SIEM detection rules
- [DFIR.training](https://www.dfir.training) — digital forensics and IR resource library

### Research & Intel
- [CVEDetails](https://www.cvedetails.com) — CVE database and vulnerability statistics
- [Exploit-DB](https://www.exploit-db.com) — public exploit archive
- [VulnHub](https://www.vulnhub.com) — vulnerable-by-design VMs
- [CryptoHack](https://cryptohack.org) — cryptography research challenges
- [OSINT Framework](https://osintframework.com) — intelligence gathering tool map
