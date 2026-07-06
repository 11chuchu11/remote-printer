# Contexto del proyecto: Brother DCP-T300 por wifi + bot de Telegram

## Objetivo
Convertir una Brother DCP-T300 (impresora USB-only, sin wifi propio) en una
impresora accesible por wifi para toda la red doméstica, y además permitir
imprimir remotamente desde cualquier lugar mandando archivos por Telegram.

## Hardware
- Impresora: Brother DCP-T300, conectada por USB. No tiene wifi ni ethernet
  propio — solo imprime/escanea localmente por cable USB.
- Servidor: notebook Lenovo IdeaPad vieja, CPU 64-bit, con wifi Intel Dual
  Band Wireless AC 3160 (driver `iwlwifi`, funciona sin drivers adicionales).

## Sistema operativo
- Debian 13 "trixie" (no Debian 12 — trixie es la stable actual desde
  agosto 2025, con soporte hasta 2030; 12 quedó como oldstable).
- Instalación mínima: solo tareas "SSH server" + "standard system utilities".
  Sin entorno de escritorio, sin "web server" (Apache no hace falta — CUPS
  trae su propio servidor web en el puerto 631).

## Arquitectura final

```
[Usuario, afuera de casa]
      |  (mensaje con PDF a Telegram)
      v
[Telegram API]
      |  (long polling — el bot pregunta, no expone puertos)
      v
[Contenedor print-bot] --localhost/network_mode:host--> [Contenedor cups] --USB--> [Brother DCP-T300]
```

Dos contenedores Docker, orquestados con `docker compose`:
- **cups**: Debian trixie-slim + CUPS + avahi-daemon + drivers Brother
  (`.deb` bajados directo del sitio de Brother en el build). Tiene acceso
  directo al bus USB (`--device=/dev/bus/usb:/dev/bus/usb`, `privileged: true`).
- **print-bot**: Python 3.12-slim + `python-telegram-bot` + `cups-client`
  (para poder correr `lp` contra el CUPS del otro contenedor). Sin acceso a
  hardware, solo a internet (saliente) y a CUPS via `localhost:631`
  (por eso ambos contenedores usan `network_mode: host`).

## Problemas ya resueltos durante el desarrollo (no repetir estos pasos)

1. **`$PATH` incompleto para usuarios normales**: en esta instalación mínima
  de Debian, `/sbin` y `/usr/sbin` no estaban en el PATH por defecto, lo cual
  hacía parecer que `ifup`, `wpa_supplicant`, `rfkill`, etc. no estaban
  instalados cuando en realidad sí lo estaban, solo que en otra ruta.
  Solucionado agregando `export PATH=$PATH:/sbin:/usr/sbin` a `~/.bashrc`
  tanto para `root` como para el usuario `franco`.

2. **Wifi bloqueada por rfkill soft-block**: la Lenovo IdeaPad bloquea la
  wifi por software al bootear Linux (driver `ideapad_laptop`, dispositivo
  `ideapad_wlan`). No es bloqueo físico (hard: 0), es soft-block (soft: 1).
  Se resuelve con `rfkill unblock all`, y se dejó un servicio systemd
  (`/etc/systemd/system/rfkill-unblock.service`) para que esto se desbloquee
  solo en cada reinicio.

3. **`ifupdown` / `dhclient` no estaban instalados** en la instalación
  mínima. Se instalaron desde el propio pendrive de instalación (que quedó
  registrado como fuente APT local), ya que en ese momento todavía no había
  wifi para bajarlos de internet.

4. **Version del instalador de drivers Brother desactualizada**: el nombre
  de archivo `linux-brprinter-installer-2.2.3-1.gz` que aparece en guías
  viejas ya no existe. La versión vigente (a la fecha de este proyecto) es
  `linux-brprinter-installer-2.2.6-0.gz`, descargable desde
  `https://download.brother.com/welcome/dlf006893/`.

