import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from binance.client import Client

# Configuración del bot
BOT_TOKEN = "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ"
API_KEY = "JkizCjtG5THCu9BQG5fjZFfEAPJWwVFbVmh9CCl2mWUGMWSbElUyeUh6LqTjBxsz"
SECRET_KEY = "Hw7m3zbbQSBSzubUqzoTuxb0zeNo9HO5ox76EdkSq4jTrtB8DMQ5ITXZmTH7Wgp9"
GROUP_CHAT_ID = "-1002450039878"

# IDs de temas
TOPICS = {
    "Fire Scalping": {"BTC": 4, "ETH": 7, "ADA": 9, "XRP": 2, "BNB": 5},
    "Elite Scalping Intradía": {"BTC": 11, "ETH": 19, "ADA": 13, "XRP": 17, "BNB": 15},
    "Delta Swing Trading": {"BTC": 20, "ETH": 28, "ADA": 26, "XRP": 24, "BNB": 22},
}

# Configuración del logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura el cliente de Binance
client = Client(api_key=API_KEY, api_secret=SECRET_KEY)

# Función para manejar el comando /start
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Español 🇪🇸", callback_data='lang_es')],
        [InlineKeyboardButton("Inglés 🇬🇧", callback_data='lang_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "¡Bienvenido a Crypto Signal Bot! Por favor, selecciona tu idioma:",
        reply_markup=reply_markup
    )

# Función para manejar la selección de idioma
def set_language(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'lang_es':
        context.user_data['language'] = 'es'
        query.edit_message_text("Idioma establecido a Español 🇪🇸. Selecciona una opción:")
    elif query.data == 'lang_en':
        context.user_data['language'] = 'en'
        query.edit_message_text("Language set to English 🇬🇧. Select an option:")

    keyboard = [
        [InlineKeyboardButton("Planes de Trading", callback_data='plans')],
        [InlineKeyboardButton("Asistencia", url="https://t.me/tu_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_reply_markup(reply_markup=reply_markup)

# Función para mostrar los planes
def show_plans(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    message = (
        "Nuestros planes de trading:\n\n"
        "🔥 *Plan Fire Scalping*: $17/mes o $132.60/año\n"
        "💎 *Plan Elite Scalping Intradía*: $31/mes o $241/año\n"
        "🌊 *Plan Delta Swing Trading*: $37/mes o $290/año\n\n"
        "Selecciona un plan para más detalles."
    )
    keyboard = [
        [InlineKeyboardButton("Ver Plan Fire Scalping", callback_data='fire_scalping')],
        [InlineKeyboardButton("Ver Plan Elite Scalping", callback_data='elite_scalping')],
        [InlineKeyboardButton("Ver Plan Delta Swing", callback_data='delta_swing')],
        [InlineKeyboardButton("Regresar", callback_data='start')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=message, parse_mode="Markdown", reply_markup=reply_markup)

# Función para mostrar detalles del plan
def show_plan_details(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    plan_details = {
        "fire_scalping": "🔥 *Plan Fire Scalping*:\n\n- $17/mes o $132.60/año\n- Alta frecuencia de operaciones para traders agresivos.",
        "elite_scalping": "💎 *Plan Elite Scalping Intradía*:\n\n- $31/mes o $241/año\n- Ideal para intradía y scalping con alta precisión.",
        "delta_swing": "🌊 *Plan Delta Swing Trading*:\n\n- $37/mes o $290/año\n- Diseñado para operaciones de mediano plazo.",
    }
    query.edit_message_text(
        text=plan_details.get(query.data, "Detalles del plan no disponibles."),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Pagar con Binance Pay", callback_data='pay_binance')],
            [InlineKeyboardButton("Regresar", callback_data='plans')],
        ])
    )

# Función para manejar pagos
def handle_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        transactions = client.get_payments_history(limit=10)
        if transactions:
            query.edit_message_text("Pago recibido. Acceso habilitado a tu plan.")
        else:
            query.edit_message_text("No se encontró ninguna transacción válida. Intenta nuevamente.")
    except Exception as e:
        query.edit_message_text(f"Error verificando el pago: {e}")

# Función principal para configurar el bot
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(set_language, pattern='^lang_'))
    dp.add_handler(CallbackQueryHandler(show_plans, pattern='^plans$'))
    dp.add_handler(CallbackQueryHandler(show_plan_details, pattern='^(fire_scalping|elite_scalping|delta_swing)$'))
    dp.add_handler(CallbackQueryHandler(handle_payment, pattern='^pay_binance$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

