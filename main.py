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

# Función para mostrar detalles de un plan
async def plan_details(update, context):
    query = update.callback_query
    plan = query.data.split("_")[0]
    details = {
        "fire_scalping": {
            "title": "🔥 Fire Scalping",
            "price_monthly": "$17/mes",
            "price_annual": "$132.60/año",
            "description": "Estrategias rápidas para traders agresivos."
        },
        "elite_scalping": {
            "title": "💎 Elite Scalping Intradía",
            "price_monthly": "$31/mes",
            "price_annual": "$241/año (50% de descuento)",
            "description": "Ideal para operaciones intradía con alta precisión."
        },
        "delta_swing": {
            "title": "🌊 Delta Swing Trading",
            "price_monthly": "$37/mes",
            "price_annual": "$290/año",
            "description": "Enfoque relajado para operaciones sostenibles."
        }
    }
    plan_data = details.get(plan, {})
    if not plan_data:
        await query.answer("Detalles no disponibles.", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("Mensual", callback_data=f"subscribe_{plan}_monthly")],
        [InlineKeyboardButton("Anual", callback_data=f"subscribe_{plan}_annual")],
        [InlineKeyboardButton("↩️ Volver", callback_data="show_plans")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"{plan_data['title']}\n\n"
        f"{plan_data['description']}\n\n"
        f"Precios:\n"
        f"Mensual: {plan_data['price_monthly']}\n"
        f"Anual: {plan_data['price_annual']}",
        reply_markup=reply_markup
    )

# Función para suscripciones
async def subscribe(update, context):
    query = update.callback_query
    plan, duration = query.data.split("_")[1:]
    await query.answer(f"Suscripción al plan {plan} ({duration}).", show_alert=True)

# Función principal
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_plans, pattern="^show_plans$"))
    application.add_handler(CallbackQueryHandler(plan_details, pattern="^(fire_scalping|elite_scalping|delta_swing)_details$"))
    application.add_handler(CallbackQueryHandler(subscribe, pattern="^subscribe_(fire_scalping|elite_scalping|delta_swing)_(monthly|annual)$"))

    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            loop = asyncio.get_event_loop()
            loop.create_task(main())
        else:
            raise
