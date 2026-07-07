import os
import shutil
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import PRINTER, FILES_DIR, PERSIST_FILES, is_allowed, get_user_name
from cups import print_file, get_status, get_ink, get_queue, cancel_all
from storage import log_print, log_event, get_print_config, set_print_config, get_history
from handlers.keyboards import (
    job_keyboard, config_keyboard, job_text, config_text,
    menu_keyboard, menu_text,
    SIDES_CYCLE, MEDIA_CYCLE, PAGES_CYCLE, next_in_cycle, BACK_BTN,
)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not is_allowed(user_id):
        await query.answer("No autorizado.", show_alert=True)
        return

    await query.answer()

    if ":" not in query.data:
        return

    prefix, action = query.data.split(":", 1)

    if action == "noop":
        return

    if prefix == "pj":
        await _job_callback(query, context, action, user_id)
    elif prefix == "cfg":
        await _cfg_callback(query, context, action, user_id)
    elif prefix == "menu":
        await _menu_callback(query, action, user_id)


async def _job_callback(query, context, action: str, user_id: int):
    pending = context.user_data.get("pending")
    if not pending:
        await query.edit_message_text("Este trabajo ya no está disponible.")
        return

    cfg = pending["config"]

    if action == "copies_inc":
        cfg["copies"] = min(99, cfg["copies"] + 1)
    elif action == "copies_dec":
        cfg["copies"] = max(1, cfg["copies"] - 1)
    elif action == "color":
        cfg["color"] = "gray" if cfg["color"] == "color" else "color"
    elif action == "sides":
        cfg["sides"] = next_in_cycle(SIDES_CYCLE, cfg["sides"])
    elif action == "media":
        cfg["media"] = next_in_cycle(MEDIA_CYCLE, cfg["media"])
    elif action == "pages":
        current = cfg.get("pages", "all")
        # custom ranges set via caption cycle back to "all"
        cfg["pages"] = next_in_cycle(PAGES_CYCLE, current if current in PAGES_CYCLE else "all")
    elif action == "confirm":
        await _do_print(query, context, pending, cfg, user_id)
        return
    elif action == "cancel":
        _cleanup(pending)
        context.user_data.pop("pending", None)
        await query.edit_message_text("❌ Cancelado.")
        return

    await query.edit_message_text(
        job_text(pending["filename"], cfg),
        reply_markup=job_keyboard(cfg),
        parse_mode="HTML",
    )


async def _do_print(query, context, pending: dict, cfg: dict, user_id: int):
    path = pending["path"]
    filename = pending["filename"]

    if not os.path.exists(path):
        await query.edit_message_text("El archivo ya no está disponible. Reenvialo.")
        context.user_data.pop("pending", None)
        return

    stored_path = None
    if PERSIST_FILES:
        dest_dir = os.path.join(FILES_DIR, str(user_id))
        os.makedirs(dest_dir, exist_ok=True)
        stored_path = os.path.join(dest_dir, filename)
        if os.path.exists(stored_path):
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_path = os.path.join(dest_dir, f"{ts}_{filename}")
        shutil.copy2(path, stored_path)
        log_event("INFO", "file_stored", user_id, stored_path)

    name = pending.get("name")
    try:
        print_file(PRINTER, path, cfg)
        log_print(user_id, filename, "ok", stored_path)
        msg = f"✅ ¡En camino, <b>{name}</b>! Se está imprimiendo <b>{filename}</b>." if name \
            else f"✅ Imprimiendo: <b>{filename}</b>."
        await query.edit_message_text(msg, parse_mode="HTML")
    except Exception as e:
        log_print(user_id, filename, "error", stored_path)
        msg = f"❌ <b>{name}</b>, no se pudo imprimir <b>{filename}</b>.\nMotivo: {e}" if name \
            else f"❌ No se pudo imprimir <b>{filename}</b>.\nMotivo: {e}"
        await query.edit_message_text(msg, parse_mode="HTML")
    finally:
        _cleanup(pending)
        context.user_data.pop("pending", None)


async def _cfg_callback(query, context, action: str, user_id: int):
    cfg = get_print_config(user_id)

    if action == "done":
        await query.edit_message_text("✅ Configuración guardada.")
        return

    if action == "copies_inc":
        cfg["copies"] = min(99, cfg["copies"] + 1)
        set_print_config(user_id, "copies", cfg["copies"])
    elif action == "copies_dec":
        cfg["copies"] = max(1, cfg["copies"] - 1)
        set_print_config(user_id, "copies", cfg["copies"])
    elif action == "color":
        cfg["color"] = "gray" if cfg["color"] == "color" else "color"
        set_print_config(user_id, "color", cfg["color"])
    elif action == "sides":
        cfg["sides"] = next_in_cycle(SIDES_CYCLE, cfg["sides"])
        set_print_config(user_id, "sides", cfg["sides"])
    elif action == "media":
        cfg["media"] = next_in_cycle(MEDIA_CYCLE, cfg["media"])
        set_print_config(user_id, "media", cfg["media"])

    log_event("INFO", "config_changed", user_id, action)
    await query.edit_message_text(
        config_text(cfg),
        reply_markup=config_keyboard(cfg),
        parse_mode="HTML",
    )


async def _menu_callback(query, action: str, user_id: int):
    if action == "back":
        await query.edit_message_text(
            menu_text(get_user_name(user_id)),
            reply_markup=menu_keyboard(),
            parse_mode="HTML",
        )
        return

    back = InlineKeyboardMarkup(BACK_BTN)

    if action == "status":
        status = get_status(PRINTER)
        ink = get_ink(PRINTER)
        msg = f"<b>Estado:</b>\n<code>{status}</code>"
        if ink:
            msg += f"\n\n<b>Tinta:</b>\n<code>{ink}</code>"
        await query.edit_message_text(msg, reply_markup=back, parse_mode="HTML")

    elif action == "queue":
        jobs = get_queue(PRINTER)
        if jobs:
            msg = f"<b>Cola de impresión:</b>\n<code>{chr(10).join(jobs)}</code>"
        else:
            msg = "Cola vacía."
        await query.edit_message_text(msg, reply_markup=back, parse_mode="HTML")

    elif action == "history":
        rows = get_history(user_id)
        if rows:
            lines = "\n".join(
                f"{r['printed_at']}  {r['status'].upper()}  {r['filename']}" for r in rows
            )
            msg = f"<b>Historial:</b>\n<code>{lines}</code>"
        else:
            msg = "Sin historial."
        await query.edit_message_text(msg, reply_markup=back, parse_mode="HTML")

    elif action == "config":
        from storage import get_print_config
        cfg = get_print_config(user_id)
        await query.edit_message_text(
            config_text(cfg),
            reply_markup=config_keyboard(cfg),
            parse_mode="HTML",
        )

    elif action == "cancel":
        count = cancel_all(PRINTER)
        log_event("INFO", "cancel_all", user_id, f"{count} trabajos")
        msg = f"❌ {count} trabajo(s) cancelado(s)." if count else "No había trabajos en cola."
        await query.edit_message_text(msg, reply_markup=back, parse_mode="HTML")


def _cleanup(pending: dict):
    path = pending.get("path")
    if path and os.path.exists(path):
        os.remove(path)
