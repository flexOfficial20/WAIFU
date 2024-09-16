from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from html import escape
import math
import random
from itertools import groupby

from shivu import collection, user_collection, application

# Rarity levels
RARITY_OPTIONS = {
    "⚪ Common": "⚪ Common",
    "🟠 Rare": "🟠 Rare",
    "🟡 Legendary": "🟡 Legendary",
    "🟢 Medium": "🟢 Medium",
    "💠 Cosmic": "💠 Cosmic",
    "💮 Exclusive": "💮 Exclusive",
    "🔮 Limited Edition": "🔮 Limited Edition"
}

async def harem(update: Update, context: CallbackContext, page=0, rarity_filter=None) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        message = 'You Have Not Guessed any Characters Yet..'
        if update.message:
            await update.message.reply_text(message)
        else:
            await update.callback_query.edit_message_text(message)
        return

    # Filter characters based on rarity if rarity_filter is provided
    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))
    if rarity_filter:
        characters = [char for char in characters if char.get('rarity') == rarity_filter]

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())
    
    total_pages = math.ceil(len(unique_characters) / 7)  # 7 characters per page
    if page < 0 or page >= total_pages:
        page = 0  # Reset page if out of bounds

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    # Display characters for current page
    current_characters = unique_characters[page*7:(page+1)*7]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        total_anime_count = await collection.count_documents({"anime": anime})
        harem_message += f'\n<b>𖤍 {anime} {len(characters)}/{total_anime_count}</b>\n'
        harem_message += "⚋" * 15 + "\n"

        for character in characters:
            count = character_counts[character['id']]  # Character count in harem
            rarity = escape(character.get('rarity', '⚪ Common'))  # Get rarity from character data

            harem_message += f'𒄬 {character["id"]} [{rarity}] {escape(character["name"])} ×{count}\n'
            harem_message += "⚋" * 15 + "\n"

    # Total count of characters
    total_count = len(user['characters'])
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    # Navigation buttons if there are multiple pages
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{rarity_filter or ''}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{rarity_filter or ''}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if the user has a favorite character
    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                # Check if the message has a caption before editing
                if update.callback_query.message.caption:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                # Check if the message has a caption before editing
                if update.callback_query.message.caption:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                else:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])

            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
                else:
                    # Check if the message has a caption before editing
                    if update.callback_query.message.caption:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if update.message:
                    await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    # Check if the message has a caption before editing
                    if update.callback_query.message.caption:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("Your List is Empty :)")

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

    # Handle pagination and rarity filter
    if data.startswith('harem:'):
        _, page, user_id, rarity_filter = data.split(':')
        page = int(page)
        user_id = int(user_id)
        rarity_filter = rarity_filter or None

        if query.from_user.id != user_id:
            await query.answer("It's Not Your Harem", show_alert=True)
            return

        await harem(update, context, page, rarity_filter)

application.add_handler(CommandHandler("harem", harem))
application.add_handler(CommandHandler("hmode", hmode))  # Use hmode command to handle rarity filtering
application.add_handler(CallbackQueryHandler(harem_callback))
