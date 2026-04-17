# 🔐 Cryptography

> Break ciphers, crack hashes, and abuse math. Know your encoding from your encryption.

---

## Encoding ≠ Encryption

| Type | Reversible Without Key? | Example |
|---|---|---|
| Encoding | Yes | Base64, Hex, URL |
| Hashing | No (one-way) | MD5, SHA-256 |
| Encryption | Yes (with key) | AES, RSA |

---

## Quick Recognition

```bash
# Identify hash type
hashid 'hash_here'
hash-identifier   # interactive

# Common hash lengths (hex chars)
# MD5    → 32
# SHA-1  → 40
# SHA-256 → 64
# SHA-512 → 128
# bcrypt → starts with $2b$
```

---

## Encoding / Decoding

### Base64
```bash
echo "SGVsbG8gV29ybGQ=" | base64 -d
echo "Hello World" | base64
```

### Hex
```bash
echo "48656c6c6f" | xxd -r -p
echo -n "Hello" | xxd -p
python3 -c "print(bytes.fromhex('48656c6c6f'))"
```

### URL Encoding
```
%20 = space
%3D = =
%2F = /
# Decode in CyberChef or:
python3 -c "import urllib.parse; print(urllib.parse.unquote('%48%65%6c%6c%6f'))"
```

### Common Encodings Cheatsheet
| Encoded | Decoded |
|---|---|
| `SGVsbG8=` | `Hello` (Base64) |
| `48656c6c6f` | `Hello` (Hex) |
| `Uryyb` | `Hello` (ROT13) |

---

## Classical Ciphers

### Caesar / ROT
```bash
# ROT13 (shift 13)
echo "Uryyb" | tr 'A-Za-z' 'N-ZA-Mn-za-m'

# Try all 25 shifts
python3 -c "
s = 'Khoor'
for i in range(26):
    print(i, ''.join(chr((ord(c)-65+i)%26+65) if c.isupper()
                     else chr((ord(c)-97+i)%26+97) if c.islower()
                     else c for c in s))
"
```

### Vigenère
```python
# Online: https://www.dcode.fr/vigenere-cipher
# Or use CyberChef "Vigenère Decode"

# Manual decode
def vigenere_decrypt(ct, key):
    pt = []
    key = key.upper()
    ki = 0
    for c in ct:
        if c.isalpha():
            shift = ord(key[ki % len(key)]) - ord('A')
            base  = ord('A') if c.isupper() else ord('a')
            pt.append(chr((ord(c) - base - shift) % 26 + base))
            ki += 1
        else:
            pt.append(c)
    return ''.join(pt)
```

### Substitution Cipher
- Use frequency analysis — `e`, `t`, `a` are most common in English
- Tools: [quipqiup.com](https://quipqiup.com), [dcode.fr](https://www.dcode.fr/substitution-cipher)

### Atbash
```python
# A↔Z, B↔Y, C↔X ...
def atbash(s):
    return ''.join(chr(ord('Z')-(ord(c)-ord('A'))) if c.isupper()
                   else chr(ord('z')-(ord(c)-ord('a'))) if c.islower()
                   else c for c in s)
```

---

## Hashing & Cracking

```bash
# Identify hash
hashid 'e10adc3949ba59abbe56e057f20f883e'

# Crack with hashcat
hashcat -m 0    hash.txt rockyou.txt   # MD5
hashcat -m 100  hash.txt rockyou.txt   # SHA-1
hashcat -m 1400 hash.txt rockyou.txt   # SHA-256
hashcat -m 3200 hash.txt rockyou.txt   # bcrypt

# Crack with john
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --format=Raw-MD5 hash.txt

# Online hash lookup
# https://crackstation.net
# https://hashes.com
```

---

## RSA

### Key Concepts
```
n = p * q          (modulus, public)
e = public exponent (usually 65537)
d = private exponent (secret)
ct = pt^e mod n    (encrypt)
pt = ct^d mod n    (decrypt)
```

### Common RSA Attacks

#### Small n (factorize it)
```python
# If n is small enough, factor it at https://factordb.com
# or use sympy
from sympy import factorint
factors = factorint(n)
```

#### Common Factor Attack (shared p or q)
```python
from math import gcd
p = gcd(n1, n2)   # if two n share a prime factor
```

#### Small e (e=3, small plaintext → cube root)
```python
import gmpy2
ct = ...
e  = 3
pt, exact = gmpy2.iroot(ct, e)  # if no padding
```

#### Low Private Exponent (Wiener's Attack)
- Use `RsaCtfTool`: `python3 RsaCtfTool.py -n <n> -e <e> --attack wiener`

#### RsaCtfTool (automate all common attacks)
```bash
python3 RsaCtfTool.py -n <n> -e <e> --uncipher <ct>
python3 RsaCtfTool.py --publickey pub.pem --uncipher ct.bin
```

#### Decrypt with known p, q
```python
from Crypto.PublicKey import RSA
from Crypto.Util.number import inverse, long_to_bytes

p = ...
q = ...
e = 65537
n = p * q
d = inverse(e, (p-1)*(q-1))
ct = ...
pt = pow(ct, d, n)
print(long_to_bytes(pt))
```

---

## AES

### Common Modes in CTFs
| Mode | Weakness |
|---|---|
| ECB | Identical plaintext blocks → identical ciphertext blocks (penguin attack) |
| CBC | Bit-flipping attack, padding oracle |
| CTR | Nonce reuse → XOR keystreams |
| GCM | Nonce reuse → authentication bypass |

### ECB Byte-at-a-Time
- When you control prefix + AES-ECB encryption:
  1. Pad input so target byte lands at block boundary
  2. Brute-force the unknown byte one at a time

### CBC Bit-Flip
```
ct[i] ^= (original_byte ^ target_byte)
```
Flipping a bit in ciphertext block i corrupts block i but predictably flips the corresponding bit in decrypted block i+1.

### Padding Oracle (CBC)
- If server tells you "bad padding" vs. other errors, you can decrypt ciphertext byte-by-byte
- Tool: `padbuster`, or implement manually

---

## XOR

```python
# Single-byte XOR
ct = bytes([0x41, 0x2b, 0x3f])
key = 0x42
pt = bytes([b ^ key for b in ct])

# Multi-byte XOR (repeating key)
from itertools import cycle
ct  = b'...'
key = b'KEY'
pt  = bytes(c ^ k for c, k in zip(ct, cycle(key)))

# If key length unknown → use index of coincidence to find key length
# Then frequency analysis per position
```

---

## Useful Python Crypto Libraries

```bash
pip install pycryptodome    # Crypto.Cipher, Crypto.Util.number
pip install gmpy2           # fast big-integer math (iroot, invert, etc.)
pip install sympy           # symbolic math, factoring
```

```python
from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse, getPrime
from Crypto.Cipher import AES
import gmpy2
```

---

## Resources

- [CryptoHack](https://cryptohack.org) — best crypto CTF challenges
- [dcode.fr](https://www.dcode.fr) — classical cipher tools
- [CyberChef](https://gchq.github.io/CyberChef/) — browser-based encoding/decoding
- [RsaCtfTool](https://github.com/RsaCtfTool/RsaCtfTool) — automated RSA attacks
- [CrackStation](https://crackstation.net) — hash lookup database
- [FactorDB](http://factordb.com) — integer factorization database
- [Cryptopals](https://cryptopals.com) — implementation-level crypto challenges
