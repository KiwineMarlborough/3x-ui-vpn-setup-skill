# VPS Optimization (optional)

Small VPS (1 GB RAM) benefits from swap + BBR.

## Swap (if RAM < 2 GB)

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## BBR congestion control

```bash
echo 'net.core.default_qdisc=fq' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control=bbr' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
sysctl net.ipv4.tcp_congestion_control
```

BBR is a kernel module (`tcp_bbr`), not a service and not part of the panel; it applies to **new** TCP connections only (existing sockets keep
the old algorithm until they reconnect), and affects every program on the host (Xray, nginx, ssh). Rollback: remove the line and
`sysctl -w net.ipv4.tcp_congestion_control=cubic`. Do not enable it on a shared host without checking that the other services do not depend on the old behaviour.

## Unattended upgrades (security)

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Reboot window: avoid peak VPN usage.