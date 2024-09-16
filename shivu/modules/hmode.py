from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import user_collection

RARITY_OPTIONS = {
    "⚪ Common": "⚪ Common",
    "🟠 Rare": "🟠 Rare",
    "🟡 Legendary": "🟡 Legendary",
    "🟢 Medium": "🟢 Medium",
    "💠 Cosmic": "💠 Cosmic",
    "💮 Exclusive": "💮 Exclusive",
    "🔮 Limited Edition": "🔮 Limited Edition"
}

async def hmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(rarity, callback_data=f"harem:0:{user_id}:{value}")]
        for rarity, value in RARITY_OPTIONS.items()
    ]
    keyboard.append([InlineKeyboardButton("Clear Filter", callback_data=f"harem:0:{user_id}:")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Select Rarity to Filter By:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Select Rarity to Filter By:", reply_markup=reply_markup)

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.startswith('harem:'):
        _, page, user_id, rarity_filter = data.split(':')
        page = int(page)
        user_id = int(user_id)
        rarity_filter = rarity_filter or None

        if query.from_user.id != user_id:
            await query.answer("It's Not Your Harem", show_alert=True)
            return

        # Save user hmode preference in the database
        if rarity_filter:
            await user_collection.update_one(
                {'id': user_id},
                {'$set': {'hmode': rarity_filter}},
                upsert=True
            )
            await query.edit_message_caption(
                caption=f"Rarity Preference Set To\n{rarity_filter}\nHarem Interface: 🐉 Default",
                reply_markup=query.message.reply_markup,
                parse_mode='HTML'
            )
        await harem(update, context, page, rarity_filter)

def setup_handlers(application):
    application.add_handler(CommandHandler("hmode", hmode))
    application.add_handler(CallbackQueryHandler(harem_callback))
