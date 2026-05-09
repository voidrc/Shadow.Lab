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

VMs attach directly to the physical LAN via an unmanaged switch. No DHCP is available on the network — every VM needs a static IP configured inside the guest OS.

Reserved IP range for QEMU VMs: **`172.16.0.15 – 172.16.0.19`**

> Replace `eth0` with your actual host interface (`ip link` to check).

First, bridge the physical interface on the host:

```bash
sudo ip link add virbr20 type bridge
sudo ip link set eth0 master virbr20
sudo ip link set virbr20 up
```

To persist across reboots, add the bridge to your network manager config (e.g. systemd-networkd or NetworkManager).

Then define the libvirt network:

```bash
sudo vim /tmp/LAN.xml
```

```xml
<network>
  <name>LAN</name>
  <forward mode='bridge'/>
  <bridge name='virbr20'/>
</network>
```

| Setting          | Value                       |
| ---------------- | --------------------------- |
| Network name     | `LAN`                       |
| Bridge interface | `virbr20`                   |
| Reserved range   | `172.16.0.15 – 172.16.0.19` |
| Gateway          | set on your router/host     |

```bash
sudo virsh net-define /tmp/LAN.xml
sudo virsh net-start LAN
sudo virsh net-autostart LAN
```

#### Setting a Static IP Inside a VM

After creating a VM on the `LAN` network, configure the static IP inside the guest. Using `nmcli`:

```bash
# Run inside the VM guest
nmcli con mod "Wired connection 1" \
  ipv4.method manual \
  ipv4.addresses 172.16.0.15/24 \
  ipv4.gateway 172.16.0.1 \
  ipv4.dns "1.1.1.1 8.8.8.8"
nmcli con up "Wired connection 1"
```

Increment the last octet (`172.16.0.15`, `.16`, `.17`…) for each new VM. Keep a note of which IP is assigned to which VM to avoid conflicts within the reserved range.

---

### Verify

```bash
sudo virsh net-list --all
sudo virsh net-info NAT
sudo virsh net-info LAN
```

---

## What to Read Next

| You want to...                | Go here                                  |
| ----------------------------- | ---------------------------------------- |
| Prefer a GUI-based hypervisor | [VirtualBox on Arch](VirtualBox_Arch.md) |
| Tune your VM after setup      | [VM Quality of Life](QOL-VM.md)          |
| Browse the full security toolkit | [General Security Tools](GeneralSecurity-Tools.md) |
