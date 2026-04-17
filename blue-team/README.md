# 🛡️ Blue Teaming

> Threat detection, incident response, malware analysis, and proactive threat hunting.

Blue teaming is the art of defending systems and networks against adversaries — both real attackers and simulated red team operations. Effective blue teamers understand how attacks work so they can detect, contain, and remediate them faster.

---

## 🔵 Blue Team Disciplines

| Discipline | Role |
|---|---|
| **SOC Analysis** | Monitor alerts, triage events, escalate confirmed incidents |
| **Incident Response (IR)** | Contain, eradicate, and recover from security incidents |
| **Digital Forensics (DFIR)** | Collect and analyse artefacts to reconstruct what happened |
| **Threat Hunting** | Proactively search for threats not caught by automated tools |
| **Malware Analysis** | Reverse-engineer malicious code to understand its behaviour |
| **Threat Intelligence** | Gather, enrich, and operationalise adversary knowledge |
| **Detection Engineering** | Write detection rules (SIEM, EDR, IDS) and tune false positives |

---

## 🚨 Incident Response Lifecycle

```
1. Preparation     → Build playbooks, deploy logging, train the team
2. Detection       → Identify indicators of compromise (IOCs)
3. Containment     → Short-term (isolate host) and long-term (patch, block)
4. Eradication     → Remove malware, revoke credentials, close access
5. Recovery        → Restore services, verify integrity, monitor closely
6. Lessons Learned → Post-incident review, update playbooks and detections
```

Reference: [NIST SP 800-61r2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)

---

## 📊 SIEM & Log Analysis

### Key Log Sources

| Source | What to Look For |
|---|---|
| Windows Security Events | 4624/4625 (logon), 4688 (process creation), 4648 (explicit logon), 4698 (scheduled task) |
| Sysmon | Process creation, network connections, file creation, registry changes |
| PowerShell logs | Script block logging (4104), module logging |
| Windows Defender / EDR | Detection events, quarantine actions |
| Firewall / proxy logs | Allowed/denied connections, unusual outbound traffic |
| DNS logs | Suspicious domains, high-frequency queries, DGA patterns |
| Web server logs | Error spikes, unusual URIs, encoding anomalies |
| Authentication logs | Failed logins, off-hours access, impossible travel |

### Splunk Essentials
```splunk
`comment("Failed logins")`
index=windows EventCode=4625 | stats count by src_ip, user | sort -count

`comment("Process creation - Sysmon Event 1")`
index=sysmon EventCode=1 | table _time, host, user, Image, CommandLine, ParentImage

`comment("PowerShell script block logging")`
index=windows EventCode=4104 | search ScriptBlockText="*Invoke-*" OR ScriptBlockText="*iex*"

`comment("Network connections to rare external IPs")`
index=sysmon EventCode=3 DestinationIp!="10.*" DestinationIp!="192.168.*" DestinationIp!="172.16.*"
| stats count by DestinationIp, Image | sort -count

`comment("Lateral movement via PsExec")`
index=windows EventCode=7045 ServiceName="PSEXESVC" | table _time, host, ServiceFileName

`comment("DCSync detection")`
index=windows EventCode=4662 OperationType="%%14674" ObjectDN="*DC=*"
| where match(Properties, "(?i)1131f6ad|1131f6aa")
```

### Elastic (EQL) Essentials
```eql
// Process injection
sequence by host.name
  [process where process.name == "powershell.exe"]
  [network where destination.port in (443, 80, 8080) and not destination.ip in ("10.0.0.0/8")]

// Credential dumping via LSASS
process where event.type == "start"
  and process.name in ("procdump.exe", "procdump64.exe", "rundll32.exe")
  and process.args : "*lsass*"
```

### Sigma Rules
```yaml
# Example Sigma rule — Suspicious PowerShell download cradle
title: PowerShell Download Cradle
status: experimental
logsource:
  product: windows
  category: ps_script
detection:
  selection:
    ScriptBlockText|contains:
      - 'DownloadString'
      - 'DownloadFile'
      - 'IEX'
      - 'Invoke-Expression'
      - 'WebClient'
  condition: selection
falsepositives:
  - Legitimate admin scripts
level: medium
```

