from telegram import Update
from telegram.ext import ContextTypes
from config import is_allowed
from storage import get_print_config
from handlers.common import reply_unauthorized
from handlers.keyboards import config_keyboard, config_text


async def handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await reply_unauthorized(update)
        return

    cfg = get_print_config(user_id)
    await update.message.reply_text(
        config_text(cfg),
        reply_markup=config_keyboard(cfg),
        parse_mode="HTML",
    )
