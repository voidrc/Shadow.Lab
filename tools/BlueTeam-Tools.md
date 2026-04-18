### SIEM & Log Analysis

> **Previous:** [General Security Tools](GeneralSecurity-Tools.md)

| Tool                                                      | Purpose                                         | Install                                           |
| --------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| [Elastic Stack (ELK)](https://www.elastic.co)             | Log ingestion, search, and visualisation        | Docker / APT                                      |
| [Splunk Free](https://www.splunk.com/en_us/download.html) | SIEM with 500MB/day free tier                   | Installer                                         |
| [Wazuh](https://wazuh.com)                                | Open-source SIEM + HIDS                         | [Install guide](https://documentation.wazuh.com/) |
| `sigma`                                                   | Convert generic detection rules to SIEM queries | `pip install sigma-cli`                           |

### Endpoint Detection & Forensics

| Tool                                                                      | Purpose                                            | Install                                 |
| ------------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------- |
| [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) | Detailed Windows event logging                     | Windows                                 |
| [Velociraptor](https://github.com/Velocidex/velociraptor)                 | DFIR and endpoint monitoring                       | GitHub releases                         |
| [Volatility 3](https://github.com/volatilityfoundation/volatility3)       | Memory forensics                                   | `pip install volatility3`               |
| [Eric Zimmerman Tools](https://ericzimmerman.github.io)                   | Windows forensics utilities (PECmd, MFTECmd, etc.) | Windows                                 |
| `autopsy`                                                                 | Digital forensics GUI                              | [autopsy.com](https://www.autopsy.com/) |

### Network Monitoring & Analysis

| Tool                            | Purpose                              | Install                 |
| ------------------------------- | ------------------------------------ | ----------------------- |
| [Zeek (Bro)](https://zeek.org)  | Network traffic analysis and logging | `apt install zeek`      |
| [Suricata](https://suricata.io) | Network IDS/IPS                      | `apt install suricata`  |
| Wireshark / `tshark`            | PCAP analysis                        | `apt install wireshark` |
| `zeek-cut`                      | Zeek log field extractor             | bundled with Zeek       |

### Malware Analysis

| Tool                                               | Purpose                                 | Install                                 |
| -------------------------------------------------- | --------------------------------------- | --------------------------------------- |
| [REMnux](https://remnux.org)                       | Linux malware analysis distro           | VM download                             |
| [FlareVM](https://github.com/mandiant/flare-vm)    | Windows malware analysis toolkit        | Windows setup script                    |
| `FLOSS`                                            | Extract obfuscated strings from malware | `pip install flare-floss`               |
| `pestudio`                                         | PE file static analysis                 | [winitor.com](https://www.winitor.com/) |
| `YARA`                                             | Pattern-matching for malware detection  | `apt install yara`                      |
| [Any.run](https://app.any.run)                     | Interactive online sandbox              | Browser                                 |
| [Hybrid-Analysis](https://www.hybrid-analysis.com) | Automated online sandbox                | Browser                                 |

### Threat Intelligence

| Tool                                 | Purpose                       | Install                                                 |
| ------------------------------------ | ----------------------------- | ------------------------------------------------------- |
| [MISP](https://www.misp-project.org) | Threat intel sharing platform | [Install guide](https://www.misp-project.org/download/) |
| [OpenCTI](https://www.opencti.io)    | Threat intel management       | Docker                                                  |

---

## Related Guides

|                            | Guide                                              |
| -------------------------- | -------------------------------------------------- |
| Offensive tooling          | [Red Team Tools](RedTeam-Tools.md)                 |
| Run services in containers | [Docker Setup](Docker.md)                          |
| Full tool reference        | [General Security Tools](GeneralSecurity-Tools.md) |
