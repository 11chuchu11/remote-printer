from telegram import Update
from telegram.ext import ContextTypes
from config import is_allowed
from storage import get_print_config, set_print_config, log_event, PRINT_CONFIG_OPTIONS

SIDES_ALIAS = {
    "duplex":      "two-sided-long-edge",
    "duplex-long": "two-sided-long-edge",
    "duplex-short":"two-sided-short-edge",
    "simple":      "one-sided",
}

HELP = (
    "<b>Configuración de impresión</b>\n\n"
    "Uso: <code>/config &lt;parámetro&gt; &lt;valor&gt;</code>\n\n"
    "<b>copies</b>  1-99\n"
    "<b>media</b>   A4 | Letter | A5 | Legal\n"
    "<b>sides</b>   one-sided | duplex | duplex-short\n"
    "<b>color</b>   color | gray\n\n"
    "Sin argumentos muestra la configuración actual."
)


async def handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("No autorizado.")
        return

    if not context.args:
        cfg = get_print_config(user_id)
        msg = (
            "<b>Tu configuración actual:</b>\n"
            f"  copies: <code>{cfg['copies']}</code>\n"
            f"  media:  <code>{cfg['media']}</code>\n"
            f"  sides:  <code>{cfg['sides']}</code>\n"
            f"  color:  <code>{cfg['color']}</code>"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if len(context.args) != 2:
        await update.message.reply_text(HELP, parse_mode="HTML")
        return

    param, raw_value = context.args[0].lower(), context.args[1].lower()

    if param not in PRINT_CONFIG_OPTIONS:
        await update.message.reply_text(HELP, parse_mode="HTML")
        return

    value = SIDES_ALIAS.get(raw_value, raw_value)

    valid = PRINT_CONFIG_OPTIONS[param]
    if param == "copies":
        try:
            value = int(value)
        except ValueError:
            await update.message.reply_text("copies debe ser un número.")
            return
        if value not in valid:
            await update.message.reply_text("copies debe estar entre 1 y 99.")
            return
    else:
        if value not in valid:
            opciones = " | ".join(valid)
            await update.message.reply_text(f"Valores válidos para {param}: {opciones}")
            return

    set_print_config(user_id, param, value)
    log_event("INFO", "config_changed", user_id, f"{param}={value}")
    await update.message.reply_text(f"✓ {param} → {value}")
