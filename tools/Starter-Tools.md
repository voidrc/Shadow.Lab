# Starter Tools

> **Previous:** [Lab Environment Setup](README.md)

---

#### System essentials — core tools every developer and security person needs

```bash
sudo apt install -y \
  git curl wget vim neovim tmux \
  build-essential gcc g++ make cmake \
  python3 python3-pip python3-venv \
  net-tools dnsutils ncat socat \
  unzip p7zip-full jq tree htop \
  golang-go ruby-full default-jdk
```

Copy the whole block, paste it into the terminal, hit Enter, and wait. It will install everything automatically.

#### VS Code — a beginner-friendly text/code editor

```bash
# Download and install
wget -qO /tmp/vscode.deb "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
sudo dpkg -i /tmp/vscode.deb
sudo apt install -f -y

# Install useful extensions
code --install-extension ms-vscode.hexeditor
code --install-extension ms-python.python
code --install-extension redhat.vscode-yaml
code --install-extension streetsidesoftware.code-spell-checker
```

#### Git — saves and tracks your work

Git is how developers save their code and share it. Think of it like "save history" for your files.

```bash
# Replace with your actual name and email
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global core.editor "vim"
git config --global init.defaultBranch main

# Create an SSH key — this is your ID card for GitHub/GitLab
ssh-keygen -t ed25519 -C "you@example.com"
# Press Enter through all prompts to accept defaults

# Show your public key — copy this and add it to GitHub → Settings → SSH Keys
cat ~/.ssh/id_ed25519.pub
```

#### Python — needed for most security tools

```bash
pip install --upgrade pip
pip install pwntools requests beautifulsoup4 scapy impacket
```

#### Go — needed for some tools (subfinder, ffuf, nuclei, etc.)

```bash
# Make Go tools available in your terminal (add this to your shell config)
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.zshrc
source ~/.zshrc
```

---

## What to Read Next

| You want to...                   | Go here                                            |
| -------------------------------- | -------------------------------------------------- |
| Browse the full security toolkit | [General Security Tools](GeneralSecurity-Tools.md) |
| Run lab services in containers   | [Docker Setup](Docker.md)                          |
| Harden and tune your Arch host   | [Arch Quality of Life](Arch-QOL.md)                |
