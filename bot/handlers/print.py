import os
import shutil
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import PRINTER, ALLOWED_EXT, FILES_DIR, PERSIST_FILES, is_allowed
from cups import print_file
from storage import log_print, log_event, get_print_config
from handlers.common import reply_unauthorized


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

    file = await doc.get_file()
    local_path = f"/tmp/{filename}"
    await file.download_to_drive(local_path)

    stored_path = None
    if PERSIST_FILES:
        dest_dir = os.path.join(FILES_DIR, str(user_id))
        os.makedirs(dest_dir, exist_ok=True)
        stored_path = os.path.join(dest_dir, filename)
        # avoid overwriting — prefix with timestamp if exists
        if os.path.exists(stored_path):
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_path = os.path.join(dest_dir, f"{ts}_{filename}")
        shutil.copy2(local_path, stored_path)
        log_event("INFO", "file_stored", user_id, stored_path)

    try:
        print_file(PRINTER, local_path, get_print_config(user_id))
        log_print(user_id, filename, "ok", stored_path)
        await update.message.reply_text(f"Imprimiendo: {filename}")
    except Exception as e:
        log_print(user_id, filename, "error", stored_path)
        await update.message.reply_text(f"Error al imprimir: {e}")
    finally:
        os.remove(local_path)
