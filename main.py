from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Configuración del bot (comentado para formato de texto)
# BOT_TOKEN = "<TU_TOKEN_DE_BOT_AQUÍ>"

# Función inicial: selección de idioma
def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Español", callback_data='lang_es')],
        [InlineKeyboardButton("English", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Bienvenido a Crypto Signal Bot! 🌍\n\nPor favor, selecciona tu idioma:",
        reply_markup=reply_markup
    )

# Función para manejar la selección de idioma
def select_language(update: Update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'lang_es':
        message = "Idioma seleccionado: Español.\n\nSeleccione un plan para continuar:"
    elif query.data == 'lang_en':
        message = "Language selected: English.\n\nSelect a plan to continue:"

    keyboard = [
        [InlineKeyboardButton("🔥 Plan Fire Scalping", callback_data='plan_fire')],
        [InlineKeyboardButton("💎 Plan Elite Scalping Intradía", callback_data='plan_elite')],
        [InlineKeyboardButton("🌊 Plan Delta Swing Trading", callback_data='plan_delta')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )

# Función para mostrar detalles del plan
def show_plan_details(update: Update, context):
    query = update.callback_query
    query.answer()

    plans = {
        'plan_fire': {
            'title': "🔥 Plan Fire Scalping",
            'details': "- Mensual: $17/mes\n- Anual: $132.60 (35% descuento)\nOperaciones rápidas con alta intensidad."
        },
        'plan_elite': {
            'title': "💎 Plan Elite Scalping Intradía",
            'details': "- Mensual: $31/mes\n- Anual: $241 (35% descuento)\nAlta precisión y diversificación."
        },
        'plan_delta': {
            'title': "🌊 Plan Delta Swing Trading",
            'details': "- Mensual: $37/mes\n- Anual: $290 (35% descuento)\nOperaciones sostenibles a mediano plazo."
        }
    }

    plan = plans.get(query.data, {})
    if plan:
        keyboard = [
            [InlineKeyboardButton("Volver", callback_data='go_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text=f"{plan['title']}\n\n{plan['details']}",
            reply_markup=reply_markup
        )

# Función para regresar al menú de planes
def go_back(update: Update, context):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🔥 Plan Fire Scalping", callback_data='plan_fire')],
        [InlineKeyboardButton("💎 Plan Elite Scalping Intradía", callback_data='plan_elite')],
        [InlineKeyboardButton("🌊 Plan Delta Swing Trading", callback_data='plan_delta')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Seleccione un plan para continuar:",
        reply_markup=reply_markup
    )

# Configuración del bot principal
def main():
    # up = Updater(BOT_TOKEN, use_context=True)  # Comentado para formato de texto
    # dp = up.dispatcher

    # Manejo de comandos y callbacks
    # dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(CallbackQueryHandler(select_language, pattern='^lang_.*'))
    # dp.add_handler(CallbackQueryHandler(show_plan_details, pattern='^plan_.*'))
    # dp.add_handler(CallbackQueryHandler(go_back, pattern='^go_back$'))

    # up.start_polling()  # Comentado para formato de texto
    # up.idle()  # Comentado para formato de texto

    pass

if __name__ == '__main__':
    main()
