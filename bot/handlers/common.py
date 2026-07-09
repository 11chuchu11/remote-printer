from telegram import Update
from cups import get_status, get_ink, get_queue


async def reply_unauthorized(update: Update) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"No estás autorizado.\n\n"
        f"Tu ID de Telegram es: <code>{user_id}</code>\n"
        f"Pasáselo al admin para que te agregue.",
        parse_mode="HTML",
    )


def format_status_message(printer: str) -> str:
    status = get_status(printer)
    jobs = get_queue(printer)
    ink = get_ink(printer)

    msg = f"<b>Estado:</b>\n<code>{status}</code>"
    msg += f"\n\n<b>Trabajos en cola:</b> {len(jobs)}"
    if ink:
        msg += f"\n\n<b>Tinta:</b>\n<code>{ink}</code>"

    return msg
