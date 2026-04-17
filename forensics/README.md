# 🔍 Forensics

> Recover, reconstruct, and reveal. Forensics covers file analysis, memory dumps, network captures, and log examination.

---

## Initial Triage

```bash
file suspect_file          # what type is it really?
strings suspect_file       # printable ASCII strings
xxd suspect_file | head -20  # magic bytes / raw hex
exiftool suspect_file      # metadata
binwalk suspect_file       # embedded files
```

---

## File Types & Magic Bytes

Common magic bytes (file signatures):

| File Type | Magic Bytes (hex) | ASCII |
|---|---|---|
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `‰PNG....` |
| JPEG | `FF D8 FF` | `ÿØÿ` |
| GIF | `47 49 46 38` | `GIF8` |
| PDF | `25 50 44 46` | `%PDF` |
| ZIP | `50 4B 03 04` | `PK..` |
| ELF | `7F 45 4C 46` | `.ELF` |
| PE (Windows) | `4D 5A` | `MZ` |
| RAR | `52 61 72 21` | `Rar!` |
| 7-Zip | `37 7A BC AF` | `7z..` |

```bash
# Restore a renamed file by its magic bytes
xxd mystery.dat | head -3
# Then rename or use appropriate tool
```

---

## File Carving

```bash
# Extract embedded files
binwalk -e archive.bin
binwalk --dd='.*' archive.bin     # extract everything

# Alternative carvers
foremost -t all -i suspect.img -o output/
scalpel suspect.img -o output/

# Carve specific type from raw image
photorec image.dd          # interactive, recovers many types
```

---

## Archive & Compression

```bash
# Extract various formats
unzip archive.zip
7z x archive.7z
tar -xvf archive.tar.gz
gunzip file.gz
bzip2 -d file.bz2

# Crack password-protected ZIP
zip2john protected.zip > hash.txt
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

# Or hashcat
zip2john protected.zip > zip.hash
hashcat -m 13600 zip.hash rockyou.txt
```

---

## Image Forensics

```bash
# Metadata
exiftool image.jpg

# Check for appended data after image EOF
xxd image.jpg | tail -20

# Steganography check → see stego guide
# Hidden zip appended to JPEG (polyglot)
binwalk image.jpg
unzip image.jpg -d output/
```

### JPEG Structure
```
FFD8 = SOI (Start of Image)
FFD9 = EOI (End of Image)
# Anything after FFD9 is appended data — extract it
```

---

## Network Forensics (PCAP Analysis)

### Wireshark

```
# Open PCAP
wireshark capture.pcap

# Useful filters
tcp                      # only TCP
http                     # HTTP traffic
http.request             # HTTP requests
dns                      # DNS queries
ip.addr == 192.168.1.1   # traffic to/from IP
tcp.stream eq 0          # follow TCP stream 0
frame contains "flag"    # search packet content

# Follow a stream: Right-click packet → Follow → TCP Stream
# Export HTTP objects: File → Export Objects → HTTP
```

### tshark (CLI)
```bash
# List all streams
tshark -r capture.pcap -z conv,tcp

# Extract HTTP URIs
tshark -r capture.pcap -Y http.request -T fields -e http.request.uri

# Extract all files via HTTP
tshark -r capture.pcap --export-objects http,output_dir/

# Decode specific stream
tshark -r capture.pcap -q -z follow,tcp,ascii,0

# Find credentials in HTTP Basic Auth
tshark -r capture.pcap -Y 'http.authorization' -T fields -e http.authorization
```

### DNS Exfiltration
```bash
# Look for unusually long subdomain queries → data encoded in DNS
tshark -r capture.pcap -Y dns.qry.type==1 -T fields -e dns.qry.name | sort -u

# Decode base32/hex from subdomain labels
echo "aGVsbG8=" | base64 -d
```

---

## Memory Forensics (Volatility 3)

```bash
# Install
pip install volatility3

# Basic usage
python3 vol.py -f memory.dmp <plugin>

# OS detection
python3 vol.py -f memory.dmp windows.info
python3 vol.py -f memory.dmp linux.info

# Common Windows plugins
windows.pslist           # running processes
windows.pstree           # process tree
windows.cmdline          # command line arguments
windows.filescan         # scan for file objects
windows.dumpfiles        # dump a file from memory
windows.hashdump         # dump NTLM hashes
windows.netscan          # network connections
windows.malfind          # find injected code

# Dump a specific process
python3 vol.py -f memory.dmp windows.dumpfiles --pid 1234

# Search for a string in memory
python3 vol.py -f memory.dmp windows.strings --strings-file strings.txt
strings memory.dmp | grep -i "flag{"
```

---

## Disk Image Forensics

```bash
# Mount a raw disk image
sudo mount -o loop,ro disk.img /mnt/forensics

# List partitions
fdisk -l disk.img
mmls disk.img            # sleuthkit

# Browse filesystem
autopsy                  # GUI tool (starts web server)

# Recover deleted files
photorec disk.img
testdisk disk.img        # recover partition table / lost files

# Timeline
fls -r -m / disk.img > bodyfile.txt
mactime -b bodyfile.txt > timeline.txt
```

---

## Log Analysis

```bash
# Linux auth logs
grep "Failed password" /var/log/auth.log
grep "Accepted password" /var/log/auth.log

# Apache/Nginx access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head  # top IPs
grep "POST" access.log | grep -v "200"

# Windows Event logs (on Linux)
python-evtx viewer or:
evtxdump.py Security.evtx | grep -i "EventID>4625"   # failed logins
EventID 4624 = Logon success
EventID 4625 = Logon failure
EventID 4688 = Process creation
```

---

## Useful Python Snippets

```python
# Read raw bytes
with open('file.bin', 'rb') as f:
    data = f.read()

# Find all occurrences of pattern
import re
matches = re.findall(b'flag\{.*?\}', data)

# XOR all bytes with key
key = 0x42
decoded = bytes([b ^ key for b in data])
```

---

## Resources

- [Volatility 3 docs](https://volatility3.readthedocs.io/)
- [Wireshark display filter reference](https://www.wireshark.org/docs/dfref/)
- [CTF 101 — Forensics](https://ctf101.org/forensics/overview/)
- [Digital Corpora](https://digitalcorpora.org/) — sample forensics images
- [13Cubed YouTube](https://www.youtube.com/@13Cubed) — forensics walkthroughs
