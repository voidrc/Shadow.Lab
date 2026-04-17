# 🔬 Reverse Engineering

> Static and dynamic analysis of compiled binaries. Read what machines read.

---

## Workflow

```
1. file / strings / exiftool → gather initial intel
2. checksec → understand protections
3. Open in Ghidra or IDA → static analysis, understand logic
4. Run under GDB / strace / ltrace → dynamic analysis
5. Patch or script the solution
```

---

## Static Analysis

### Initial Triage
```bash
file binary              # ELF, PE, Mach-O? 32/64-bit?
strings binary           # look for flags, URLs, keys, error messages
strings -n 6 binary      # min string length 6
hexdump -C binary | head -20  # raw hex view
objdump -d binary        # disassemble all sections
objdump -d -M intel binary   # Intel syntax
nm binary                # symbol table (if not stripped)
readelf -a binary        # ELF headers, sections, symbols
```

### Understand the Binary Architecture
```bash
# Check if statically/dynamically linked
ldd binary

# Identify library calls
objdump -d binary | grep "call"
ltrace ./binary          # trace library calls at runtime
```

---

## Ghidra Quick Start

1. **New Project** → Import binary
2. **Auto-analysis** → accept defaults
3. **Symbol Tree** → find `main`, `entry`
4. **Decompiler** → read pseudocode on the right panel
5. Rename variables: right-click → Rename Variable
6. Re-type variables: right-click → Retype Variable
7. Look for comparisons — `strcmp`, `memcmp`, custom loops

### Ghidra Shortcuts
| Key | Action |
|---|---|
| `G` | Go to address |
| `L` | Rename label/variable |
| `T` | Retype variable |
| `F` | Find references to |
| `Ctrl+F` | Search text |
| `Ctrl+Shift+F` | Search memory |

---

## GDB Dynamic Analysis

```bash
gdb ./binary
gdb -q ./binary

# Useful commands
run                      # run binary
run <<< "input"          # run with stdin
break main               # break at main
break *0x401234          # break at address
info functions           # list all functions
disas main               # disassemble main
x/s 0x402000             # examine string at address
x/20wx $rsp              # 20 words at stack pointer
finish                   # run to end of function
watch *(int*)0x602010    # watchpoint on memory
```

---

## Anti-Debugging Techniques & Bypasses

### ptrace Check
```c
// Common anti-debug: call ptrace on self
if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) exit(1);
```
**Bypass:** Patch the conditional jump after the ptrace call (je → jne), or hook ptrace with LD_PRELOAD.

### Timing Checks
```c
// Detect slow execution (debugger overhead)
clock_gettime(), gettimeofday()
```
**Bypass:** NOP the check, or set a breakpoint after the timing block.

### String Obfuscation
- XOR-encoded strings decoded at runtime
- Look for a decode loop → set breakpoint after it → read string from memory

### VM/Sandbox Detection
```bash
# Check CPUID, /proc/cpuinfo, MAC address prefix, hostname
# Usually safe to patch or ignore in CTFs
```

---

## Crackmes / License Check Pattern

Most basic reversing challenges verify a password or serial.

```
1. Find the comparison function (strcmp, memcmp, custom)
2. Set a breakpoint just before comparison
3. Read both values from registers/memory
4. Derive the correct input, or patch the jump
```

### Patching with GDB
```bash
# NOP out a conditional jump (replace bytes with 0x90)
set {unsigned char[2]}0x401234 = {0x90, 0x90}
```

### Patching with Python/radare2
```bash
r2 -w binary          # open in write mode
s 0x401234            # seek to address
pd 3                  # disassemble 3 instructions
wa nop                # write nop at current address
```

---

## Scripting Reversing Tasks

### Python — XOR Decode
```python
data = bytes([0x41, 0x2b, 0x3f, 0x1a])  # encoded bytes
key  = 0x42
decoded = bytes([b ^ key for b in data])
print(decoded)
```

### Python — Automated GDB (with pwntools)
```python
from pwn import *

p = process('./binary')
gdb.attach(p, gdbscript='''
break *0x401234
continue
''')
p.interactive()
```

### angr — Symbolic Execution
```python
import angr

proj = angr.Project('./binary', auto_load_libs=False)
state = proj.factory.entry_state()
simgr = proj.factory.simulation_manager(state)

# Find path that reaches success address, avoid failure
simgr.explore(find=0x401234, avoid=0x401567)

if simgr.found:
    print(simgr.found[0].posix.dumps(0))  # stdin that leads to success
```

---

## Windows Binaries (PE)

```bash
# On Linux
wine binary.exe           # run Windows binaries
strings binary.exe        # same as ELF

# PE analysis tools
pestudio                  # static PE analysis (Windows)
PEiD / Detect-It-Easy    # packer/compiler identification
x64dbg / x32dbg          # Windows debugger
```

---

## Packing / Obfuscation

```bash
# Detect packer
file binary
strings binary | grep -i "upx\|packer"
Detect-It-Easy (DIE)

# Unpack UPX
upx -d binary

# Manual unpacking: run until OEP (Original Entry Point), dump process
```

---

## Common Challenge Types

| Type | Approach |
|---|---|
| Password check | Find strcmp/memcmp, read args at breakpoint |
| Serial / keygen | Understand the algorithm, reverse the math |
| Obfuscated string | Find decode loop, breakpoint after it |
| Flag XOR'd | Find key in binary, XOR with ciphertext |
| Packed binary | Detect & unpack, then analyze |
| VM / bytecode interpreter | Map opcodes, write disassembler |

---

## Resources

- [Ghidra](https://ghidra-sre.org/) — free NSA decompiler
- [crackmes.one](https://crackmes.one/) — reversing challenges by difficulty
- [malware.wtf](https://malware.wtf/) — malware reversing challenges
- [angr docs](https://docs.angr.io/) — symbolic execution framework
- [OpenSecurityTraining2](https://p.ost2.fyi/) — deep RE courses
- [Reverse Engineering for Beginners (free book)](https://beginners.re/)
