import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from config import TOKEN
from storage import init_db
from handlers.print import handle_document
from handlers.queue import handle_status, handle_cancel, handle_queue, handle_history, handle_ink
from handlers.config import handle_config
from handlers.help import handle_start, handle_help
from handlers.callbacks import handle_callback

logging.basicConfig(level=logging.INFO)


def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("cancel", handle_cancel))
    app.add_handler(CommandHandler("queue", handle_queue))
    app.add_handler(CommandHandler("history", handle_history))
    app.add_handler(CommandHandler("tinta", handle_ink))
    app.add_handler(CommandHandler("config", handle_config))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