5. **`cupsctl` no puede correr dentro de un `RUN` del Dockerfile**: necesita
  un servidor CUPS corriendo para conectarse, y durante el `docker build` no
  hay ningún proceso vivo. Se movió esa línea al `entrypoint.sh`, después de
  levantar `cupsd`.

6. **`service dbus/avahi-daemon start` falla en la imagen `debian:trixie-slim`**:
  no trae los scripts de sysvinit (`/etc/init.d/...`) que el comando
  `service` espera. Esto generaba un loop de reinicio del contenedor
  (por el `set -e` del entrypoint). Se reemplazó por invocar los binarios
  directamente:
  ```bash
  dbus-daemon --system --fork
  avahi-daemon --daemonize --no-drop-root
  ```

7. **Grupo `docker` no aplicado en la sesión activa**: después de
  `usermod -aG docker franco`, hace falta cerrar sesión y volver a entrar
  (o `newgrp docker`) para que el cambio de grupo tome efecto.

## Seguridad — decisiones tomadas

- El bot de Telegram usa **long polling**, no webhook — esto significa que
  **no hay ningún puerto abierto en el router** hacia internet. Todo el
  tráfico es saliente desde el servidor hacia Telegram.
- **Whitelist de usuarios**: el bot solo acepta archivos de IDs de Telegram
  listados en `ALLOWED_USER_IDS` (variable de entorno). Cualquier otro user
  recibe "No autorizado" y se loguea el intento.
- **Validación de extensión de archivo** antes de imprimir (`.pdf`, `.jpg`,
  `.jpeg`, `.png`, `.txt`) — nunca se ejecuta nada, solo se manda a `lp`.
- El puerto **631 (CUPS) nunca debe exponerse a internet**, ni por
  port-forwarding del router ni con `--remote-any` accesible desde afuera.
  Solo debe ser alcanzable dentro de la red local.
- **Secretos fuera del control de versiones**: `TELEGRAM_BOT_TOKEN` y
  `ALLOWED_USER_IDS` viven en un archivo `.env` (listado en `.gitignore`,
  nunca commiteado). El `docker-compose.yml` los referencia con `env_file`.
- Un token de bot llegó a exponerse una vez sin querer en un log compartido
  durante el desarrollo — se revocó y regeneró desde BotFather
  (`/mybots` → Bot Settings → API Token → Revoke current token). Si en algún
  momento se vuelve a exponer un secreto (token, IDs, credenciales), hay que
  revocarlo/regenerarlo, no alcanza con solo borrar el mensaje o el archivo.
- Recomendado pero no aplicado todavía: `ufw` restringiendo el puerto 631
  solo al rango de la red local, y considerar Tailscale/WireGuard si en el
  futuro se quiere administrar CUPS remotamente (en vez de exponer puertos).

## Estructura del repo

```
print-project/
├── cups/
│   ├── Dockerfile
│   └── entrypoint.sh
├── bot/
│   ├── Dockerfile
│   └── bot.py
├── docker-compose.yml
├── .env              (NO versionado — crear a mano en cada máquina nueva)
├── .gitignore
└── CONTEXT.md         (este archivo)
```

## Cómo levantar el proyecto desde cero en una máquina nueva

```bash
git clone <url-del-repo>
cd print-project
nano .env   # completar TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS, CUPS_PRINTER
docker compose up -d --build
docker compose logs cups       # confirmar "Impresora DCPT300 agregada."
docker compose logs print-bot  # confirmar "Application started"
```

## Pendientes / ideas para seguir extendiendo

- Firewall (`ufw`) restringiendo el 631 a la red local.
- Feedback de estado de tinta o de trabajos de impresión vía el bot.
- Soporte para escaneo remoto (devolver el PDF escaneado por Telegram),
  usando el driver `brscan4` que ya está instalado pero sin explotar.
- Notificación al bot cuando se traba el papel o falta tinta (leyendo el
  estado de CUPS/IPP periódicamente).
