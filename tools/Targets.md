# Vulnerable Lab Containers

> **Previous:** [Docker Setup](Docker.md)

Ready-made deliberately vulnerable applications you can spin up locally for hands-on practice. Each one targets different skill areas — web exploitation, privilege escalation, container security, and more.

> Make sure Docker is running before pulling any image. See [Docker Setup](Docker.md).

---

## Web Application Exploitation

### OWASP Juice Shop

The most complete intentionally insecure web app. Covers the full OWASP Top 10 and beyond, with a built-in score board and progressive challenges.

```bash
docker run -d -p 3000:3000 bkimminich/juice-shop
```

Open [http://localhost:3000](http://localhost:3000)

---

### DVWA — Damn Vulnerable Web Application

Classic PHP/MySQL app covering SQLi, XSS, CSRF, file upload, command injection, and more. Adjustable difficulty levels.

```bash
docker run -d -p 80:80 vulnerables/web-dvwa
```

Open [http://localhost](http://localhost) — default login: `admin` / `password`

---

### WebGoat

OWASP's interactive learning platform. Lessons are embedded in the app; you exploit the vulnerability and then read the explanation.

```bash
docker run -d -p 8080:8080 -p 9090:9090 webgoat/goat-and-wolf
```

Open [http://localhost:8080/WebGoat](http://localhost:8080/WebGoat)

---

### bWAPP — Buggy Web Application

Over 100 web vulnerabilities in a single PHP app. Good breadth for systematically working through vulnerability classes.

```bash
docker run -d -p 80:80 raesene/bwapp
```

Open [http://localhost/bWAPP](http://localhost/bWAPP) — default login: `bee` / `bug`

---

### Security Shepherd

OWASP's CTF-style training platform for web and mobile security. Flag-based progression.

```bash
docker run -d -p 80:80 -p 443:443 owasp/security-shepherd
```

Open [https://localhost](https://localhost)

---

## Full Network Labs

### Metasploitable 2

A deliberately vulnerable Linux VM exposed as a network target. Covers services like FTP, SSH, Samba, MySQL, Tomcat, and more.

```bash
docker run -d -p 22:22 -p 80:80 -p 445:445 tleemcjr/metasploitable2
```

> Bind only to loopback or an isolated network — never expose this to a real network.

---

### VulnHub (local VMs)

VulnHub hosts downloadable VM images, not Docker containers. Download an image, import it into VirtualBox or QEMU, and attack it from your Kali VM on an isolated network.

[vulnhub.com](https://www.vulnhub.com)

---

## Container & Kubernetes Security

### Damn Vulnerable Docker (DVD)

A deliberately misconfigured Docker environment to practice container escapes, privilege escalation inside containers, and Docker daemon abuse.

```bash
git clone https://github.com/christophetd/damn-vulnerable-docker
cd damn-vulnerable-docker
docker compose up -d
```

[GitHub](https://github.com/christophetd/damn-vulnerable-docker)

---

### Kubernetes Goat

An intentionally vulnerable Kubernetes cluster. Covers misconfigurations, RBAC weaknesses, secret exposure, and container breakouts.

```bash
git clone https://github.com/madhuakula/kubernetes-goat
cd kubernetes-goat
bash setup-kubernetes-goat.sh
```

[GitHub](https://github.com/madhuakula/kubernetes-goat)

---

## Container Hardening

### Docker Bench for Security

Runs the CIS Docker Benchmark checks against your host and running containers. Use it to audit your setup before deploying anything real.

```bash
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /etc:/etc:ro \
  -v /lib/systemd/system:/lib/systemd/system:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security
```

[GitHub](https://github.com/docker/docker-bench-security)

---

## Quick Reference

| Container              | Focus                    | Difficulty              |
| ---------------------- | ------------------------ | ----------------------- |
| Juice Shop             | Web / OWASP Top 10       | Beginner → Advanced     |
| DVWA                   | Web fundamentals         | Beginner                |
| WebGoat                | Web / guided lessons     | Beginner                |
| bWAPP                  | Web breadth (100+ vulns) | Beginner → Intermediate |
| Security Shepherd      | Web / mobile CTF         | Intermediate            |
| Metasploitable 2       | Network services         | Beginner                |
| VulnHub VMs            | Mixed                    | Varies                  |
| Damn Vulnerable Docker | Container security       | Intermediate            |
| Kubernetes Goat        | Kubernetes security      | Intermediate → Advanced |
| Docker Bench           | Hardening audit          | All levels              |

---

## What to Read Next

| You want to...                              | Go here                             |
| ------------------------------------------- | ----------------------------------- |
| Offensive tools for attacking these targets | [Red Team Tools](RedTeam-Tools.md)  |
| Tune your Arch host                         | [Arch Quality of Life](Arch-QOL.md) |
| Back up your lab                            | [Backups](BackUps.md)               |
