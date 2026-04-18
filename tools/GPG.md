# GPG

## Install

```bash
sudo pacman -S gnupg
```

---

## Generate a Keypair

```bash
gpg --full-generate-key
```

When prompted:

| Prompt       | Recommended value       |
| ------------ | ----------------------- |
| Key type     | `RSA and RSA` (default) |
| Key size     | `4096`                  |
| Expiration   | `0` (never)             |
| Name / Email | your alias              |
| Passphrase   | strong and memorized    |

---

## Encrypt a File

```bash
gpg --encrypt --recipient "user" file.txt
```

Output is `file.txt.gpg` — unreadable without the private key.

---

## Decrypt a File

```bash
gpg --decrypt file.txt.gpg > file.txt
```

---

## Key Management

List keys:

```bash
gpg --list-keys          # public keys
gpg --list-secret-keys   # private keys
```

Export public key (to share):

```bash
gpg --export --armor "user" > user_public.asc
```

Backup private key (keep offline — USB or paper):

```bash
gpg --export-secret-keys --armor "user" > user_private.asc
```

---

## Sign a File

Prove a file came from you:

```bash
gpg --sign file.txt          # binary signature embedded
gpg --clearsign file.txt     # human-readable signed output
gpg --detach-sign file.txt   # separate .sig file
```

Verify a signature:

```bash
gpg --verify file.txt.sig file.txt
```

---

## Notes

- Even if your files are stolen, they are unreadable without the private key.
- Store key backups offline (USB + printed copy as last resort).
- Practice encrypting and decrypting dummy files until it is second nature.

---

## What to Read Next

| You want to...           | Go here               |
| ------------------------ | --------------------- |
| Set up encrypted backups | [Backups](BackUps.md) |
