# 🎲 Miscellaneous

> Research utilities, scripting, unusual encodings, and everything that doesn't fit neatly elsewhere.

> **Grey Hat context:** Scripting and automation are force multipliers for both red and blue teams — from automating recon pipelines to building custom detection parsers. Esoteric encoding knowledge is useful in malware analysis and threat intel.

---

## Common Misc Challenge Types

| Type | Description |
|---|---|
| Programming | Write code to solve a math/logic puzzle, often with a server |
| Esoteric Languages | Brainfuck, Malbolge, Piet, Whitespace, etc. |
| Jail Escape | Python/Bash sandbox escape |
| CAPTCHA / OCR | Read and solve text from images |
| Encoding Chains | Multiple layers of encoding/obfuscation |
| QR Code / Barcode | Decode visual codes |
| Music / Dance notation | Non-standard data encodings |
| Git challenges | Find secrets in git history |
| Docker / CI | Read pipeline artifacts or container configs |

---

## Scripting / Programming Challenges

Most "pwnscript" or proof-of-work challenges need you to automate interaction.

```python
from pwn import *

p = remote('ctf.example.com', 1337)

# Read a math challenge and solve it
line = p.recvline().decode()
# e.g., "What is 3421 * 98712? > "
import re
nums = re.findall(r'\d+', line)
result = int(nums[0]) * int(nums[1])
p.sendline(str(result).encode())

p.interactive()
```

---

## Esoteric Languages

### Brainfuck
```
Commands: > < + - . , [ ]
# Online interpreter: https://brainfuck-online.org
# Or: python3 -c "import brainfuck; ..."
```

### Malbolge
```
# Extremely complex, rarely hand-written in CTFs
# Online: https://malbolge.doleczek.pl/
```

### Piet
```
# Uses colored pixels as instructions
# Interpreter: npiet, or online at https://www.bertnase.de/npiet/npiet-execute.php
```

### Whitespace
```
# Uses only spaces, tabs, and newlines
# Online: https://vii5ard.github.io/whitespace/
```

### JSFuck / JJEncode / AAencode (JavaScript obfuscation)
```javascript
// JSFuck: only uses []()!+
// Paste in browser console or Node.js REPL to evaluate

// JJEncode: decode at https://utf-8.jp/public/jjencode.html
// AAencode: uses Japanese unicode art — paste in browser console
```

---

## Python Jail Escape

The goal is usually to execute arbitrary code or read a file despite restrictions.

```python
# Common restricted globals/builtins
# Bypass: recover __builtins__ from class hierarchy
__builtins__ = {}    # common restriction

# Get builtins back via subclasses
().__class__.__mro__[-1].__subclasses__()

# Find <class 'os._wrap_close'>
import_subclass = [c for c in ''.__class__.__mro__[-1].__subclasses__()
                   if 'wrap_close' in str(c)][0]
import_subclass.__init__.__globals__['system']('id')

# With f-strings in Python 3.12+
f"{ __import__('os').system('id') }"

# audit log bypass (CTF-specific, varies)
```

### Common Filter Bypasses
```python
# underscore filtered → use vars()
# quotes filtered → use chr() or bytes
# import filtered → use __import__
# space filtered → use /**/  or (for Python) use (    )

# Concatenation bypass
__import__('o'+'s').system('id')

# Alternative import
import importlib
importlib.import_module('os').system('id')
```

---

## Bash Jail Escape

```bash
# Restricted shell (rbash) bypasses
# If vim is available: :!/bin/sh
# If awk is available: awk 'BEGIN {system("/bin/sh")}'
# If python is available: python3 -c "import os; os.system('/bin/sh')"
# If less is available: less /etc/passwd → !sh

# Restricted character sets
# Replace /bin/sh with $'\x2f\x62\x69\x6e\x2f\x73\x68'  (hex escape)
# Use env to find shell: env | grep SHELL

# PATH manipulation
export PATH=/usr/local/bin:/bin:/usr/bin
```

---

## Encoding Chains

Many misc challenges layer multiple encodings. Work methodically.

```
Typical chain: Binary → Base64 → Hex → ROT13 → Morse
```

```bash
# CyberChef "Magic" operation → auto-detects and chains decodes
# https://gchq.github.io/CyberChef/#recipe=Magic(3,false,false,'')

# Manual check order:
# 1. Is it printable ASCII? → Try Base64, Hex, ROT13
# 2. Only 0 and 1? → Binary
# 3. Dots and dashes? → Morse
# 4. Numbers 0-7? → Octal
# 5. Numbers with `:` or spaces? → Decimal ASCII
```

### Quick Conversions
```python
# Binary to string
bits = '01001000 01100101 01101100 01101100 01101111'
result = ''.join(chr(int(b, 2)) for b in bits.split())

# Decimal to string
nums = [72, 101, 108, 108, 111]
result = ''.join(chr(n) for n in nums)

# Octal to string
octal = ['110', '145', '154', '154', '157']
result = ''.join(chr(int(o, 8)) for o in octal)
```

---

## QR Codes & Barcodes

```bash
# Decode QR from image
zbarimg image.png
zbarimg -q --raw image.png   # just the data

# Python
pip install pyzbar pillow
python3 -c "
from pyzbar.pyzbar import decode
from PIL import Image
result = decode(Image.open('qr.png'))
print(result[0].data)
"

# Repair broken QR? Use online tools:
# https://merri.cx/qrazybox/
```

---

## Git Challenges

```bash
# Look at all commits
git log --oneline --all

# Check all branches
git branch -a

# Look at stashed changes
git stash list
git stash show -p

# Find deleted content
git log --all --full-history -- '*.txt'
git show HEAD~1:file.txt

# Search commit messages and diffs for keywords
git log -p | grep -i "flag\|secret\|password\|key"

# Check git config for credentials
cat .git/config
```

---

## Morse Code

```
A .-    B -...  C -.-.  D -..   E .
F ..-.  G --.   H ....  I ..    J .---
K -.-   L .-..  M --    N -.    O ---
P .--.  Q --.-  R .-.   S ...   T -
U ..-   V ...-  W .--   X -..-  Y -.--
Z --..
0 -----  1 .----  2 ..---  3 ...--  4 ....-
5 .....  6 -....  7 --...  8 ---..  9 ----.
```

```python
# Decode morse
morse_table = {'.-':'A', '-...':'B', ... }
code = '.... . .-.. .-.. ---'
print(''.join(morse_table.get(c, '?') for c in code.split()))
# Or use: https://morsedecoder.com
```

---

## Phone Keypad / T9

```
2=ABC  3=DEF  4=GHI  5=JKL  6=MNO
7=PQRS  8=TUV  9=WXYZ
```
Number sequences like `4 3 5 5 6` → `H E L L O`

---

## Useful One-Liners

```bash
# Flip binary string
echo "01001000" | rev

# Count character frequency
echo "hello" | fold -w1 | sort | uniq -c | sort -rn

# Base85 decode
python3 -c "import base64; print(base64.b85decode(b'Xk~0{Zv'))"

# HTML entity decode
python3 -c "import html; print(html.unescape('&lt;b&gt;hello&lt;/b&gt;'))"
```

---

## Resources

- [CyberChef](https://gchq.github.io/CyberChef/) — encoding/decoding swiss army knife
- [dcode.fr](https://www.dcode.fr/) — 800+ cipher/code tools
- [Brainfuck interpreter](https://copy.sh/brainfuck/)
- [Piet interpreter](https://www.bertnase.de/npiet/npiet-execute.php)
- [QRazyBox](https://merri.cx/qrazybox/) — QR code repair/analysis
