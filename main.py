import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import requests
from datetime import datetime, timedelta

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

# Función para manejar el comando /start
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Planes", callback_data='plans')],
        [InlineKeyboardButton("Asistencia", url="https://t.me/tu_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "¡Bienvenido a Crypto Signal Bot! 🚀\n\nSelecciona una opción para comenzar:",
        reply_markup=reply_markup
    )

# Función para mostrar los planes
def show_plans(update, context):
    query = update.callback_query
    query.answer()
    message = (
        "Nuestros planes de trading:\n\n"
        "🔥 *Plan Fire Scalping*: $17/mes o $132.60/año\n"
        "💎 *Plan Elite Scalping Intradía*: $31/mes o $241/año\n"
        "🌊 *Plan Delta Swing Trading*: $37/mes o $290/año\n\n"
        "Para suscribirte, escribe /subscribe y sigue las instrucciones."
    )
    query.edit_message_text(text=message, parse_mode="Markdown")

# Función para manejar suscripciones
def subscribe(update, context):
    keyboard = [
        [InlineKeyboardButton("Pagar con Binance Pay", callback_data='pay_binance')],
        [InlineKeyboardButton("Cancelar", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Selecciona tu método de pago:",
        reply_markup=reply_markup
    )

# Función para manejar pagos con Binance Pay
def handle_payment(update, context):
    query = update.callback_query
    query.answer()

    # Ejemplo de validación de pago (se debe adaptar con la API de Binance Pay)
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.get("https://api.binance.com/sapi/v1/pay/transactions", headers=headers)
    payments = response.json()

    if payments.get("success"):
        query.edit_message_text("Pago recibido. Acceso habilitado a tu plan.")
        # Lógica para asignar usuario al grupo y tema correspondiente
        # Ejemplo:
        # bot.add_chat_member(chat_id=GROUP_CHAT_ID, user_id=update.effective_user.id, custom_title="Miembro")
    else:
        query.edit_message_text("No se pudo verificar el pago. Intenta nuevamente.")

# Configuración de recordatorios de renovación
def send_renewal_reminder(bot, user_id, plan_name, expiry_date):
    today = datetime.now()
    if expiry_date - today <= timedelta(days=3):
        bot.send_message(chat_id=user_id, text=f"Tu suscripción al {plan_name} está por vencer. ¡Renueva para no perder acceso!")

# Función principal para configurar el bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Manejo de comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))

    # Manejo de callbacks
    dp.add_handler(CallbackQueryHandler(show_plans, pattern='^plans$'))
    dp.add_handler(CallbackQueryHandler(handle_payment, pattern='^pay_binance$'))

    # Inicia el bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
