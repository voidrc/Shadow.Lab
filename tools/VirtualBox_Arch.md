# VirtualBox on Arch

Setup guide for Arch and Arch-based distros (Manjaro, EndeavourOS, CachyOS, etc.).

---

## Step 1 — Install VirtualBox

For the stock Arch kernel:

```bash
sudo pacman -S virtualbox virtualbox-host-modules-arch
```

For a custom or non-stock kernel (e.g. linux-zen, linux-cachyos):

```bash
sudo pacman -S virtualbox virtualbox-host-dkms dkms linux-headers
```

> Use `uname -r` to check your running kernel if unsure.

---

## Step 2 — Load Kernel Modules

Load immediately:

```bash
sudo modprobe vboxdrv
```

Persist across reboots:

```bash
echo -e "vboxdrv\nvboxnetflt\nvboxnetadp\nvboxpci" | sudo tee /etc/modules-load.d/virtualbox.conf
```

---

## Step 3 — Add User to vboxusers

```bash
sudo usermod -aG vboxusers $USER
```

**Log out and back in** — group membership changes don't apply to the current session.

---

## Step 4 — Verify Installation

```bash
VBoxManage --version
```

Launch the GUI:

```bash
virtualbox
```

---

## Step 5 — Extension Pack (Optional)

Adds USB 2/3, RDP, NVMe, and disk encryption support.

Download the pack matching your VirtualBox version from the [official downloads page](https://www.virtualbox.org/wiki/Downloads), then install:

```bash
sudo VBoxManage extpack install Oracle_VirtualBox_Extension_Pack*.vbox-extpack
```

---

## Common Arch Quirks

| Issue | Fix |
|-------|-----|
| Kernel mismatch after update | `sudo dkms autoinstall` |
| Modules blocked at boot | Disable Secure Boot or sign the modules |
| UI glitches on Wayland | Launch under X11: `DISPLAY=:0 virtualbox` |

---

## Optional — Host-Only Networking

```bash
sudo vboxmanage hostonlyif create
```
