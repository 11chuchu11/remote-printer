# Design: remote-printer — Sistema de Impresión Remota

## Technical Approach

Bot de Telegram con long polling que recibe archivos, presenta configuración interactiva via inline keyboards, y despacha trabajos a CUPS mediante subprocess. Dos contenedores Docker independientes comunicados por red del host.

---

## Architecture Decisions

| Decisión | Elección | Alternativas | Rationale |
|---|---|---|---|
| Networking | `network_mode: host` | bridge + expose 631 | Bot accede a CUPS en localhost sin config de red |
| Bot mode | Long polling | Webhook | Sin puertos entrantes; modelo de seguridad más simple para red local |
| Base de datos | SQLite (stdlib) | PostgreSQL, Redis | Sin dependencias extra; volumen Docker preserva datos |
| Whitelist | Variable de entorno | SQLite | Cambios de acceso requieren reinicio explícito; no expone gestión al bot |
| Config usuario | SQLite `print_config` | Env por usuario | Modificable en runtime por usuario sin escalar el `.env` |
| UI interactiva | InlineKeyboardMarkup | Comandos de texto | UX nativa de Telegram; actualización en tiempo real editando el mismo mensaje |
| Driver Brother | `.deb` i386 en imagen | Driver genérico | DCP-T300 requiere driver propietario; versión 3.0.2 verificada en Debian trixie |

---

## Data Flow

### Flujo principal — impresión

```
User ──envía archivo──► handle_document
                              │
                         download /tmp/{uid}_{file}
                         get_print_config() ← SQLite
                         parse caption (page range?)
                         user_data["pending"] = {path, cfg, name}
                              │
                         InlineKeyboard (job_keyboard)
                              │
                    ┌─────────┴─────────┐
                 pj:*              pj:confirm
               (ajustes)               │
            edita cfg en          print_file()
              memoria            (lp subprocess)
            edita msg                  │
                                   CUPS ──► Printer
                                       │
                                  log_print() → SQLite
                                  edit msg → resultado
                                  cleanup /tmp
```

### Flujo de autenticación

```
Cualquier mensaje o callback
           │
     is_allowed(user_id) ← ALLOWED_IDS (frozenset, cargado al inicio desde env)
           │
     NO ──► reply_unauthorized()  →  muestra user_id al usuario
     SÍ ──► handler continúa
```

### Flujo de configuración predeterminada

```
/config ──► get_print_config(user_id) ← SQLite
                │
          config_keyboard()
                │
          cfg:* callbacks ──► set_print_config(user_id, param, value)
                                      │
                               SQLite upsert
                               ON CONFLICT DO UPDATE
```

---

## Module Map

| Módulo | Responsabilidad |
|---|---|
| `config.py` | Env vars, auth (`is_allowed`), nombres de usuario (`get_user_name`) |
| `cups.py` | Subprocess CUPS: `print_file`, `get_status`, `get_ink`, `get_queue`, `cancel_job`, `cancel_all` |
| `storage.py` | SQLite: `history`, `logs`, `print_config`. Funciones: `log_event`, `log_print`, `get_history`, `get_print_config`, `set_print_config` |
| `handlers/keyboards.py` | Constructores de `InlineKeyboardMarkup` y textos HTML para mensajes |
| `handlers/callbacks.py` | Dispatch de callbacks `pj:*` (trabajo pendiente) y `cfg:*` (config default) |
| `handlers/print.py` | Recepción de archivos, construcción del `pending`, muestra teclado |
| `handlers/queue.py` | `/status` `/queue` `/cancel` `/history` |
| `handlers/config.py` | `/config` — muestra teclado de config predeterminada |
| `handlers/help.py` | `/start` `/help` — con diferenciación autorizado/no autorizado |
| `handlers/common.py` | `reply_unauthorized` — mensaje con user_id propio |
| `bot.py` | Entry point: `init_db()`, registro de todos los handlers |

---

## SQLite Schema

```sql
CREATE TABLE history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    filename   TEXT,
    file_path  TEXT,                          -- NULL si PERSIST_FILES=false
    printed_at TEXT DEFAULT (datetime('now')),
    status     TEXT                           -- 'ok' | 'error'
);

CREATE TABLE logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT DEFAULT (datetime('now')),
    level     TEXT,                           -- 'INFO' | 'WARNING' | 'ERROR'
    event     TEXT,                           -- ver eventos abajo
    user_id   INTEGER,
    detail    TEXT
);

CREATE TABLE print_config (
    user_id INTEGER PRIMARY KEY,
    copies  INTEGER DEFAULT 1,
    media   TEXT    DEFAULT 'A4',
    sides   TEXT    DEFAULT 'one-sided',
    color   TEXT    DEFAULT 'color'
);
```

**Eventos de log**: `file_received`, `file_stored`, `print_ok`, `print_error`, `unauthorized`, `invalid_ext`, `cancel_job`, `cancel_all`, `config_changed`.

---

## Interfaces Clave

```python
# cups.py
def print_file(printer: str, path: str, config: dict | None = None) -> None
# config keys: copies(int), media(str), sides(str), color(str), pages(str)
# pages: "all" | "odd" | "even" | "1-3,5" → CUPS page-ranges / page-set

# storage.py
def get_print_config(user_id: int) -> dict       # devuelve defaults si no hay fila
def set_print_config(user_id: int, param: str, value) -> None  # upsert
def log_event(level, event, user_id=None, detail=None) -> None
def log_print(user_id, filename, status, file_path=None) -> None

# handlers/keyboards.py
def job_keyboard(cfg: dict) -> InlineKeyboardMarkup
def config_keyboard(cfg: dict) -> InlineKeyboardMarkup
def job_text(filename: str, cfg: dict, name: str | None = None) -> str
def config_text(cfg: dict) -> str
```

---

## Callback Protocol

Formato: `{prefix}:{action}`

| Prefix | Estado | Acciones |
|---|---|---|
| `pj` | `user_data["pending"]` (en memoria) | `copies_inc`, `copies_dec`, `color`, `sides`, `media`, `pages`, `confirm`, `cancel`, `noop` |
| `cfg` | SQLite `print_config` | `copies_inc`, `copies_dec`, `color`, `sides`, `media`, `done`, `noop` |

El estado `pj` vive en `context.user_data["pending"]` — se pierde si el bot reinicia antes de que el usuario confirme.

---

## Testing Strategy

Sin framework de tests. Verificación manual via:

```bash
docker compose logs print-bot   # errores del bot
docker compose logs cups        # estado de CUPS
```

---

## Open Questions

- [ ] **Niveles de tinta** (`get_ink`): depende de si el driver Brother expone supply levels via `lpstat -l -p`. Requiere verificar con impresora conectada.
- [ ] **Pending job persistencia**: `user_data["pending"]` se pierde si el bot reinicia mid-flow. Evaluar persistencia en SQLite si esto es problema operativo.
