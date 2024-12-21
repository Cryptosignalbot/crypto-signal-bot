import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Token del bot de Telegram
BOT_TOKEN = "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ"

# Función de inicio
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Menú Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¡Bienvenido al Bot! Selecciona una opción para continuar:",
        reply_markup=reply_markup
    )

# Función para mostrar el menú principal
async def main_menu(update, context):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Opción 1", callback_data="option_1")],
        [InlineKeyboardButton("Opción 2", callback_data="option_2")],
        [InlineKeyboardButton("↩️ Volver", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Menú Principal:",
        reply_markup=reply_markup
    )

# Función principal
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers básicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(start, pattern="^start$"))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
