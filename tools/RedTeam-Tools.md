## Reconnaissance & OSINT

> **Previous:** [General Security Tools](GeneralSecurity-Tools.md)

| Tool           | Purpose                           | Install                                                                    |
| -------------- | --------------------------------- | -------------------------------------------------------------------------- |
| `nmap`         | Network port scanner              | `apt install nmap`                                                         |
| `masscan`      | Fast mass port scanner            | `apt install masscan`                                                      |
| `subfinder`    | Passive subdomain enumeration     | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| `amass`        | Subdomain enumeration and mapping | `apt install amass`                                                        |
| `theHarvester` | Email/domain OSINT                | `apt install theharvester`                                                 |
| `sherlock`     | Username search across platforms  | `pip install sherlock-project`                                             |

## Web Exploitation

| Tool           | Purpose                              | Install                                                              |
| -------------- | ------------------------------------ | -------------------------------------------------------------------- |
| Burp Suite Pro | HTTP proxy, scanner, intruder        | [portswigger.net](https://portswigger.net/burp/pro)                  |
| `ffuf`         | Web fuzzing                          | `go install github.com/ffuf/ffuf/v2@latest`                          |
| `sqlmap`       | SQL injection automation             | `apt install sqlmap`                                                 |
| `nuclei`       | Template-based vulnerability scanner | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| `nikto`        | Web vulnerability scanner            | `apt install nikto`                                                  |

## Active Directory & Network Attacks

| Tool                | Purpose                                         | Install                                              |
| ------------------- | ----------------------------------------------- | ---------------------------------------------------- |
| `impacket`          | AD/SMB attack suite (psexec, secretsdump, etc.) | `pip install impacket`                               |
| `bloodhound-python` | BloodHound data collection                      | `pip install bloodhound`                             |
| BloodHound          | AD attack path visualisation                    | [GitHub](https://github.com/BloodHoundAD/BloodHound) |
| `evil-winrm`        | WinRM shell                                     | `gem install evil-winrm`                             |
| `responder`         | LLMNR/NBT-NS poisoning                          | `apt install responder`                              |
| `crackmapexec`      | AD Swiss-army knife                             | `apt install crackmapexec`                           |
| `kerbrute`          | Kerberos user enumeration and bruteforce        | [GitHub](https://github.com/ropnop/kerbrute)         |

## Post-Exploitation & C2

| Tool                                          | Purpose                                      | Install                                          |
| --------------------------------------------- | -------------------------------------------- | ------------------------------------------------ |
| Metasploit                                    | Exploitation and post-exploitation framework | `apt install metasploit-framework`               |
| [Sliver](https://github.com/BishopFox/sliver) | Open-source C2 framework                     | GitHub releases                                  |
| `msfvenom`                                    | Payload generation                           | bundled with Metasploit                          |
| `chisel`                                      | TCP/UDP tunnel over HTTP                     | `go install github.com/jpillora/chisel@latest`   |
| `ligolo-ng`                                   | Tunneling for pivoting                       | [GitHub](https://github.com/nicocha30/ligolo-ng) |

## Privilege Escalation

| Tool       | Purpose                                  | Install                                           |
| ---------- | ---------------------------------------- | ------------------------------------------------- |
| `linpeas`  | Linux privilege escalation enumeration   | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `winpeas`  | Windows privilege escalation enumeration | [GitHub](https://github.com/carlospolop/PEASS-ng) |
| `mimikatz` | Windows credential dumping               | [GitHub](https://github.com/gentilkiwi/mimikatz)  |
| `Rubeus`   | Kerberos manipulation                    | [GitHub](https://github.com/GhostPack/Rubeus)     |

---

## Related Guides

|                               | Guide                                              |
| ----------------------------- | -------------------------------------------------- |
| Defensive tooling             | [Blue Team Tools](BlueTeam-Tools.md)               |
| Run attack labs in containers | [Docker Setup](Docker.md)                          |
| Full tool reference           | [General Security Tools](GeneralSecurity-Tools.md) |