Convert Sigma to your SIEM:
```bash
sigma convert -t splunk rules/windows/powershell/powershell_download_cradle.yml
sigma convert -t elastic-lucene rules/windows/powershell/powershell_download_cradle.yml
```

---

## 🔬 Malware Analysis

### Safe Lab Setup
```
- Isolated VM (no host-only or bridged network — use internal-only)
- Snapshots before and after execution
- INetSim or FakeNet-NG for network simulation
- Recommended VMs: FlareVM (Windows), REMnux (Linux)
```

### Static Analysis
```bash
# File type and hashes
file malware.exe
md5sum malware.exe && sha256sum malware.exe
# Submit hash to VirusTotal: https://www.virustotal.com

# Strings
strings malware.exe
strings -el malware.exe    # Unicode strings
FLOSS malware.exe          # deobfuscated strings (FLOSS tool)

# PE analysis
pesign malware.exe         # check code signing
pecheck malware.exe        # imports, exports, sections
pestudio malware.exe       # GUI: strings, imports, entropy, IoCs

# Detect packer
Detect-It-Easy (DIE)
ExeinfoPE

# Imports → reveals capabilities
# CreateRemoteThread → process injection
# VirtualAllocEx, WriteProcessMemory → classic injection
# RegSetValueEx, CreateService → persistence
# InternetOpenA, HttpSendRequest, WinHttpOpen → C2 comms
# CryptEncrypt, CryptDecrypt → encryption (possibly ransomware)
```

### Dynamic Analysis
```bash
# Windows sandbox tools
ProcessMonitor (Procmon)   # file, registry, network activity
ProcessHacker / Process Explorer
Wireshark / FakeNet-NG     # network traffic capture
RegShot                    # registry snapshot diff (before/after run)
API Monitor                # trace API calls

# Linux / automated sandboxes
cuckoo sandbox             # automated dynamic analysis (self-hosted)
# Online: https://any.run, https://app.any.run (interactive)
# https://tria.ge, https://www.hybrid-analysis.com

# Run with FakeNet-NG (simulates DNS, HTTP, SMTP)
fakenet &
.\malware.exe

# Monitor child processes
.\malware.exe &
ps auxf / Get-Process
```

### Memory Forensics for Malware
```bash
# Volatility 3
python3 vol.py -f infected.dmp windows.malfind         # injected code regions
python3 vol.py -f infected.dmp windows.pstree          # process tree anomalies
python3 vol.py -f infected.dmp windows.netscan         # active connections
python3 vol.py -f infected.dmp windows.dlllist --pid 1234
python3 vol.py -f infected.dmp windows.handles --pid 1234
python3 vol.py -f infected.dmp windows.dumpfiles --pid 1234  # dump process files

# Extract and scan extracted code
python3 vol.py -f infected.dmp windows.malfind | grep -v "^Volatility\|^$" | awk '{print $1}' | sort -u
yara -r malware_rules.yar extracted_files/
```

### YARA Rules
```yara
rule SuspiciousPowerShellDownload {
    meta:
        description = "Detects PowerShell download cradles"
        author = "Shadow.Lab"
    strings:
        $s1 = "DownloadString" nocase
        $s2 = "IEX" nocase
        $s3 = "WebClient" nocase
        $s4 = "Invoke-Expression" nocase
    condition:
        2 of ($s1, $s2, $s3, $s4)
}

rule SuspiciousImports {
    meta:
        description = "PE with common injection imports"
    strings:
        $a = "VirtualAllocEx"
        $b = "WriteProcessMemory"
        $c = "CreateRemoteThread"
    condition:
        all of them
}
```

```bash
# Scan with YARA
yara -r rules/ suspicious_file.exe
yara -r rules/ /path/to/scan/
```

---

## 🔭 Threat Hunting

Threat hunting is the proactive, human-led search for threats that automated tools have not detected.

### Hunting Hypothesis Framework
```
1. Threat Intel → "APT29 uses beacon over HTTPS with JA3 fingerprint X"
2. TTP-based    → "Hunt for evidence of Kerberoasting in the last 30 days"
3. Anomaly-based → "Find hosts making DNS queries to 50+ unique domains/hour"
4. Situational  → "Hunt after red team engagement to validate detections"
```

