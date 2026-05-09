# Quality of Life — Arch / Arch-based

Practical setup tips for daily use on Arch and Arch-based distros.

---

## Static IP (NetworkManager)

Identify the network interface:

```bash
nmcli device
```

Edit the connection (replace `enp108s0` with your interface):

```bash
nmcli connection edit enp108s0
```

Inside the editor:

```
set ipv4.method manual
set ipv4.addresses 172.16.0.11/24
set ipv4.gateway 172.16.0.1
set ipv4.dns "1.1.1.1 8.8.8.8"
save
quit
```

Activate:

```bash
nmcli connection up enp108s0
```

Verify:

```bash
ip addr show enp108s0
```

---

## SSH Setup

**Goal:** secure, passwordless SSH login using key authentication.

### Install and Enable

```bash
sudo pacman -S openssh
sudo systemctl enable --now sshd
```

Verify the service is running:

```bash
sudo systemctl status sshd
ss -tlnp | grep :22
```

### Copy Public Key to Server

```bash
ssh-copy-id USER@IP
```

Enter the password once. The key is installed into `~/.ssh/authorized_keys` on the server.

### Test Passwordless Login

```bash
ssh USER@IP
```

### Disable Password Authentication

Only do this **after confirming key login works**.

```bash
sudo vim /etc/ssh/sshd_config
```

```
PasswordAuthentication no
PubkeyAuthentication yes
```

```bash
sudo systemctl restart sshd
```

### SSH Host Alias

```bash
vim ~/.ssh/config
```

```
Host SERVER
    HostName IP
    User USER
    IdentityFile ~/.ssh/id_ed25519
```

Connect with:

```bash
ssh SERVER
```

---

## Move Home Directories to a Separate Drive

Useful for offloading large directories (Git, Media, etc.) to a secondary SSD.

### Format the Drive

```bash
sudo mkfs.btrfs -f /dev/sdX
```

### Mount

```bash
sudo mkdir -p /media/$USER
sudo mount /dev/sdX /media/$USER
sudo chown $USER:$USER /media/$USER
```

### Create Directories

```bash
mkdir /media/$USER/{Documents,Git,Music,Pictures,Videos}
```

### Copy Data

```bash
sudo rsync -avh --progress ~/Documents/ /media/$USER/Documents/
sudo rsync -avh --progress ~/Git/       /media/$USER/Git/
sudo rsync -avh --progress ~/Music/     /media/$USER/Music/
sudo rsync -avh --progress ~/Pictures/  /media/$USER/Pictures/
sudo rsync -avh --progress ~/Videos/    /media/$USER/Videos/
```

> Verify the data before deleting originals.

### Remove Old Directories

```bash
rm -rf ~/Documents ~/Git ~/Music ~/Pictures ~/Videos
```

### Symlink Back

```bash
ln -s /media/$USER/Documents ~/Documents
ln -s /media/$USER/Git       ~/Git
ln -s /media/$USER/Music     ~/Music
ln -s /media/$USER/Pictures  ~/Pictures
ln -s /media/$USER/Videos    ~/Videos
```

### Persist in fstab

Get the drive UUID:

```bash
lsblk -f /dev/sdX
```

Add to `/etc/fstab`:

```
UUID=<UUID>  /media/<youruser>  btrfs  defaults,noatime,compress=zstd  0  2
```

> Consider adding a Snapper config for the mount point as a safety net.

---

## Zoxide

A smarter `cd` that remembers your most visited directories — stop typing full paths.

### Install and Setup

```bash
sudo pacman -S zoxide
```

Add to `~/.zshrc`:

```bash
eval "$(zoxide init zsh)"
```

Reload:

```bash
source ~/.zshrc
```

### Usage

| Command       | Action                                                   |
| ------------- | -------------------------------------------------------- |
| `z <keyword>` | Jump to the best match for `<keyword>` (e.g., `z proj`) |
| `zi`          | Interactive fuzzy picker (list all frequent dirs)        |
| `z foo bar`   | Jump to a dir matching both "foo" and "bar"              |
| `z -i`        | Interactive mode (manual selection)                      |

> The more you use it, the smarter it gets — it learns your habits.

---

## Neovim Configuration

### Quick Setup with LazyVim

Easiest way to get a functional editor with plugins and themes pre-configured:

```bash
# Backup old config
mv ~/.config/nvim ~/.config/nvim.bak
# Clone LazyVim starter
git clone https://github.com/LazyVim/starter ~/.config/nvim
# Remove the .git folder
rm -rf ~/.config/nvim/.git
```

### Tokyo Night Theme (Manual)

Add to `~/.config/nvim/lua/plugins/colorscheme.lua`:

```lua
return {
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      style = "storm", -- "night", "day", or "storm" (best for Hyprland)
      transparent = true, -- required for Hyprland blur
      styles = {
        comments = { italic = true },
        keywords = { italic = true },
        functions = {},
        variables = {},
      },
      day_brightness = 0.3,
      dim_inactive = false,
      lualine_bold = false,
      on_highlights = function(hl, c)
        hl.CursorLine = { bg = "#24283b" }
      end,
    },
    config = function(_, opts)
      require("tokyonight").setup(opts)
      vim.cmd.colorscheme("tokyonight")
    end,
  },
}
```

> Requires a **Nerd Font** installed (e.g., `JetBrainsMono Nerd Font`) for icons to render correctly.

---

## What to Read Next

| You want to...            | Go here                         |
| ------------------------- | ------------------------------- |
| Encrypt files and backups | [GPG](GPG.md)                   |
| Back up your setup        | [Backups](BackUps.md)           |
| Tune your VM              | [VM Quality of Life](QOL-VM.md) |
