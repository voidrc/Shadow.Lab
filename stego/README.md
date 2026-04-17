# 🖼️ Steganography

> Data hidden in plain sight — inside images, audio, video, and text.

---

## Initial Checks (Do These First)

```bash
file image.png           # verify actual file type
strings image.png        # look for readable text/flags
exiftool image.png       # check all metadata fields
xxd image.png | tail -20 # check for appended data after EOF
binwalk image.png        # check for embedded files
binwalk -e image.png     # extract embedded files
```

---

## Image Steganography

### Colour & Bit Analysis

```bash
# stegsolve — visual channel & LSB analysis (GUI)
java -jar stegsolve.jar

# zsteg — detects LSB stego in PNG and BMP
zsteg image.png          # auto-detect
zsteg -a image.png       # try all methods
zsteg image.png -E "b1,r,lsb,xy"   # extract specific channel

# stegoveritas — run many checks at once
stegoveritas image.png
```

### Hidden Files Inside Images

```bash
# Check for ZIP/RAR/other files appended after JPEG EOI (FFD9)
xxd image.jpg | grep -A 2 "ff d9"
# Or just try:
unzip image.jpg -d output/
7z x image.jpg

# binwalk extraction
binwalk -e image.png
```

### steghide (JPEG / BMP)
```bash
# Extract without password
steghide extract -sf image.jpg

# Extract with password
steghide extract -sf image.jpg -p "password"

# Embed (for understanding)
steghide embed -cf image.jpg -sf secret.txt -p "password"

# Check if data is embedded
steghide info image.jpg
```

### outguess (JPEG)
```bash
outguess -r image.jpg output.txt
outguess -k "password" -r image.jpg output.txt
```

### OpenStego (PNG)
- GUI tool — [openstego.com](https://www.openstego.com/)
- Also handles watermarking

---

## LSB (Least Significant Bit) Stego

The most common technique: hides data in the lowest bits of pixel colour values.

```python
# Manual LSB extraction (PNG, channel R)
from PIL import Image

img = Image.open('image.png')
pixels = list(img.getdata())

bits = ''
for pixel in pixels:
    for channel in pixel[:3]:   # R, G, B
        bits += str(channel & 1)

# Convert bits to bytes
chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
print(''.join(chars)[:100])
```

```bash
# Use zsteg for quick LSB extraction
zsteg -a image.png

# Use stegsolve → Data Extract → select LSB channels
```

---

## Audio Steganography

### Spectrogram Analysis
```bash
# Open in Audacity → View → Plot Spectrum
# Or use sox / python
sox audio.wav -n spectrogram -o spectrogram.png
# Open spectrogram.png and look for text/morse/QR patterns

# Online: https://www.dcode.fr/spectral-analysis
```

### MP3 / WAV Stego Tools
```bash
# mp3stego
MP3Stego -x output.txt stego.mp3

# steghide also works on WAV/AU
steghide extract -sf audio.wav

# OpenPuff (Windows) — supports many formats
```

### Morse Code in Audio
```bash
# Listen to audio — short/long beeps = morse
# Use: https://morsecode.world/international/decoder/audio-decoder-adaptive.html
```

### DTMF Tones
```bash
# Touch-tone phone numbers encoded in audio
multimon-ng -t wav -a DTMF audio.wav
```

---

## Text / Whitespace Steganography

```bash
# Snow — whitespace stego (tabs/spaces at line endings)
stegsnow -C stego.txt

# Zero-width characters (Unicode steganography)
# Look for: U+200B (ZWSP), U+FEFF (BOM), U+200D (ZWJ)
cat -A stego.txt         # show non-printing chars
hexdump -C stego.txt | grep "e2 80"   # zero-width in UTF-8

# Unicode stego decoder:
# https://330k.github.io/misc_tools/unicode_steganography.html
```

---

## Video Steganography

```bash
# Extract all frames
ffmpeg -i video.mp4 frames/frame_%04d.png

# Check audio track separately
ffmpeg -i video.mp4 -vn audio.wav

# Look at first and last frames — sometimes flag is there
# Analyse frames with zsteg / stegsolve
```

---

## PDF & Document Stego

```bash
# Highlight all text in PDF (sometimes white-on-white text)
# Extract all text
pdftotext file.pdf -

# Check all layers / metadata
exiftool file.pdf
strings file.pdf | grep -i flag

# Peepdf (Python tool for PDF analysis)
peepdf -i file.pdf
```

---

## Colour-Based Stego

### RGBA Alpha Channel
```python
from PIL import Image

img = Image.open('image.png').convert('RGBA')
data = img.getdata()
alpha_vals = [p[3] for p in data]   # extract alpha channel
print(bytes(alpha_vals))
```

### Palette-Based (GIF / PNG)
```bash
# Check palette in GIMP or:
python3 -c "
from PIL import Image
img = Image.open('image.gif')
print(img.getpalette())
"
```

---

## Common Steganography Tools Summary

| Tool | Type | Notes |
|---|---|---|
| `steghide` | JPEG, BMP, WAV | Supports passwords |
| `zsteg` | PNG, BMP | LSB, multi-channel |
| `stegsolve` | PNG, BMP, GIF | Visual analysis |
| `binwalk` | Any | File carving |
| `outguess` | JPEG | Statistical stego |
| `sox` | Audio | Spectrogram |
| `stegoveritas` | Multi | Automated multi-check |
| OpenStego | PNG | GUI |

---

## Quick Checklist

```
[ ] Check metadata (exiftool)
[ ] Look for appended data (xxd tail, unzip)
[ ] Run binwalk for embedded files
[ ] Try zsteg -a (PNG/BMP)
[ ] Open stegsolve and browse bit planes
[ ] Try steghide extract (no password, then common wordlist)
[ ] For audio: check spectrogram
[ ] For text: check for whitespace / zero-width chars
[ ] Check all colour channels individually
[ ] Check alpha channel
```

---

## Resources

- [CTF 101 — Steganography](https://ctf101.org/forensics/what-is-stegonagraphy/)
- [StegOnline](https://stegonline.georgeom.net/) — browser-based stego analysis
- [Aperi'Solve](https://www.aperisolve.com/) — online stego multi-tool
- [dcode.fr stego tools](https://www.dcode.fr/steganography)
- [zsteg GitHub](https://github.com/zed-0xff/zsteg)
