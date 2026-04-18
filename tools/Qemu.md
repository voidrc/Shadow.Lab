# QEMU/KVM — Virtualization Setup

## What is QEMU/KVM?

QEMU/KVM is a virtualization stack built into the Linux kernel.

Compared to VirtualBox:

|             | QEMU/KVM                                                           |
| ----------- | ------------------------------------------------------------------ |
| Performance | Runs closer to native speed via hardware virtualization            |
| Control     | Networking, snapshots, and storage are configurable at a low level |
| Interface   | CLI-first — managed with `virsh` and `virt-install`                |

> Commands here target Arch and Arch-based distros. Other distros may have different package names.

---

## Step 1 — Install the Virtualization Stack

```bash
sudo pacman -Syu qemu-full virt-manager libvirt dnsmasq ebtables iptables-nft edk2-ovmf virt-install
```

| Package        | Purpose                                      |
| -------------- | -------------------------------------------- |
| `qemu-full`    | Emulator/hypervisor core                     |
| `virt-manager` | GUI frontend for managing VMs                |
| `libvirt`      | Daemon that manages virtualization resources |
| `dnsmasq`      | DHCP and DNS for virtual networks            |
| `iptables-nft` | Firewall rules (required for NAT networking) |
| `edk2-ovmf`    | UEFI firmware support for VMs                |
| `virt-install` | CLI tool for creating VMs                    |

---

## Step 2 — Enable libvirt

Enable and start the daemon:

```bash
sudo systemctl enable --now libvirtd
```

Add your user to the `libvirt` group to manage VMs without `sudo`:

```bash
sudo usermod -aG libvirt $USER
```

**Log out and back in** (or reboot) for the group change to take effect.

Verify the daemon is running:

```bash
virsh --connect qemu:///system list --all
```

Check available virtual networks:

```bash
virsh net-list --all
```

---

## Step 3 — Custom Networks (Optional)

Two network profiles are available depending on your lab needs. You can define one or both.

---

### Option A — NAT (NAT)

VMs get a private internal network. Internet access is routed through the host via NAT.

```bash
sudo vim /tmp/NAT.xml
```

```xml
<network>
  <name>NAT</name>
  <forward mode='nat'/>
  <bridge name='virbr10' stp='on' delay='0'/>
  <domain name='shadow_lab'/>
  <ip address='10.10.10.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.10.10.2' end='10.10.10.200'/>
    </dhcp>
  </ip>
</network>
```

| Setting          | Value                       |
| ---------------- | --------------------------- |
| Network name     | `NAT`                       |
| Bridge interface | `virbr10`                   |
| Internal domain  | `shadow_lab`                |
| Gateway          | `10.10.10.1`                |
| DHCP range       | `10.10.10.2 – 10.10.10.200` |

```bash
sudo virsh net-define /tmp/NAT.xml
sudo virsh net-start NAT
sudo virsh net-autostart NAT
```

---

### Option B — Bridged LAN (LAN)

VMs appear directly on the physical LAN. Useful for accessing VMs from other devices on the network.

> Replace `eth0` with your actual host interface (`ip link` to check).

```bash
sudo vim /tmp/LAN.xml
```

```xml
<network>
  <name>LAN</name>
  <forward mode='bridge'/>
  <bridge name='virbr20'/>
  <ip address='172.16.0.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='172.16.0.15' end='172.16.0.19'/>
    </dhcp>
  </ip>
</network>
```

| Setting          | Value                       |
| ---------------- | --------------------------- |
| Network name     | `LAN`                       |
| Bridge interface | `virbr20`                   |
| Gateway          | `172.16.0.1`                |
| DHCP range       | `172.16.0.15 – 172.16.0.19` |

```bash
sudo virsh net-define /tmp/LAN.xml
sudo virsh net-start LAN
sudo virsh net-autostart LAN
```

---

### Verify

```bash
sudo virsh net-list --all
sudo virsh net-info NAT
sudo virsh net-info LAN
```
