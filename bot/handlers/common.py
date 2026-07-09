from telegram import Update
from cups import get_status, get_ink, get_queue
from storage import get_ink_estimate, BLACK_YIELD_PAGES, COLOR_YIELD_PAGES


async def reply_unauthorized(update: Update) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"No estás autorizado.\n\n"
        f"Tu ID de Telegram es: <code>{user_id}</code>\n"
        f"Pasáselo al admin para que te agregue.",
        parse_mode="HTML",
    )


def format_ink_message() -> str:
    est = get_ink_estimate()
    return (
        "<b>Tinta (estimado):</b>\n"
        f"  Negro: ~{est['black_pct']}% restante ({est['black_pages']}/{BLACK_YIELD_PAGES} pág. desde el último rellenado)\n"
        f"  Color: ~{est['color_pct']}% restante ({est['color_pages']}/{COLOR_YIELD_PAGES} pág. desde el último rellenado)\n"
        f"  Último rellenado: {est['reset_at']}\n\n"
        "<i>Estimado por conteo de páginas, no es una lectura real del tanque. "
        "Reiniciá el contador con /tinta reset al rellenar.</i>"
    )


def format_status_message(printer: str) -> str:
    status = get_status(printer)
    jobs = get_queue(printer)
    ink = get_ink(printer)

    msg = f"<b>Estado:</b>\n<code>{status}</code>"
    msg += f"\n\n<b>Trabajos en cola:</b> {len(jobs)}"
    if ink:
        msg += f"\n\n<b>Tinta:</b>\n<code>{ink}</code>"
    else:
        msg += f"\n\n{format_ink_message()}"

    return msg
