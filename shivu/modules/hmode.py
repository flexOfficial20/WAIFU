from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import user_collection, application
from html import escape

# Define rarity map
rarity_map = {
    1: "⚪ Common", 
    2: "🟠 Rare", 
    3: "🟡 Legendary", 
    4: "🟢 Medium", 
    5: "💠 Cosmic", 
    6: "💮 Exclusive", 
    7: "🔮 Limited Edition"
}

# Rarity options for buttons
RARITY_OPTIONS = ["⚪ Common", "🟠 Rare", "🟡 Legendary", "🟢 Medium", "💠 Cosmic", "💮 Exclusive", "🔮 Limited Edition"]

# Command to display the hmode selection menu
async def hmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have no characters to display in Harem.')
        return

    # Rarity selection buttons
    rarity_buttons = [
        [InlineKeyboardButton(f"{rarity}", callback_data=f"hmode:rarity:{rarity}:{user_id}") for rarity in RARITY_OPTIONS],
        [InlineKeyboardButton("🅰️ Alphabetical", callback_data=f"hmode:alpha:{user_id}"),
         InlineKeyboardButton("🌟 Rarity", callback_data=f"hmode:rarity:{user_id}")]
    ]

    reply_markup = InlineKeyboardMarkup(rarity_buttons)
    await update.message.reply_text(
        f"<b>{escape(update.effective_user.first_name)}'s Harem Interface:</b>\nChoose how you want to view your harem!",
        parse_mode='HTML', reply_markup=reply_markup
    )

# Callback handler for hmode interactions
async def hmode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = update.callback_query.from_user.id

    _, mode, rarity_or_user, user_id = data.split(':')

    if int(user_id) != update.effective_user.id:
        await query.answer("This is not your harem!", show_alert=True)
        return

    user = await user_collection.find_one({'id': int(user_id)})
    if not user:
        await query.answer("No characters found.", show_alert=True)
        return

    if mode == 'alpha':
        characters = sorted(user['characters'], key=lambda x: x['name'])
        message_text = f"Viewing {escape(update.effective_user.first_name)}'s Harem in 🅰️ Alphabetical Order.\n"
        for character in characters:
            rarity = rarity_map.get(character['rarity_id'], "Unknown")
            message_text += f"{character['name']} - {rarity}\n"

    elif mode == 'rarity':
        rarity = rarity_or_user
        filtered_characters = [c for c in user['characters'] if rarity_map.get(c['rarity_id']) == rarity]

        if not filtered_characters:
            await query.edit_message_text(
                f"⚠️ You don't have any characters from {rarity}.\nTry changing your rarity preference.",
                parse_mode='HTML'
            )
            return

        message_text = f"Viewing {escape(update.effective_user.first_name)}'s Harem by 🌟 Rarity: {rarity}.\n"
        for character in filtered_characters:
            rarity_label = rarity_map.get(character['rarity_id'], "Unknown")
            message_text += f"{character['name']} - {rarity_label}\n"

    keyboard = [[InlineKeyboardButton(f"See Collection ({len(user['characters'])})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='HTML')

# Register handlers
application.add_handler(CommandHandler(["hmode"], hmode, block=False))
hmode_handler = CallbackQueryHandler(hmode_callback, pattern='^hmode', block=False)
application.add_handler(hmode_handler)
