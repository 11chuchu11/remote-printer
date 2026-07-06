# CLAUDE.md

Este archivo es leído automáticamente por Claude Code al iniciar en este proyecto.

## Qué es este proyecto

Servidor de impresión en red para una Brother DCP-T300 (impresora USB-only,
sin wifi propio), corriendo en Docker sobre una Debian 13 headless, con un
bot de Telegram para imprimir remotamente. Dos contenedores: `cups` (CUPS +
drivers Brother, con acceso al USB) y `print-bot` (bot de Telegram en Python
que manda archivos a imprimir vía `lp`).

## Antes de hacer cambios

**Leé `CONTEXT.md`** antes de modificar el `Dockerfile` de `cups/`, el
`entrypoint.sh`, o el `docker-compose.yml`. Ese archivo documenta problemas ya
resueltos (versión del instalador de Brother, por qué `cupsctl` está en el
entrypoint y no en el Dockerfile, por qué se reemplazó `service` por invocar
los binarios de dbus/avahi directo, etc.). Si un cambio que estás por hacer
choca con algo documentado ahí, avisá antes de proceder — probablemente ya se
intentó de otra forma y falló por una razón concreta.

También conviene revisar `CONTEXT.md` si:
- Hay que tocar algo de red/wifi del lado del host Debian (hay gotchas de
  `$PATH`, `rfkill`, `ifupdown` documentados ahí, aunque son del host, no del
  proyecto Docker en sí).
- Se va a tocar cualquier cosa relacionada a secretos (`.env`,
  `TELEGRAM_BOT_TOKEN`, `ALLOWED_USER_IDS`) — hay una sección de seguridad
  con las reglas que se vienen siguiendo (nunca commitear el `.env`, nunca
  exponer el puerto 631 a internet, etc.).

## Reglas del proyecto

- Nunca exponer el puerto 631 (CUPS) a internet — solo accesible en red local.
- Nunca commitear `.env` (ya está en `.gitignore`, no lo saques de ahí).
- El bot usa long polling, no webhook — no agregar lógica de servidor HTTP
  entrante para el bot sin discutirlo primero, rompería el modelo de
  seguridad (nada de puertos entrantes expuestos).
- Si se agrega o cambia una dependencia de Python en `bot/bot.py`, actualizar
  también `bot/Dockerfile`.
- Si un token o credencial se expone por error (log, commit, chat), hay que
  revocarlo/regenerarlo — no alcanza con borrar el mensaje o el archivo.

## Comandos útiles

```bash
docker compose up -d --build       # levantar/reconstruir todo
docker compose logs cups           # ver si detectó la impresora e inició bien
docker compose logs print-bot      # ver si el bot arrancó sin errores
docker compose restart cups        # si no detectó la impresora por timing de USB
```
