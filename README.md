# Shadow.Lab
> *See. Understand. Control.*

A comprehensive roadmap and guide repository for the **Shadow** CTF team. This repo is the single source of truth for techniques, tools, and resources across all major CTF categories.

---

## 🗺️ Roadmap

### Beginner Path
1. Start with **[Tools & Setup](tools/README.md)** — get your environment ready
2. Learn **[Cryptography](crypto/README.md)** basics — encoding, classic ciphers, hashing
3. Explore **[Forensics](forensics/README.md)** — file analysis, memory dumps, traffic captures
4. Try **[Steganography](stego/README.md)** — hidden data in images/audio
5. Work through **[OSINT](osint/README.md)** — research & intelligence gathering
6. Study **[Web Exploitation](web/README.md)** — the most common category in CTFs

### Intermediate Path
7. Dive into **[Reverse Engineering](rev/README.md)** — understand compiled binaries
8. Tackle **[Binary Exploitation / PWN](pwn/README.md)** — memory corruption & exploitation

### Advanced / Specialty
- **[Miscellaneous](misc/README.md)** — everything that doesn't fit elsewhere

---

## 📂 Categories

| Category | Description |
|---|---|
| [🌐 Web](web/README.md) | SQL injection, XSS, SSRF, LFI/RFI, deserialization, auth bypass |
| [💥 PWN](pwn/README.md) | Buffer overflows, ROP chains, heap exploitation, shellcoding |
| [🔬 Reverse Engineering](rev/README.md) | Static/dynamic analysis, decompiling, patching, anti-debug |
| [🔐 Cryptography](crypto/README.md) | Classical ciphers, modern crypto attacks, hash cracking |
| [🔍 Forensics](forensics/README.md) | File carving, memory forensics, network forensics, log analysis |
| [👁️ OSINT](osint/README.md) | Metadata, geolocation, social engineering research |
| [🖼️ Steganography](stego/README.md) | Image/audio stego, LSB, hidden data extraction |
| [🛠️ Tools & Setup](tools/README.md) | Environment setup, essential tools, cheatsheets |
| [🎲 Miscellaneous](misc/README.md) | Scripting, esoteric languages, puzzles, everything else |

---

## 🏁 Quick Reference

### General CTF Tips
- Read the challenge description carefully — the flag format is usually given (e.g., `flag{...}`)
- Always check file metadata: `file`, `strings`, `exiftool`, `binwalk`
- When stuck, Google the challenge name or error message — it's not cheating, it's OSINT
- Document your findings as you go; it helps teammates and future you
- Work in a VM or isolated container to stay safe

### Flag Formats
Common formats seen in CTFs:
```
flag{...}
CTF{...}
TEAM{...}
picoCTF{...}
```

---

## 🤝 Contributing

1. Branch off `main` and add your guide or improvement
2. Keep guides practical — commands, examples, and real challenge references
3. Use consistent Markdown formatting
4. Submit a PR and tag a teammate for review

---

## 📚 External Resources

- [CTFtime.org](https://ctftime.org) — upcoming CTF events and team rankings
- [PicoCTF](https://picoctf.org) — beginner-friendly practice challenges
- [HackTheBox](https://hackthebox.com) — machines and web challenges
- [TryHackMe](https://tryhackme.com) — guided learning paths
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — free web exploitation labs
- [pwn.college](https://pwn.college) — binary exploitation curriculum
- [CryptoHack](https://cryptohack.org) — cryptography challenges
- [CTF101](https://ctf101.org) — category overviews and basics
