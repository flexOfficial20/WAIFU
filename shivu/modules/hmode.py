from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from html import escape
import math
from shivu import application
# Define rarity map
rarity_map = {1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic", 6: "💮 Exclusive", 7: "🔮 Limited Edition"}

async def hmode(update: Update, context: CallbackContext, page=0, rarity_filter=None, sort_type="alphabetical") -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed Any Characters Yet.')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed Any Characters Yet.')
        return

    # Filter characters by rarity if a filter is set
    characters = user['characters']
    if rarity_filter:
        characters = [char for char in characters if char['rarity'] == rarity_filter]

    # Sort characters by name or rarity
    if sort_type == "alphabetical":
        characters = sorted(characters, key=lambda x: x['name'])
    else:
        characters = sorted(characters, key=lambda x: x['rarity'])

    if not characters:
        message = f"⚠️ You Don't Have Any Waifu From {rarity_map[rarity_filter]} Rarity.\nTry Changing Rarity Preference."
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    # Calculate pagination
    total_pages = math.ceil(len(characters) / 15)
    if page < 0 or page >= total_pages:
        page = 0

    # Build the message
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Waifus - Page: {page+1}/{total_pages}</b>\n\n"
    current_characters = characters[page*15:(page+1)*15]

    for character in current_characters:
        anime_total = await collection.count_documents({"anime": character['anime']})
        harem_message += (f"☘️ Name: {escape(character['name'])} (x{character['count']})\n"
                          f"{rarity_map[character['rarity']]}\n"
                          f"⚜️ Anime: {escape(character['anime'])} "
                          f"({len([c for c in user['characters'] if c['anime'] == character['anime']])}/{anime_total})\n\n")

    # Navigation buttons
    keyboard = []
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"hmode:{page-1}:{rarity_filter}:{sort_type}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"hmode:{page+1}:{rarity_filter}:{sort_type}"))
        keyboard.append(nav_buttons)

    # Filter and sorting buttons
    rarity_buttons = [[InlineKeyboardButton(rarity_map[r], callback_data=f"hmode:0:{r}:{sort_type}") for r in rarity_map]]
    sort_buttons = [[InlineKeyboardButton("Alphabetical", callback_data=f"hmode:0:{rarity_filter}:alphabetical"),
                     InlineKeyboardButton("Rarity", callback_data=f"hmode:0:{rarity_filter}:rarity")]]
    keyboard.extend(rarity_buttons + sort_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message
    if update.message:
        await update.message.reply_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.callback_query.edit_message_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')

# Callback to handle pagination and filtering
async def hmode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, rarity_filter, sort_type = query.data.split(':')
    
    await hmode(update, context, int(page), int(rarity_filter) if rarity_filter.isdigit() else None, sort_type)

# Register handlers
application.add_handler(CommandHandler("hmode", hmode))
application.add_handler(CallbackQueryHandler(hmode_callback, pattern="^hmode"))
