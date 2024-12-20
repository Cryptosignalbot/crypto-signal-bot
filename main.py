import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "TU_BOT_TOKEN"  # Reemplaza con tu token real

# Configuración del logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Función para el comando /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔥 Detalles Plan Fire Scalping", callback_data='fire'),
            InlineKeyboardButton("💎 Detalles Plan Elite Scalping Intradía", callback_data='elite'),
            InlineKeyboardButton("🌊 Detalles Plan Delta Swing Trading", callback_data='delta')
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data='back'),
            InlineKeyboardButton("🛠️ Asistencia", url="https://t.me/tu_admin")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona un plan:", reply_markup=reply_markup)

# Función para manejar detalles de los planes
async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan = query.data
    if plan == 'fire':
        text = (
            "🔥 *Plan Fire Scalping*\n\n"
            "💵 $11/mes\n💵 $132/año\n\n"
            "⚡ Características:\n"
            "- Alta intensidad para traders agresivos.\n"
            "- Diversificación en 5 criptomonedas clave.\n\n"
            "🔗 [Más detalles en el sitio web](https://tusitio.com/fire)"
        )
    elif plan == 'elite':
        text = (
            "💎 *Plan Elite Scalping Intradía*\n\n"
            "✅ Recomendado - 50% de descuento\n"
            "💵 $21/mes\n💵 $126/año (antes $252)\n\n"
            "⚡ Características:\n"
            "- Precisión extrema: 99.10% de éxito.\n"
            "- Diseñado para traders experimentados.\n\n"
            "🔗 [Más detalles en el sitio web](https://tusitio.com/elite)"
        )
    elif plan == 'delta':
        text = (
            "🌊 *Plan Delta Swing Trading*\n\n"
            "💵 $31/mes\n💵 $372/año\n\n"
            "⚡ Características:\n"
            "- Ideal para operaciones prolongadas.\n"
            "- Aprovecha tendencias de mediano plazo.\n\n"
            "🔗 [Más detalles en el sitio web](https://tusitio.com/delta)"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("Mensual", callback_data=f'{plan}_monthly'),
            InlineKeyboardButton("Anual", callback_data=f'{plan}_yearly')
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data='menu'),
            InlineKeyboardButton("🛠️ Asistencia", url="https://t.me/tu_admin")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

# Configuración principal del bot
async def main():
    # Crea la aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Manejo de comandos
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(show_details, pattern='^(fire|elite|delta)$'))
    application.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))

    # Ejecuta el bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
