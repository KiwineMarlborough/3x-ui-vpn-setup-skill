# 3x-ui-vpn-setup — Skill для ИИ-агента (v1.2)

> **Задолбали блокировки чужих VPN?** Подними **свой** сервер за один вечер — без ручного копания в конфигах.
>
> **Как это работает:** установи skill в ИИ-агента (Claude, Codex, Grok, Qwen…) и **просто отдай ему задачу**. Агент сам по SSH настроит 3X-UI, Reality, XHTTP, Hysteria2, подписку и маршрутизацию Happ. Тебе не нужно разбираться в Xray — достаточно дать доступ и домены.
>
> **Что нужно от тебя:**
> - IP VPS и **два домена** (панель + CDN, например `panel.example.com` и `cdn.example.com`)
> - **SSH-доступ** к серверу (лучше **ключ**, не пароль)
> - **Sudo** на время настройки — желательно **не дольше 30 дней**; после setup можно отозвать пароль и оставить только ключ + `sudo` по ключу, либо вообще закрыть панель через SSH-туннель
>
> Всё остальное — сертификаты, inbound'ы, подписка, routing — делает агент по playbook внутри skill.

**Стек:** VLESS **Reality** + XHTTP + TCP Podkop + Hysteria2 + Happ routing (DoH) + nginx CDN fallback.

📄 **[QUICKSTART.ru.md](QUICKSTART.ru.md)** — быстрый старт (5 минут)  
📄 **[ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md)** — полная пошаговая инструкция  
📄 **[QUICKSTART.md](QUICKSTART.md)** — English quickstart
📄 **[CHANGELOG.md](CHANGELOG.md)** — история версий

---

## Установка skill

```bash
npx skills add KiwineMarlborough/3x-ui-vpn-setup-skill@3x-ui-vpn-setup -g -y
```

Скопируй [`.env.example`](.env.example) → `.env.local` (не коммить в git).

## Поддерживаемые агенты

Claude Code · OpenAI Codex · Qwen Code · OpenCode · **Grok Build** · Google Antigravity

Подробнее: [`agent-install.md`](3x-ui-vpn-setup/references/agent-install.md)

## Что ты получишь на выходе

| Результат | Описание |
|-----------|----------|
| 4 профиля в подписке | Reality (основной), TCP, XHTTP, Hysteria2 |
| Своя подписка | Кастомные пути, не `/sub/` как у всех |
| Split .ru | Российские сайты напрямую, остальное через VPN |
| CDN-страница на :443 | Выглядит как обычный сайт, не «голый» VPN-порт |
| Handoff | Агент отдаёт ссылки, пароли — в твой менеджер |

## Что внутри v1.2

| Категория | Файлы |
|-----------|-------|
| **Ядро** | `panel-settings`, `api-reference`, `repair-only`, `secrets-management` |
| **Эксплуатация** | `dns-setup`, `migration`, `monitoring`, `multi-user` |
| **Контекст** | `rkn-and-blocking`, `compatibility`, `vps-providers` |
| **Деплой** | nginx-шаблон, `deploy-nginx-fallback.sh`, `deploy-cert-hook.sh` |
| **Скрипты** | `verify-server.sh`, `audit-server.sh`, `set-sub-paths.py`, … |

## Структура репозитория

```
3x-ui-vpn-setup/
├── SKILL.md              ← главный playbook для агента
├── scripts/              ← 8 скриптов автоматизации
├── templates/            ← routing, hysteria, nginx
├── references/           ← 25 справочников
└── assets/cdn-fallback/  ← лендинг для :443
```

## Принципы

- Не патчим бинарники 3X-UI / Xray — только панель, API, SQLite
- Reality — основной протокол, не голый TLS на 443
- Новый сервер → `execution-order.md`; починка → `repair-only.md`
- Секреты не попадают в публичный репозиторий

## Безопасность доступа

| Вариант | Рекомендация |
|---------|--------------|
| SSH | Только **ed25519 ключ**, `PasswordAuthentication no` |
| Sudo | Временный пароль на setup **≤ 30 дней**, потом сменить / убрать |
| Панель | Случайный `webBasePath`, API-токен, доступ по домену |
| После setup | Панель через SSH-туннель, sudo только по ключу |

## Участие в разработке

[CONTRIBUTING.md](CONTRIBUTING.md) — PR приветствуются.

## Лицензия

MIT — [LICENSE](LICENSE)

**Репозиторий:** https://github.com/KiwineMarlborough/3x-ui-vpn-setup-skill