### Common Hunt Scenarios

#### Suspicious Scheduled Tasks
```splunk
index=windows EventCode=4698 OR EventCode=4702
| rex field=TaskContent "(?i)<Command>(?P<cmd>[^<]+)"
| where match(cmd, "(?i)(powershell|wscript|mshta|regsvr32|certutil|bitsadmin)")
| table _time, host, user, TaskName, cmd
```

#### Beaconing Detection (C2 Traffic)
```splunk
-- Identify hosts with very regular outbound connection intervals
index=network_traffic dest_port IN (80,443,8080)
| bucket _time span=1h
| stats count by _time, src_ip, dest_ip
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by src_ip, dest_ip
| where stdev_count < 2   -- suspiciously regular = low stdev
```

#### Living-off-the-Land Execution
```splunk
index=sysmon EventCode=1
| where match(Image, "(?i)(certutil|mshta|regsvr32|wscript|cscript|msiexec|rundll32)")
  AND match(CommandLine, "(?i)(http|ftp|\\\\|base64|decode)")
| table _time, host, user, Image, CommandLine, ParentImage, ParentCommandLine
```

#### Pass-the-Hash / Lateral Movement
```splunk
`comment("Logon Type 3 with NTLM instead of Kerberos")`
index=windows EventCode=4624 LogonType=3 AuthenticationPackageName=NTLM
| stats count by src_ip, TargetUserName, host
| where count > 5
```

#### DGA Domain Detection
```splunk
`comment("High entropy domains in DNS queries")`
index=dns query_type=A
| eval domain_len=len(query)
| eval char_freq=mvmap(split(query,""), len(mvfilter(match(mvindex(split(query,""),0), ".")))),
       entropy=-(sum(eval(f/domain_len * log(f/domain_len, 2))) over char_freq)
| where entropy > 3.5 AND domain_len > 20
| stats count by query, src_ip | sort -count
```

---

## 🔑 Threat Intelligence

