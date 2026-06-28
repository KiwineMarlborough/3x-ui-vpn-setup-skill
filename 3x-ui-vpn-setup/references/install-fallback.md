# Install Fallback (when GitHub blocked)

If `install.sh` fails to download from GitHub:

## Option A — download from another network

On machine with access:

```bash
curl -Lo install.sh https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh
scp install.sh user@vps:/tmp/
ssh user@vps 'bash /tmp/install.sh'
```

## Option B — manual install (wiki)

Follow official wiki: https://github.com/MHSanaei/3x-ui/wiki  
Install Xray core + panel binary + systemd unit manually.

## Option C — mirror / proxy on server

```bash
# If user provides HTTP proxy:
export https_proxy=http://proxy:port
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)
```

## After any path

Same steps: change password, `webBasePath`, API token, continue `execution-order.md` from phase 3.