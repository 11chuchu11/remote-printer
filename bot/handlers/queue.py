from telegram import Update
from telegram.ext import ContextTypes
from config import PRINTER, is_allowed
from cups import get_status, get_ink, get_queue, cancel_job, cancel_all
from storage import get_history, log_event
from handlers.common import reply_unauthorized


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await reply_unauthorized(update)
        return

    status = get_status(PRINTER)
    ink = get_ink(PRINTER)

    msg = f"<b>Estado:</b>\n<code>{status}</code>"
    if ink:
        msg += f"\n\n<b>Tinta:</b>\n<code>{ink}</code>"

    await update.message.reply_text(msg, parse_mode="HTML")


async def handle_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await reply_unauthorized(update)
        return

    jobs = get_queue(PRINTER)
    if not jobs:
        await update.message.reply_text("Cola vacía.")
        return

    lines = "\n".join(jobs)
    await update.message.reply_text(f"<b>Cola de impresión:</b>\n<code>{lines}</code>", parse_mode="HTML")


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await reply_unauthorized(update)
        return

    user_id = update.effective_user.id
    if context.args:
        job_id = context.args[0]
        try:
            cancel_job(job_id)
            log_event("INFO", "cancel_job", user_id, job_id)
            await update.message.reply_text(f"Trabajo {job_id} cancelado.")
        except Exception as e:
            log_event("ERROR", "cancel_job_failed", user_id, f"{job_id}: {e}")
            await update.message.reply_text(f"Error al cancelar {job_id}: {e}")
    else:
        count = cancel_all(PRINTER)
        log_event("INFO", "cancel_all", user_id, f"{count} trabajos")
        if count:
            await update.message.reply_text(f"{count} trabajo(s) cancelado(s).")
        else:
            await update.message.reply_text("No había trabajos en cola.")


async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await reply_unauthorized(update)
        return

    rows = get_history(update.effective_user.id)
    if not rows:
        await update.message.reply_text("Sin historial.")
        return

    lines = "\n".join(
        f"{r['printed_at']}  {r['status'].upper()}  {r['filename']}"
        for r in rows
    )
    await update.message.reply_text(f"<b>Historial:</b>\n<code>{lines}</code>", parse_mode="HTML")
