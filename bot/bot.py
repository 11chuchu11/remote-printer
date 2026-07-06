import os
import logging
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_IDS = [int(x) for x in os.environ["ALLOWED_USER_IDS"].split(",")]
PRINTER = os.environ.get("CUPS_PRINTER", "DCPT300")
ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".txt")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_IDS:
        await update.message.reply_text("No autorizado.")
        logging.warning(f"Intento de acceso no autorizado: {user_id}")
        return

    doc = update.message.document
    filename = doc.file_name or "archivo"
    if not filename.lower().endswith(ALLOWED_EXT):
        await update.message.reply_text("Solo acepto PDF, JPG, PNG o TXT.")
        return

    file = await doc.get_file()
    local_path = f"/tmp/{filename}"
    await file.download_to_drive(local_path)

    try:
        subprocess.run(["lp", "-d", PRINTER, local_path], check=True, timeout=30)
        await update.message.reply_text(f"Imprimiendo: {filename}")
    except Exception as e:
        await update.message.reply_text(f"Error al imprimir: {e}")
    finally:
        os.remove(local_path)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()
