# Быстрый старт (5 минут) — Русский

| Язык | Файл |
|------|------|
| **Русский** | **QUICKSTART.ru.md** (этот файл) · [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) |
| **English** | [QUICKSTART.md](QUICKSTART.md) |

Для себя или друга — личный VPN с любым ИИ-агентом.

> **Отдай skill агенту с доступом по SSH — он сделает всё сам.** Тебе нужны IP сервера, один домен, твой собственный публичный IP и отдельная учётка агента (только ключ).

---

## 1. Установить skill

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## 2. Подготовить

| Что | Пример |
|-----|--------|
| Чистый Ubuntu VPS | от 1 GB RAM |
| SSH | `deploy@203.0.113.10` + ключ (учётка агента на ограниченный срок — `agent-access-hygiene.md`) |
| **Твой публичный IP** | `198.51.100.7` — идёт в белый список IPsum/Fail2Ban, чтобы не заблокировать себя |
| Домен CDN/VPN | `cdn.vpn.example.com` (единственное публичное имя; **DNS-записи панели нет**) |
| DNS | одна A-запись → IP VPS, **прокси выкл** (серое облако в Cloudflare) |
| Reality SNI | `pixelforge.pics` (чужой живой HTTPS-сайт; на каждый Reality-порт свой) |

Скопируй `.env.example` → `.env.local` (никогда не коммить).

## 3. Промпт агенту

**Новый сервер:**

```text
Используй skill 3x-ui-vpn-setup v1.3. Следуй references/execution-order.md.

SSH: deploy@203.0.113.10, ключ ~/.ssh/vps_ed25519 (sudo только по ключу)
Домен CDN: cdn.vpn.example.com   (публичной записи панели нет; панель — через SSH-туннель)
ADMIN_IPS: 198.51.100.7
Страна: DE
Reality SNI: pixelforge.pics
Happ routing: SplitRU (happ-routing-profile-ru.json)
nginx CDN fallback: да
AmneziaWG 3.1: нет   (или: да, порт 56100, клиенты router,phone)

Выполни все фазы сам по SSH. Включи IPsum + Fail2Ban (автооткат, потом подтверди).
Сделай так, чтобы сертификат продлевался сам (deploy-acme-renewal.sh: STAGING_TEST, затем APPLY).
В конце — scripts/loopback-test.py и scripts/verify-server.sh с SUB_ID.
Отдай handoff по post-setup-handoff.md. Секреты — secrets-management.md.
```

**Сломался существующий сервер:**

```text
Skill 3x-ui-vpn-setup. Следуй references/repair-only.md.
Симптом: <одной строкой>.
Сначала audit-server.sh, check-cert-expiry.sh и loopback-test.py. Не переустанавливай.
Не откатывай серверные изменения, пока серверная сторона не доказана (testing-methods.md).
```

**Обновить панель:**

```text
Skill 3x-ui-vpn-setup, references/backup-update.md: бэкап БД + бинарников, прочитай release notes
("Before you upgrade"), обнови 3X-UI + Xray вместе, затем loopback-test.py и verify-server.sh.
```

У агента должны быть включены **терминал / SSH**.

## 4. Как открыть админ-панель (она закрыта от интернета)

1. Добавь в hosts на своём ПК: `127.0.0.1 <имя-панели>`.
2. `ssh -i <ключ> -L 29800:127.0.0.1:29800 <user>@<ip-vps>` (окно держи открытым).
3. Браузер: `https://<имя-панели>:29800/<webBasePath>/`, прими самоподписанный сертификат.
   (`localhost` даёт 403 — так и должно быть.) Подробности: `references/panel-tunnel-access.md`.

## 5. Телефон (Happ Plus)

1. Импортировать subscription URL из handoff
2. Потянуть подписку вниз для обновления routing
3. Сначала профиль **Reality**. Если профиль показывает `n/a` — проверь реальный трафик: индикатор ненадёжен (`testing-methods.md`).
   AmneziaWG **не** входит в подписку: используй приложения AmneziaVPN/AmneziaWG и `.conf`/QR.

## 6. Если что-то сломалось

| Симптом | Док / скрипт |
|---------|--------------|
| Reality работает, TCP/XHTTP/Hysteria/подписка мертвы | **истёк сертификат** → `check-cert-expiry.sh`, `cert-renewal-nginx.md` |
| Профиль «n/a» в клиенте | `loopback-test.py` → другой клиент → другая сеть (`testing-methods.md`) |
| Пропал доступ только из одной сети | ложное срабатывание IPsum → белый список (`blocklist-ipsum-fail2ban.md`) |
| JSON sub 500 | `gotchas.md` + `fix-hysteria-stream.py` |
| Sub 404 | `panel-settings.md` + `set-sub-paths.py` |
| В ссылках подписки неверные `security`/`sni` | устаревшая строка `hosts` (`gotchas.md`) |
| Podkop не коннектит | `fix-podkop-flow.py` / проверить фактический flow (`inbounds.md`) |
| Xray не стартует | Hysteria `version != 2` |
| install.sh падает | `install-fallback.md` |
| Диагностика | `audit-server.sh` |

## 7. Структура репозитория

Полное описание — [README.ru.md](README.ru.md).
