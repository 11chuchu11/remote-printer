from telegram import Update
from telegram.ext import ContextTypes
from config import is_allowed

HELP_AUTHORIZED = (
    "<b>Comandos disponibles:</b>\n\n"
    "/status — estado de la impresora y tinta\n"
    "/queue — cola de impresión actual\n"
    "/cancel — cancelar todos los trabajos\n"
    "/cancel &lt;id&gt; — cancelar un trabajo específico\n"
    "/history — últimas 10 impresiones\n"
    "/config — ver configuración de impresión\n"
    "/config &lt;param&gt; &lt;valor&gt; — cambiar un parámetro\n\n"
    "Para imprimir, enviá un archivo PDF, JPG, PNG o TXT."
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text(
            f"Hola. Este bot es privado.\n\n"
            f"Tu ID de Telegram es: <code>{user_id}</code>\n"
            f"Pasáselo al admin para que te agregue.",
            parse_mode="HTML",
        )
        return
    await update.message.reply_text(HELP_AUTHORIZED, parse_mode="HTML")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text(
            f"No estás autorizado.\n\n"
            f"Tu ID de Telegram es: <code>{user_id}</code>\n"
            f"Pasáselo al admin para que te agregue.",
            parse_mode="HTML",
        )
        return
    await update.message.reply_text(HELP_AUTHORIZED, parse_mode="HTML")
