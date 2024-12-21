import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Token del bot de Telegram
BOT_TOKEN = "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ"

# Función de inicio
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Planes", callback_data="show_plans")],
        [InlineKeyboardButton("Contacto con la administradora", url="https://t.me/tu_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bienvenido a Crypto Signal Bot! 🚀\n\nSelecciona una opción para continuar:",
        reply_markup=reply_markup
    )

# Función para mostrar planes
async def show_plans(update, context):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🔥 Fire Scalping", callback_data="fire_scalping_details")],
        [InlineKeyboardButton("💎 Elite Scalping Intradía (Recomendado)", callback_data="elite_scalping_details")],
        [InlineKeyboardButton("🌊 Delta Swing Trading", callback_data="delta_swing_details")],
        [InlineKeyboardButton("↩️ Volver", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Nuestros planes de trading:\n\n"
        "🔥 *Plan Fire Scalping*: $17/mes o $132.60/año\n"
        "💎 *Plan Elite Scalping Intradía*: $31/mes o $241/año (50% de descuento anual)\n"
        "🌊 *Plan Delta Swing Trading*: $37/mes o $290/año\n",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Función principal
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_plans, pattern="^show_plans$"))

    # Ejecutar el bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

