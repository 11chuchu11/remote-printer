import os
import re
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import PRINTER, ALLOWED_EXT, is_allowed, get_user_name
from storage import log_event, get_print_config
from handlers.common import reply_unauthorized
from handlers.keyboards import job_keyboard, job_text

_PAGE_RANGE_RE = re.compile(r'^\d+(-\d+)?(,\d+(-\d+)?)*$')


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        log_event("WARNING", "unauthorized", user_id)
        await reply_unauthorized(update)
        logging.warning(f"Acceso no autorizado: {user_id}")
        return

    doc = update.message.document
    filename = os.path.basename(doc.file_name or "archivo")

    if not filename.lower().endswith(ALLOWED_EXT):
        log_event("WARNING", "invalid_ext", user_id, filename)
        await update.message.reply_text("Solo acepto PDF, JPG, PNG o TXT.")
        return

    log_event("INFO", "file_received", user_id, filename)

    # cancel previous pending job if any
    prev = context.user_data.get("pending")
    if prev:
        path = prev.get("path")
        if path and os.path.exists(path):
            os.remove(path)

    file = await doc.get_file()
    local_path = f"/tmp/{user_id}_{filename}"
    await file.download_to_drive(local_path)

    cfg = get_print_config(user_id)
    caption = (update.message.caption or "").strip()
    cfg["pages"] = caption if _PAGE_RANGE_RE.match(caption) else "all"

    name = get_user_name(user_id)
    context.user_data["pending"] = {
        "path": local_path,
        "filename": filename,
        "config": cfg,
        "name": name,
    }

    await update.message.reply_text(
        job_text(filename, cfg, name),
        reply_markup=job_keyboard(cfg),
        parse_mode="HTML",
    )
