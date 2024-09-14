from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from html import escape
import math
import random
from itertools import groupby

from shivu import collection, user_collection, application

# Define rarity map
rarity_map = {1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic", 6: "💮 Exclusive", 7: "🔮 Limited Edition"}

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    # Fetch the user from the database
    user = await user_collection.find_one({'id': user_id})
    
    if not user:
        message = 'You Have Not Guessed any Characters Yet..'
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    # Sort characters by anime and id
    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())

    # Calculate total pages for pagination
    total_pages = math.ceil(len(unique_characters) / 15)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Recent Waifus - Page: {page+1}/{total_pages}</b>\n\n"

    # Get characters for the current page
    current_characters = unique_characters[page*15:(page+1)*15]

    # Group characters by anime
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    # Build the message
    for anime, characters in current_grouped_characters.items():
        for character in characters:
            name = escape(character.get('name', 'Unknown'))
            rarity = rarity_map.get(character.get('rarity', 1), "Unknown")
            count = character_counts[character['id']]  
            anime_name = escape(character.get('anime', 'Unknown'))

            # Count total characters in the anime
            anime_total = await collection.count_documents({"anime": anime_name})

            harem_message += (f"☘️ Name: {name} (x{count})\n"
                              f"{rarity}\n"
                              f"⚜️ Anime: {anime_name} ({len([c for c in user['characters'] if c['anime'] == anime_name])}/{anime_total})\n\n")

    total_count = len(user['characters'])
    
    # Add navigation buttons and inline query button
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle favorites or random character image
    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        random_character = random.choice(user['characters'])
        if 'img_url' in random_character:
            if update.message:
                await update.message.reply_photo(photo=random_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)

# Callback function to handle pagination
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, user_id = query.data.split(':')

    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("It's Not Your Harem", show_alert=True)
        return

    await harem(update, context, page)

# Register handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
