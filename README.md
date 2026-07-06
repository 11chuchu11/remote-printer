# Remote Printer

Servidor de impresión en red para una impresora Brother DCP-T300 (USB-only) corriendo en Docker sobre Debian 13 headless, controlable remotamente a través de un bot de Telegram.

---

## Arquitectura

Dos contenedores Docker orquestados con Docker Compose:

| Contenedor | Imagen base | Función |
|---|---|---|
| `cups` | debian:trixie-slim | Servidor CUPS + driver Brother DCP-T300 |
| `print-bot` | python:3.12-slim | Bot de Telegram que envía trabajos a CUPS |

Ambos usan `network_mode: host` para que el bot pueda alcanzar CUPS en `localhost:631` sin configuración extra.

```
Telegram ──► print-bot ──► CUPS ──► Brother DCP-T300 (USB)
```

---

## Variables de entorno (.env)

```env
# Obligatorias
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
ALLOWED_USER_IDS=111111111,222222222

# Opcionales
USER_NAMES=111111111:Alice,222222222:Bob    # nombres por ID
CUPS_PRINTER=DCPT300                        # default: DCPT300
DB_PATH=/data/bot.db                        # default: /data/bot.db
PERSIST_FILES=false                         # guardar archivos en disco (default: false)
FILES_DIR=/data/files                       # carpeta de archivos persistidos (default: /data/files)
```

`ALLOWED_USER_IDS` — IDs de Telegram separados por coma. Solo estos usuarios pueden usar el bot.  
`USER_NAMES` — mapeo opcional `id:nombre` separado por coma. Habilita mensajes personalizados.

---

## Comandos del bot

### `/start` y `/help`
- Usuario **autorizado**: muestra la lista de comandos disponibles.
- Usuario **no autorizado**: informa que el bot es privado y muestra su propio ID de Telegram para que se lo pase al admin.

### Enviar un archivo
El usuario envía un documento (PDF, JPG, JPEG, PNG o TXT). El bot responde con un menú interactivo para configurar la impresión antes de confirmar.

Si el archivo se envía con un **caption** en formato de rango de páginas (ej: `1-3,5,7-9`), ese rango se preselecciona automáticamente.

#### Menú de impresión interactivo
```
Hola, Alice! 📄 documento.pdf

Ajustá la configuración antes de imprimir:
  Copias:  1
  Color:   color
  Lados:   Simple
  Papel:   A4
  Páginas: Todas

[➖] [1 copia(s)] [➕]
[🎨 Color]
[📄 Simple]
[📐 A4]
[📑 Todas]
[✅ Imprimir]  [❌ Cancelar]
```

Cada botón actualiza el mensaje en tiempo real. Al confirmar, el bot imprime y notifica el resultado.

**Parámetros configurables por trabajo:**

| Parámetro | Opciones |
|---|---|
| Copias | 1 – 99 |
| Color | Color / Escala de grises |
| Lados | Simple / Doble (largo) / Doble (corto) |
| Papel | A4 / Letter / A5 / Legal |
| Páginas | Todas / Impares / Pares / rango custom (via caption) |

### `/status`
Muestra el estado actual de la impresora (via `lpstat -p`). Si el driver expone niveles de tinta, los incluye.

### `/queue`
Lista los trabajos de impresión en cola con su ID de trabajo.

### `/cancel`
- `/cancel` — cancela todos los trabajos en cola.
- `/cancel <id>` — cancela un trabajo específico por ID.

### `/history`
Muestra las últimas 10 impresiones del usuario con fecha, archivo y estado (ok/error).

### `/config`
Abre un menú interactivo para modificar la **configuración predeterminada** del usuario. Cada cambio se guarda automáticamente en la base de datos y se aplica a futuras impresiones.

```
⚙️ Configuración predeterminada

  Copias:  1
  Color:   color
  Lados:   Simple
  Papel:   A4

[➖] [1 copia(s)] [➕]
[🎨 Color]
[📄 Simple]
[📐 A4]
[✅ Listo]
```

---

## Mensajes personalizados

Si el usuario tiene nombre configurado en `USER_NAMES`, los mensajes del bot lo incluyen:

- **Menú de impresión**: `"Hola, Alice! 📄 documento.pdf"`
- **Impresión exitosa**: `"✅ ¡En camino, Alice! Se está imprimiendo documento.pdf."`
- **Error de impresión**: `"❌ Alice, no se pudo imprimir documento.pdf. Motivo: ..."`

