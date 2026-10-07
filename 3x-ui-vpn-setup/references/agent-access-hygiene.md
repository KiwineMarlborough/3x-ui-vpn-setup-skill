# Access Hygiene: the AI-agent account and leftovers

An agent needs SSH + sudo to build this server. Every such account is **standing root access** — it must be
deliberate, key-only, time-boxed or explicitly renewed, and removed when the work is done.

## Create the agent account (run by the owner as root)

Generate the key pair **on the agent's machine** (the private key never travels); give the owner only the public key.

```bash
useradd -m -s /bin/bash agentadmin
usermod -aG sudo agentadmin
passwd -l agentadmin                                   # no password login at all
install -d -m 700 -o agentadmin -g agentadmin /home/agentadmin/.ssh
echo "ssh-ed25519 AAAA... agent@host" > /home/agentadmin/.ssh/authorized_keys
chmod 600 /home/agentadmin/.ssh/authorized_keys; chown -R agentadmin:agentadmin /home/agentadmin/.ssh
echo "agentadmin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/agentadmin; chmod 440 /etc/sudoers.d/agentadmin; visudo -c
chage -E $(date -d '+30 days' +%F) agentadmin           # time-box (omit only if you accept permanent access)
# sshd: global options first (e.g. DebianBanner no), Match blocks LAST
printf '\nMatch User agentadmin\n    PasswordAuthentication no\n' >> /etc/ssh/sshd_config.d/99-custom.conf
sshd -t && systemctl reload ssh
```

Notes that cost real time:

* **`passwd -l` + sudo asking for a password = sudo never works** (a locked account has no valid password).
  Either give the account `NOPASSWD` sudo as above or set a password for sudo; do not combine "locked" with
  "sudo requires a password".
* **Prefer a brand-new account name over reusing an old one.** In the originating project an account that another agent
  had used before kept answering `sudo: interactive authentication is required` even after a correct `NOPASSWD` file was
  written; the cause was never diagnosed, and a fresh account with the identical steps worked immediately. Don't spend time
  debugging a stale account — create a new one.
* **Expiry surprises:** an expired account fails with `Your account has expired; please contact your system administrator`
  at SSH login. Renew as root *in a shell on the server* — `chage -E <date> <user>` (`-E -1` = never). Do not run
  `ssh root@<the-same-server> "…"` from a session that is already on that server: it asks for a password that key-based
  setups don't have.
* In `sshd_config.d`, options such as `DebianBanner` are **not allowed inside a `Match` block** — put them above the first
  `Match`, or `sshd -t` fails.
* The agent's private key lives on the owner's workstation without a passphrase (the agent must use it unattended): keep it out
  of cloud-synced folders and never share the directory. Permanent access = permanent exposure of that file.

## Audit for leftovers (do it on every entry to a server; `scripts/audit-server.sh` prints all of this)

```bash
getent passwd | awk -F: '$7 ~ /(bash|sh)$/ {print $1, $3, $6}'      # who can log in
getent group sudo ; ls -l /etc/sudoers.d/ ; sudo grep -r . /etc/sudoers.d/ | grep -v '^#'
for h in /root /home/*; do sudo test -s $h/.ssh/authorized_keys && sudo ssh-keygen -lf $h/.ssh/authorized_keys; done
sudo crontab -l ; for u in $(cut -d: -f1 /etc/passwd); do sudo crontab -u $u -l 2>/dev/null | sed "s/^/$u: /"; done
```

Red flags found in practice: a temporary agent user (`*-temp`, key comment like `…-codex-temp`) with
`NOPASSWD:ALL` in `/etc/sudoers.d/90-…-temp` left months after the session; a renamed installer account with
two unknown keys; an unused `acme.sh` copy with its own daily cron in a user's home. Remove with a backup first:

```bash
sudo tar czf /root/backups/home-<user>.tgz -C /home <user>        # keep until you are sure
sudo crontab -u <user> -r ; sudo rm -f /etc/sudoers.d/<file> ; sudo visudo -c
sudo userdel -r <user>                                             # also removes /home/<user>
# remove its Match block from /etc/ssh/sshd_config.d/*.conf ; sshd -t && systemctl reload ssh
```
Verify afterwards: open a **new** SSH session as the remaining admin account before closing the old one.
Check for orphaned homes owned by a numeric uid (`ls -ln /home`) — e.g. the hoster's original `/home/user` after a rename.

## End of engagement

Delete (or `usermod -L -e 1`) the agent account, remove its sudoers file and key, rotate what the agent saw
(`secrets-management.md`), and delete private keys on the owner's machine.

## Related

`secrets-management.md` · `blocklist-ipsum-fail2ban.md` · `panel-tunnel-access.md`
