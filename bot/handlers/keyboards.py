from telegram import InlineKeyboardButton, InlineKeyboardMarkup

BACK_BTN = [[InlineKeyboardButton("🔙 Menú", callback_data="menu:back")]]


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Estado",    callback_data="menu:status"),
            InlineKeyboardButton("📋 Cola",      callback_data="menu:queue"),
        ],
        [
            InlineKeyboardButton("📜 Historial", callback_data="menu:history"),
            InlineKeyboardButton("⚙️ Config",    callback_data="menu:config"),
        ],
        [InlineKeyboardButton("❌ Cancelar todo", callback_data="menu:cancel")],
    ])


def menu_text(name: str | None = None) -> str:
    greeting = f"Hola, <b>{name}</b>! " if name else ""
    return f"{greeting}🖨️ ¿Qué hacemos?"

PAGES_CYCLE = ["all", "odd", "even"]
PAGES_LABELS = {"all": "📑 Todas", "odd": "📑 Impares", "even": "📑 Pares"}

SIDES_CYCLE = ["one-sided", "two-sided-long-edge", "two-sided-short-edge"]
SIDES_LABELS = {
    "one-sided":            "Simple",
    "two-sided-long-edge":  "Doble (largo)",
    "two-sided-short-edge": "Doble (corto)",
}
MEDIA_CYCLE = ["A4", "Letter", "A5", "Legal"]
COLOR_LABELS = {"color": "🎨 Color", "gray": "⬛ Grises"}


def next_in_cycle(cycle: list, current: str) -> str:
    idx = cycle.index(current) if current in cycle else 0
    return cycle[(idx + 1) % len(cycle)]


def _pages_label(pages: str) -> str:
    if pages in PAGES_LABELS:
        return PAGES_LABELS[pages]
    return f"📑 Págs: {pages}"


def job_keyboard(cfg: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="pj:copies_dec"),
            InlineKeyboardButton(f"{cfg['copies']} copia(s)", callback_data="pj:noop"),
            InlineKeyboardButton("➕", callback_data="pj:copies_inc"),
        ],
        [InlineKeyboardButton(COLOR_LABELS[cfg["color"]], callback_data="pj:color")],
        [InlineKeyboardButton(f"📄 {SIDES_LABELS.get(cfg['sides'], cfg['sides'])}", callback_data="pj:sides")],
        [InlineKeyboardButton(f"📐 {cfg['media']}", callback_data="pj:media")],
        [InlineKeyboardButton(_pages_label(cfg.get("pages", "all")), callback_data="pj:pages")],
        [
            InlineKeyboardButton("✅ Imprimir", callback_data="pj:confirm"),
            InlineKeyboardButton("❌ Cancelar", callback_data="pj:cancel"),
        ],
    ])


def config_keyboard(cfg: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="cfg:copies_dec"),
            InlineKeyboardButton(f"{cfg['copies']} copia(s)", callback_data="cfg:noop"),
            InlineKeyboardButton("➕", callback_data="cfg:copies_inc"),
        ],
        [InlineKeyboardButton(COLOR_LABELS[cfg["color"]], callback_data="cfg:color")],
        [InlineKeyboardButton(f"📄 {SIDES_LABELS.get(cfg['sides'], cfg['sides'])}", callback_data="cfg:sides")],
        [InlineKeyboardButton(f"📐 {cfg['media']}", callback_data="cfg:media")],
        [InlineKeyboardButton("✅ Listo", callback_data="cfg:done")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu:back")],
    ])


def job_text(filename: str, cfg: dict, name: str | None = None) -> str:
    pages = cfg.get("pages", "all")
    pages_display = PAGES_LABELS.get(pages, pages)
    greeting = f"Hola, <b>{name}</b>! " if name else ""
    return (
        f"{greeting}📄 <b>{filename}</b>\n\n"
        f"Ajustá la configuración antes de imprimir:\n"
        f"  Copias:  {cfg['copies']}\n"
        f"  Color:   {cfg['color']}\n"
        f"  Lados:   {SIDES_LABELS.get(cfg['sides'], cfg['sides'])}\n"
        f"  Papel:   {cfg['media']}\n"
        f"  Páginas: {pages_display}"
    )


def config_text(cfg: dict) -> str:
    return (
        f"⚙️ <b>Configuración predeterminada</b>\n\n"
        f"  Copias: {cfg['copies']}\n"
        f"  Color:  {cfg['color']}\n"
        f"  Lados:  {SIDES_LABELS.get(cfg['sides'], cfg['sides'])}\n"
        f"  Papel:  {cfg['media']}\n\n"
        f"Cada cambio se guarda automáticamente."
    )
