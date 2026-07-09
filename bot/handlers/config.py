from telegram import Update
from telegram.ext import ContextTypes
from config import is_allowed
from storage import get_print_config, set_print_config, log_event, PRINT_CONFIG_OPTIONS
from handlers.common import reply_unauthorized
from handlers.keyboards import config_keyboard, config_text


async def handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await reply_unauthorized(update)
        return

    if context.args:
        await _handle_config_args(update, user_id, context.args)
        return

    cfg = get_print_config(user_id)
    await update.message.reply_text(
        config_text(cfg),
        reply_markup=config_keyboard(cfg),
        parse_mode="HTML",
    )


async def _handle_config_args(update: Update, user_id: int, args: list[str]) -> None:
    if len(args) != 2:
        await update.message.reply_text(
            "Uso: /config &lt;param&gt; &lt;valor&gt;\n"
            "Params: copies, media, sides, color",
            parse_mode="HTML",
        )
        return

    param, raw_value = args[0], args[1]
    if param not in PRINT_CONFIG_OPTIONS:
        await update.message.reply_text(
            f"Parámetro desconocido: {param}\nParams válidos: copies, media, sides, color"
        )
        return

    options = PRINT_CONFIG_OPTIONS[param]
    if param == "copies":
        if not raw_value.isdigit() or int(raw_value) not in options:
            await update.message.reply_text("Copias debe ser un número entre 1 y 99.")
            return
        value = int(raw_value)
    else:
        if raw_value not in options:
            await update.message.reply_text(
                f"Valor inválido para {param}. Opciones: {', '.join(options)}"
            )
            return
        value = raw_value

    set_print_config(user_id, param, value)
    log_event("INFO", "config_changed", user_id, param)
    await update.message.reply_text(f"✅ {param} = {value}")
