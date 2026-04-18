# VM Quality of Life

Quality of life tips for VM users.

---

## Kali

### GRUB Timeout

No need for a boot countdown inside a VM — disable it:

```bash
sudo vim /etc/default/grub
```

```ini
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
```

Apply the change:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### Auto Login

Already authenticated on the host — skip the login screen:

```bash
sudo vim /etc/lightdm/lightdm.conf
```

```ini
[Seat:*]
autologin-user=<login_user>
autologin-user-timeout=0
autologin-session=xfce
```

Add your user to the autologin group:

```bash
sudo groupadd -r autologin 2>/dev/null
sudo gpasswd -a $USER autologin
```

### Screen Lock / Idle Timeout

Host already locks — no need to double-lock inside the VM too.

Disable the soft lock layer:

- **Settings → Power Manager**
- **Settings → Xfce Screensaver**

### Kali Tweaks

For everything else, open **Kali Tweaks**.

---

## What to Read Next

| You want to...           | Go here                             |
| ------------------------ | ----------------------------------- |
| Install your first tools | [Starter Tools](Starter-Tools.md)   |
| Tune your Arch host      | [Arch Quality of Life](Arch-QOL.md) |
