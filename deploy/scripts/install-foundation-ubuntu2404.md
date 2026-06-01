# MedOrion Foundation Install Plan for Ubuntu 24.04

This is a reviewable plan, not an executed script. It needs sudo.

## Intended impact

- Install Docker Engine and Docker Compose Plugin.
- Add Docker's apt repository and keyring if using the official Docker packages.
- Start and enable Docker service.
- Install host Nginx for HTTPS reverse proxy.
- Install Node.js LTS tooling for frontend builds if builds are performed on host.
- Install python3-pip and python3-venv for operational scripts and emergency local checks.
- Create the docker group; the SSH user may need to log out and back in before docker works without sudo.

## Suggested install commands

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release python3-pip python3-venv nginx

# Docker official repository for Ubuntu 24.04
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker sygxdg
sudo systemctl enable --now docker
sudo systemctl enable --now nginx
```

Node.js LTS should be installed after architecture confirms whether host builds are required. If host Node is needed, use a reviewed LTS source rather than Ubuntu's default Node 18 package.

## Rollback commands

```bash
sudo systemctl disable --now nginx || true
sudo apt-get purge -y nginx nginx-common

sudo systemctl disable --now docker || true
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo rm -f /etc/apt/sources.list.d/docker.list /etc/apt/keyrings/docker.gpg

# Only after explicit confirmation, because this deletes container images, volumes, and build cache:
# sudo rm -rf /var/lib/docker /var/lib/containerd
```

Python pip/venv rollback:

```bash
sudo apt-get purge -y python3-pip python3-venv
sudo apt-get autoremove -y
```
