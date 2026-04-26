# Docker

Setup guide for Arch and Arch-based distros.

---

## Step 1 — Install Docker

```bash
sudo pacman -S docker docker-compose
```

---

## Step 2 — Enable and Start the Daemon

```bash
sudo systemctl enable --now docker
```

Verify it is running:

```bash
sudo systemctl status docker
```

---

## Step 3 — Add User to docker Group

Running Docker without `sudo` requires your user to be in the `docker` group:

```bash
sudo usermod -aG docker $USER
```

**Log out and back in** for the group change to take effect.

Verify:

```bash
docker run --rm hello-world
```

---

## Step 4 — Install lazydocker

lazydocker is a terminal UI for managing containers, images, volumes, and logs.

Via AUR (recommended):

```bash
yay -S lazydocker
# or
paru -S lazydocker
```

Via the official install script (no AUR helper required):

```bash
curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
```

The binary is placed in `~/.local/bin/lazydocker`. Make sure `~/.local/bin` is in your `$PATH`.

---

## Step 5 — Launch lazydocker

```bash
lazydocker
```

Or alias it for convenience:

```bash
echo "alias lzd='lazydocker'" >> ~/.zshrc
source ~/.zshrc
```

---

## Key Bindings

| Key       | Action                              |
| --------- | ----------------------------------- |
| `x`       | Open command menu for selected item |
| `e`       | Open config/compose file in editor  |
| `[` / `]` | Switch panels                       |
| `enter`   | View logs / inspect                 |
| `d`       | Remove container or image           |
| `u`       | Pull latest image                   |
| `R`       | Restart container                   |
| `q`       | Quit                                |

---

## Notes

- The `docker` group grants root-equivalent access to the host. Only add trusted users.
- `docker-compose` is included in the `docker` package on Arch (v2 plugin, use `docker compose`).
- lazydocker reads the Docker socket at `/var/run/docker.sock` — no extra config needed.

---

## What to Read Next

| You want to...                 | Go here                             |
| ------------------------------ | ----------------------------------- |
| Spin up vulnerable lab targets | [Targets](Targets.md)               |
| Tune your Arch host            | [Arch Quality of Life](Arch-QOL.md) |
| Encrypt sensitive data         | [GPG](GPG.md)                       |
| Back up your lab               | [Backups](BackUps.md)               |