### Intelligence Pyramid of Pain
```
Hash values     → Trivial (attacker changes instantly)
IP addresses    → Easy  (VPNs, proxies)
Domain names    → Simple (new domain in minutes)
Network artefacts → Annoying (JA3, URI patterns)
Host artefacts  → Challenging (registry keys, file paths)
Tools           → Tough (recompile with changes)
TTPs            → Hard  (fundamental behaviour)
```
_Reference: [David Bianco's Pyramid of Pain](https://detect-respond.blogspot.com/2013/03/the-pyramid-of-pain.html)_

### Intel Sources
```
Free:
- https://otx.alienvault.com       AlienVault OTX — IoC sharing
- https://threatfox.abuse.ch       Malware IOCs
- https://urlhaus.abuse.ch         Malicious URLs
- https://malwarebazaar.abuse.ch   Malware samples
- https://www.virustotal.com       Hash/IP/domain reputation
- https://shodan.io                Internet-wide scanning data
- https://greynoise.io             Internet noise vs. targeted activity

OSINT frameworks:
- MISP (Malware Information Sharing Platform)
- OpenCTI
```

### IoC Hunting
```bash
# Search for known-bad hash in logs
grep -r "44d88612fea8a8f36de82e1278abb02f" /var/log/

# Search for IP in firewall/proxy logs
grep "185.220.101.34" access.log

# YARA scan for known malware families
yara -r /opt/yara-rules/malware/ /path/to/scan/

# Sigma rule deployment
python3 sigmac -t splunk rule.yml >> custom_searches.conf
```

---

## 🏥 Incident Response Playbooks

### Ransomware
```
1. IMMEDIATE: Isolate affected hosts from network (disable NIC, not shutdown)
2. Preserve memory dump before shutdown (lsass, suspicious processes)
3. Identify patient zero — check file creation timestamps
4. Check for lateral movement — event logs, network flow data
5. Identify data exfiltration — DLP logs, proxy/firewall egress
6. Identify ransomware family — submit sample to ID-Ransomware (https://id-ransomware.malwarehunterteam.com)
7. Determine if decryptor exists (https://www.nomoreransom.org)
8. Scope full affected systems — check all hosts for encrypted files, indicators
9. Eradicate: rebuild from clean backups (verify backups pre-date infection)
10. Recover and monitor closely for re-infection
```

### Account Compromise
```
1. Disable compromised account immediately
2. Force password reset on all related accounts (shared passwords)
3. Revoke all active sessions and OAuth tokens
4. Check mailbox rules (auto-forwarding to external address is common)
5. Review MFA registrations — attacker may have added their own device
6. Audit email forwards and calendar sharing
7. Check sent items and deleted items for data exfiltration
8. Review sign-in logs for IP/device/location patterns
9. Scope: check for lateral movement using compromised credentials
10. Harden: enforce MFA, conditional access, credential monitoring
```

### Malware / C2 Beacon
```
1. Identify all affected hosts via C2 IOC (IP, domain, hash, JA3)
2. Capture memory from affected hosts before isolation
3. Isolate: remove from network, keep powered on for analysis
4. Identify persistence mechanisms (scheduled tasks, services, registry run keys)
5. Determine implant capability (keylogging, screenshot, lateral movement, exfil)
6. Review 90-day log history for dwell time and full scope
7. Eradicate: remove all persistence, rebuild compromised hosts
8. Reset credentials accessed from or on compromised hosts
9. Block IOCs at perimeter (firewall, proxy, DNS sinkhole)
10. Improve detections based on observed TTPs
```

---

## 🛠️ Blue Team Tools

| Category | Tool | Purpose |
|---|---|---|
| SIEM | [Splunk](https://www.splunk.com) | Log aggregation and detection |
| SIEM | [Elastic Stack (ELK)](https://www.elastic.co) | Open-source log analysis |
| SIEM | [Microsoft Sentinel](https://azure.microsoft.com/en-us/products/microsoft-sentinel) | Cloud-native SIEM |
| EDR | [Velociraptor](https://www.rapid7.com/products/velociraptor/) | Open-source DFIR and endpoint monitoring |
| EDR | [Wazuh](https://wazuh.com) | Open-source SIEM + HIDS |
| Endpoint logging | [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) | Detailed Windows process/network logging |
| Network | [Zeek (Bro)](https://zeek.org) | Network traffic analysis and logging |
| Network | [Suricata](https://suricata.io) | Network IDS/IPS and NSM |
| Malware analysis | [REMnux](https://remnux.org) | Linux distro for malware analysis |
| Malware analysis | [FlareVM](https://github.com/mandiant/flare-vm) | Windows malware analysis toolkit |
| Sandbox | [Cuckoo](https://cuckoosandbox.org) | Automated malware sandbox |
| Sandbox | [Any.run](https://app.any.run) | Interactive online sandbox |
| Forensics | [Autopsy](https://www.autopsy.com) | Digital forensics GUI |
| Forensics | [Volatility 3](https://github.com/volatilityfoundation/volatility3) | Memory forensics |
| Threat intel | [MISP](https://www.misp-project.org) | Threat intelligence sharing platform |
| Detection | [Sigma](https://github.com/SigmaHQ/sigma) | Generic SIEM detection rules |
| Detection | [YARA](https://virustotal.github.io/yara/) | Pattern matching for malware |

---

## 📚 Resources

- [MITRE ATT&CK](https://attack.mitre.org) — adversary techniques and detection guidance
- [Blue Team Labs Online](https://blueteamlabs.online) — defensive security challenges
- [LetsDefend](https://letsdefend.io) — SOC analyst training
- [Splunk BOTS](https://bots.splunk.com) — SIEM detection challenge
- [DFIR.training](https://www.dfir.training) — DFIR resource library
- [Eric Zimmerman's Tools](https://ericzimmerman.github.io) — Windows forensics utilities
- [Awesome Incident Response](https://github.com/meirwah/awesome-incident-response) — curated IR resource list
- [SANS Posters & Cheatsheets](https://www.sans.org/posters/) — quick reference cards
- [The DFIR Report](https://thedfirreport.com) — real-world intrusion case studies
- [Sigma Rules Repository](https://github.com/SigmaHQ/sigma) — community detection rules
