# Orange Pi Media Hub

Um dashboard leve para servidores caseiros baseados em Orange Pi (ou qualquer SBC Linux/Docker) — mostra CPU, RAM, discos, rede e temperatura em tempo real, além de uma lista de atalhos para os serviços que você roda (Jellyfin, File Browser, Portainer, etc.).

A lightweight status dashboard for home servers built on an Orange Pi (or any Linux/Docker SBC) — live CPU, RAM, disk, network and temperature metrics, plus a shortcut list for whatever services you self-host (Jellyfin, File Browser, Portainer, etc.).

![status](https://img.shields.io/badge/status-stable-58bd8b)

---

## PT-BR

### O que é

Dois containers Docker:

- **`media-portal`** (nginx) — serve a página estática e faz proxy de `/api/status` para o backend.
- **`portal-status`** (Flask) — lê `/proc`, `/sys` e `/` do host (montados read-only) e expõe `/status` como JSON. Não depende de nenhum caminho ou IP específico da sua máquina — funciona em qualquer SBC Linux.

A interface tem suporte a português e inglês (alterna pelo botão no canto superior direito, a escolha fica salva no navegador).

### Instalação

Pré-requisitos: Docker + Docker Compose instalados no seu Orange Pi (ou outro host Linux/arm).

```bash
git clone https://github.com/<seu-usuario>/orangepi-dashboard.git
cd orangepi-dashboard
docker compose up -d --build
```

Acesse `http://<ip-do-seu-pi>/`.

### Configurar seus serviços

Edite `www/config.json`. Cada entrada em `services` vira um card clicável na página:

```json
{
  "id": "jellyfin",
  "name": "Jellyfin",
  "description": { "pt": "filmes, séries e música", "en": "movies, shows and music" },
  "icon": "JF",
  "accent": "blue",
  "port": 8096,
  "protocol": "http",
  "path": "/web/"
}
```

- `icon`: até 3 caracteres, aparece na bolha colorida do card.
- `accent`: uma das cores prontas — `blue`, `leaf`, `red`, `teal`, `sun`, `mint` — ou qualquer cor CSS válida (`#ff8800`, `rgb(...)`).
- `port` / `protocol` / `path`: o link do card é montado como `protocol://<hostname-da-página>:port/path` — assim funciona tanto acessando pelo IP local quanto por um túnel/VPN (Tailscale, etc.), sem hardcodar IP nenhum.
- `description`: objeto com `pt` e `en`; se faltar um dos dois, cai no outro.

Não precisa mexer em HTML/CSS/JS para adicionar, remover ou reordenar serviços — só editar esse arquivo e recarregar a página (é servido estático, sem rebuild).

O campo `title` no topo do `config.json` também é bilíngue e vira o nome exibido no topo da página e na aba do navegador.

Como `www/` é montado direto no container do nginx (bind mount), qualquer edição em `config.json` aparece na hora, sem `docker compose` de novo.

### Notas técnicas

- `portal-status` precisa dos bind mounts `/proc`, `/sys` e `/` (read-only) para ler métricas do host de dentro do container — já vêm configurados no `docker-compose.yml`, não precisa mexer.
- Discos: qualquer partição real (`/dev/*`) montada é detectada automaticamente, não é preciso listar manualmente.
- Rede: todas as interfaces reais são detectadas (ignora `docker*`, `veth*`, `lo`, `tun*`, `tap*`, `br-*`). Interfaces de túnel (Tailscale, WireGuard) que reportam estado "unknown" no kernel são tratadas como ativas — é um comportamento normal dessas interfaces, não um bug.
- Se `config.json` não existir ou estiver com erro de sintaxe, a página mostra um aviso em vez de quebrar silenciosamente.

---

## English

### What this is

Two Docker containers:

- **`media-portal`** (nginx) — serves the static page and proxies `/api/status` to the backend.
- **`portal-status`** (Flask) — reads `/proc`, `/sys` and `/` from the host (mounted read-only) and exposes `/status` as JSON. No machine-specific path or IP is hardcoded — it works on any Linux SBC.

The UI supports Portuguese and English (toggle button top-right, choice persisted in the browser).

### Install

Requirements: Docker + Docker Compose on your Orange Pi (or any Linux/arm host).

```bash
git clone https://github.com/<your-username>/orangepi-dashboard.git
cd orangepi-dashboard
docker compose up -d --build
```

Visit `http://<your-pi-ip>/`.

### Configure your services

Edit `www/config.json`. Every entry under `services` becomes a clickable card:

```json
{
  "id": "jellyfin",
  "name": "Jellyfin",
  "description": { "pt": "filmes, series e musica", "en": "movies, shows and music" },
  "icon": "JF",
  "accent": "blue",
  "port": 8096,
  "protocol": "http",
  "path": "/web/"
}
```

- `icon`: up to 3 characters, shown in the card's colored badge.
- `accent`: one of the built-in palette colors — `blue`, `leaf`, `red`, `teal`, `sun`, `mint` — or any valid CSS color (`#ff8800`, `rgb(...)`).
- `port` / `protocol` / `path`: the card's link is built as `protocol://<page-hostname>:port/path` — this works whether you're on the local IP or a tunnel/VPN (Tailscale, etc.), since no IP is ever hardcoded.
- `description`: an object with `pt` and `en`; if one is missing it falls back to the other.

No need to touch HTML/CSS/JS to add, remove, or reorder services — just edit this file and reload the page (it's served statically, no rebuild needed).

The `title` field at the top of `config.json` is bilingual too, and controls the name shown at the top of the page and the browser tab.

Since `www/` is bind-mounted straight into the nginx container, any edit to `config.json` shows up immediately, no `docker compose` needed.

### Technical notes

- `portal-status` needs the `/proc`, `/sys` and `/` (read-only) bind mounts to read host metrics from inside the container — already set up in `docker-compose.yml`, no changes needed.
- Disks: any real partition (`/dev/*`) that's mounted is auto-detected, no manual list required.
- Network: every real interface is auto-detected (ignores `docker*`, `veth*`, `lo`, `tun*`, `tap*`, `br-*`). Tunnel interfaces (Tailscale, WireGuard) that report kernel state "unknown" are treated as active — that's expected behavior for that interface type, not a bug.
- If `config.json` is missing or has a syntax error, the page shows a warning instead of failing silently.

## License

MIT — see [LICENSE](LICENSE).
