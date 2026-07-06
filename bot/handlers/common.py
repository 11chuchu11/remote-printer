from telegram import Update


async def reply_unauthorized(update: Update) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"No estás autorizado.\n\n"
        f"Tu ID de Telegram es: <code>{user_id}</code>\n"
        f"Pasáselo al admin para que te agregue.",
        parse_mode="HTML",
    )
