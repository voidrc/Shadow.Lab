# 👁️ OSINT

> Open Source Intelligence — gather information from publicly available sources.

---

## OSINT Mindset

1. Start with what you know (name, username, email, image, domain)
2. Expand outward — every piece of info leads to the next
3. Document everything — links, screenshots, timestamps
4. Stay passive — do not interact with or alert the target

---

## Username & Identity

```bash
# Search username across many platforms
sherlock username
maigret username

# Manual checks
# GitHub: https://github.com/username
# Twitter/X: https://twitter.com/username
# Instagram: https://instagram.com/username
# Reddit: https://reddit.com/u/username
# LinkedIn: search by name
```

---

## Email Investigation

```bash
# Validate if email exists (without sending)
holehe email@example.com     # checks which sites the email is registered on

# WHOIS lookup
whois example.com

# Email header analysis (paste into)
# https://mxtoolbox.com/EmailHeaders.aspx
# https://toolbox.googleapps.com/apps/messageheader/

# Find emails for a domain
theHarvester -d example.com -b all
```

---

## Domain & IP Recon

```bash
# WHOIS
whois example.com
whois 1.2.3.4

# DNS records
nslookup example.com
dig example.com ANY +noall +answer
dig @8.8.8.8 example.com MX

# Reverse DNS
dig -x 1.2.3.4

# Subdomain discovery (passive)
subfinder -d example.com
amass enum -passive -d example.com
# Online: https://dnsdumpster.com, https://crt.sh

# Certificate transparency logs
curl "https://crt.sh/?q=%.example.com&output=json" | python3 -m json.tool

# Shodan (indexed internet devices)
shodan host 1.2.3.4         # requires API key
# Online: https://shodan.io

# Check historical DNS/WHOIS
# https://securitytrails.com
# https://viewdns.info
```

---

## Web & Content

```bash
# Wayback Machine — archived versions of websites
# https://web.archive.org
waybackurls example.com     # extract all archived URLs

# Google dorking
site:example.com filetype:pdf
site:example.com inurl:admin
site:example.com "confidential"
"@example.com" site:pastebin.com
intitle:"index of" "backup"

# Find cached pages
cache:example.com/page

# GitHub dorking
# https://github.com/search
org:example filename:.env
org:example "password"
org:example "api_key"
```

---

## Image & Geolocation

```bash
# Reverse image search
# https://images.google.com  (drag & drop)
# https://yandex.com/images   (often better for faces/locations)
# https://tineye.com

# Extract image metadata
exiftool image.jpg           # GPS coords, camera model, software, dates

# Convert GPS coords
# DMS: 40°41'21.4"N 74°2'40.2"W
# DD: 40.689278, -74.044500
# → Paste in Google Maps or maps.google.com

# Geolocate from clues in the image
# - Street signs, language
# - Architecture, vegetation
# - Sun angle / shadows
# - GeoGuessr practice helps
```

---

## Social Media Analysis

```bash
# Twitter/X advanced search
# https://twitter.com/search-advanced
# from:username, to:username, geocode:lat,lon,radius, since:2023-01-01

# Facebook Graph Search (still partially works):
# https://www.facebook.com/search/people/?q=John+Doe

# Instagram location tags, tagged photos

# LinkedIn — company employees, job history
# Google dork: site:linkedin.com/in "example company" "engineer"
```

---

## Document & File Metadata

```bash
# PDF metadata
exiftool document.pdf
pdfinfo document.pdf
strings document.pdf | grep -i "author\|creator\|producer"

# Office documents (DOCX/XLSX)
unzip document.docx -d doc_extracted
cat doc_extracted/docProps/core.xml    # author, last modified by, dates

# Image metadata
exiftool image.jpg
# Look for: GPS coords, camera serial, software used, original date
```

---

## Breach Data & Credential Lookup

```bash
# Check if email appears in known breaches
# https://haveibeenpwned.com
# https://dehashed.com  (paid, more detail)
# https://intelx.io

# Paste sites
# https://pastebin.com
# https://paste.ee
# https://ghostbin.com
# Search: site:pastebin.com "target name"
```

---

## People Search

```
# USA
https://www.whitepages.com
https://www.spokeo.com
https://pipl.com

# Public records
https://www.publicrecords.com
County court records, property records, voter registration

# LinkedIn Sales Navigator (profile URL trick)
https://linkedin.com/in/username
```

---

## OSINT Framework

A categorized list of OSINT tools:
- [OSINT Framework](https://osintframework.com) — visual mind-map of tools by category

---

## CTF-Specific OSINT Tips

- Read challenge text carefully — usernames, dates, locations are often direct clues
- Check challenge author's social media for hints
- Reverse search profile pictures
- Check metadata on all provided files
- Try the Wayback Machine on any given URL
- Look at the page source and HTTP headers of challenge websites
- If given a real-world location clue, use Google Street View

---

## Resources

- [OSINT Framework](https://osintframework.com)
- [Bellingcat's Online Investigation Toolkit](https://docs.google.com/spreadsheets/d/18rtqh8EG2q1xBo2cLNyhIDuK9jrPGwYr9DI2UncoqJQ/)
- [IntelTechniques Tools](https://inteltechniques.com/tools/)
- [Trace Labs](https://www.tracelabs.org/) — OSINT CTFs with real-world missing persons cases
- [Michael Bazzell's OSINT Podcast](https://inteltechniques.com/podcast.html)
