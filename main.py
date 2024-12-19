import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
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
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Planes", callback_data='plans')],
        [InlineKeyboardButton("Asistencia", url="https://t.me/tu_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¡Bienvenido a Crypto Signal Bot! 🚀\n\nSelecciona una opción para comenzar:",
        reply_markup=reply_markup
    )

# Función para mostrar los planes
async def show_plans(update, context):
    query = update.callback_query
    await query.answer()
    message = (
        "Nuestros planes de trading:\n\n"
        "🔥 *Plan Fire Scalping*: $17/mes o $132.60/año\n"
        "💎 *Plan Elite Scalping Intradía*: $31/mes o $241/año\n"
        "🌊 *Plan Delta Swing Trading*: $37/mes o $290/año\n\n"
        "Para suscribirte, escribe /subscribe y sigue las instrucciones."
    )
    await query.edit_message_text(text=message, parse_mode="Markdown")

# Función para manejar suscripciones
async def subscribe(update, context):
    keyboard = [
        [InlineKeyboardButton("Pagar con Binance Pay", callback_data='pay_binance')],
        [InlineKeyboardButton("Cancelar", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Selecciona tu método de pago:",
        reply_markup=reply_markup
    )

# Función para manejar pagos con Binance Pay
async def handle_payment(update, context):
    query = update.callback_query
    await query.answer()

    try:
        # Ejemplo de validación de pagos con Binance Pay
        transactions = client.get_payments_history(limit=10)
        if transactions:
            await query.edit_message_text("Pago recibido. Acceso habilitado a tu plan.")
        else:
            await query.edit_message_text("No se encontró ninguna transacción válida. Intenta nuevamente.")
    except Exception as e:
        await query.edit_message_text(f"Error verificando el pago: {e}")

# Función principal para configurar el bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Manejo de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))

    # Manejo de callbacks
    application.add_handler(CallbackQueryHandler(show_plans, pattern='^plans$'))
    application.add_handler(CallbackQueryHandler(handle_payment, pattern='^pay_binance$'))

    # Inicia el bot
    application.run_polling()

if __name__ == '__main__':
    main()