Usuarios sin nombre configurado reciben mensajes genéricos equivalentes.

---

## Persistencia de datos

### Base de datos SQLite (`/data/bot.db`)

**Tabla `history`** — historial de trabajos de impresión:

| Campo | Descripción |
|---|---|
| `user_id` | ID de Telegram del usuario |
| `filename` | Nombre del archivo |
| `file_path` | Ruta en disco (si `PERSIST_FILES=true`) |
| `printed_at` | Fecha y hora |
| `status` | `ok` o `error` |

**Tabla `logs`** — auditoría de eventos:

| Campo | Descripción |
|---|---|
| `level` | `INFO`, `WARNING`, `ERROR` |
| `event` | Tipo de evento (ver lista abajo) |
| `user_id` | ID del usuario involucrado |
| `detail` | Detalle adicional |
| `logged_at` | Fecha y hora |

Eventos registrados: `file_received`, `file_stored`, `print_ok`, `print_error`, `unauthorized`, `invalid_ext`, `cancel_job`, `cancel_all`, `config_changed`.

**Tabla `print_config`** — configuración predeterminada por usuario:

| Campo | Default |
|---|---|
| `copies` | 1 |
| `media` | A4 |
| `sides` | one-sided |
| `color` | color |

### Persistencia de archivos (opcional)

Con `PERSIST_FILES=true`, cada archivo recibido se copia a `/data/files/{user_id}/{filename}` antes de imprimir. Si el archivo ya existe, se prefija con un timestamp. La ruta queda guardada en `history.file_path`.

---

## Scripts de gestión de usuarios

Ubicados en `scripts/`. Leen y escriben directamente el `.env`.

```bash
./scripts/add-users.sh      # agrega usuarios (pide ID y nombre, hasta -1)
./scripts/remove-user.sh    # elimina un usuario por ID
./scripts/edit-user.sh      # edita el nombre de un usuario existente
./scripts/list-users.sh     # lista todos los usuarios con su nombre
```

Todos avisan al finalizar que hay que reiniciar el contenedor para aplicar los cambios:
```bash
docker compose restart print-bot
```

---

## Despliegue

```bash
# Primera vez
cp .env.example .env       # completar con token y user IDs
docker compose up -d --build

# Actualizar con cambios
git pull
docker compose up -d --build

# Ver logs
docker compose logs print-bot   # bot
docker compose logs cups        # servidor de impresión

# Reiniciar si la impresora no se detectó al arrancar
docker compose restart cups
```

---

## Estructura del proyecto

```
remote-printer/
├── docker-compose.yml
├── .env                        # secretos (nunca commitear)
├── cups/
│   ├── Dockerfile
│   └── entrypoint.sh           # inicia dbus, avahi, cupsd y configura la impresora
├── bot/
│   ├── Dockerfile
│   ├── bot.py                  # entry point, registro de handlers
│   ├── config.py               # variables de entorno y helpers
│   ├── cups.py                 # capa de abstracción sobre CUPS (lp, lpstat, cancel)
│   ├── storage.py              # SQLite: historial, logs, config de impresión
│   └── handlers/
│       ├── print.py            # recepción de archivos y menú interactivo
│       ├── queue.py            # /status, /queue, /cancel, /history
│       ├── config.py           # /config interactivo
│       ├── help.py             # /start, /help
│       ├── callbacks.py        # manejo de botones inline
│       ├── keyboards.py        # constructores de teclados y textos
│       └── common.py           # helpers compartidos (reply_unauthorized)
└── scripts/
    ├── add-users.sh
    ├── remove-user.sh
    ├── edit-user.sh
    └── list-users.sh
```

---

## Seguridad

- El puerto 631 (CUPS) no se expone a internet — solo accesible en red local.
- El `.env` está en `.gitignore` y nunca debe commitearse.
- El bot usa long polling (sin puertos entrantes expuestos).
- Solo los IDs listados en `ALLOWED_USER_IDS` pueden enviar comandos o archivos.
- Los usuarios no autorizados reciben su propio ID para contactar al admin, pero no pueden ejecutar ninguna acción.
- Si un token o credencial se expone por error, debe revocarse/regenerarse — borrar el archivo o mensaje no es suficiente.
