# Быстрый старт (5 минут)

🇬🇧 English: [QUICKSTART.md](QUICKSTART.md) · Подробнее: [ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md) · [README.ru.md](README.ru.md)

Для себя или друга — личный VPN с любым ИИ-агентом.

> **Отдай skill агенту с доступом по SSH — он сделает всё сам.** Тебе нужны только IP сервера, домены и sudo на время настройки (лучше не дольше 30 дней) или SSH-ключ вместо пароля.

---

## 1. Установить skill

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

## 2. Подготовить

| Что | Пример |
|-----|--------|
| Чистый Ubuntu VPS | от 1 GB RAM |
| SSH | `deploy@203.0.113.10` + ключ |
| Домен панели | `panel.vpn.example.com` |
| Домен CDN | `cdn.vpn.example.com` |
| DNS | A-записи → IP VPS, **прокси выкл** (серое облако в Cloudflare) |
| Reality SNI | `pixelforge.pics` (чужой живой HTTPS-сайт) |

Скопируй `.env.example` → `.env.local` (никогда не коммить).

## 3. Промпт агенту

**Новый сервер:**

```text
Используй skill 3x-ui-vpn-setup v1.2. Следуй references/execution-order.md.

SSH: deploy@203.0.113.10, ключ ~/.ssh/vps_ed25519
Домены: panel.vpn.example.com, cdn.vpn.example.com
Страна: DE
Reality SNI: pixelforge.pics
Happ routing: SplitRU (happ-routing-profile-ru.json)
nginx CDN fallback: да

Выполни все фазы сам по SSH.
В конце — scripts/verify-server.sh с SUB_ID.
Отдай handoff по post-setup-handoff.md. Секреты — secrets-management.md.
```

**Сломался существующий сервер:**

```text
Skill 3x-ui-vpn-setup. Следуй references/repair-only.md.
Симптом: JSON подписка отдаёт HTTP 500.
Сначала audit-server.sh. Не переустанавливай.
```

У агента должны быть включены **терминал / SSH**.

## 4. Телефон (Happ Plus)

1. Импортировать subscription URL из handoff
2. Потянуть подписку вниз для обновления routing
3. Подключиться к профилю **Reality** первым

## 5. Если что-то сломалось

| Симптом | Док / скрипт |
|---------|--------------|
| JSON sub 500 | `gotchas.md` + `fix-hysteria-stream.py` |
| Sub 404 | `panel-settings.md` + `set-sub-paths.py` |
| Podkop не коннектит | `fix-podkop-flow.py` |
| Xray не стартует | Hysteria `version != 2` |
| install.sh падает | `install-fallback.md` |
| Диагностика | `audit-server.sh` |

## 6. Структура репозитория

Полное описание — [README.ru.md](README.ru.md).