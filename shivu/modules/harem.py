from telegram import Update
from itertools import groupby
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import collection, user_collection, application

# Define rarity mapping
rarity_map = {1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic", 6: "💮 Exclusive", 7: "🔮 Limited Edition"}

async def harem(update: Update, context: CallbackContext, page=0, rarity_filter=None) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    # Filter characters based on rarity if specified
    if rarity_filter:
        characters = [c for c in user['characters'] if rarity_map.get(c.get('rarity', 1)) == rarity_filter]
    else:
        characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

    if not characters:
        if update.message:
            await update.message.reply_text(f"No characters found with rarity '{rarity_filter}'.")
        else:
            await update.callback_query.edit_message_text(f"No characters found with rarity '{rarity_filter}'")
        return

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    unique_characters = list({character['id']: character for character in characters}.values())

    # Pagination to display 7 characters per page
    total_pages = math.ceil(len(unique_characters) / 7)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    # Select the characters to display on the current page
    current_characters = unique_characters[page*7:(page+1)*7]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    # Construct the harem message for each anime and its characters
    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n𖤍 <b>{anime} {len(characters)}/{await collection.count_documents({"anime": anime})}</b>\n'
        harem_message += "⚋" * 15 + "\n"

        for character in characters:
            count = character_counts[character['id']]
            rarity_value = character.get("rarity", 1)  # Default to 1 if rarity is missing
            rarity = rarity_map.get(rarity_value, "⚪ Common")  # Get rarity from map, default to Common
            harem_message += f'𒄬 {character["id"]} [{rarity}] {character["name"]} ×{count}\n'
            harem_message += "⚋" * 15 + "\n"

    total_count = len(user['characters'])

    # Create the navigation and collection buttons
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    # Pagination buttons
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{rarity_filter}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{rarity_filter}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a photo or text based on favorites/random
    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

        if fav_character and 'img_url' in fav_character:
            if update.message:
                await update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
            else:
                if update.callback_query.message.caption != harem_message:
                    await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            if update.message:
                await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                if update.callback_query.message.text != harem_message:
                    await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if user['characters']:
            random_character = random.choice(user['characters'])

            if 'img_url' in random_character:
                if update.message:
                    await update.message.reply_photo(photo=random_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
                else:
                    if update.callback_query.message.caption != harem_message:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                if update.message:
                    await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    if update.callback_query.message.text != harem_message:
                        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            if update.message:
                await update.message.reply_text("Your List is Empty :)")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    _, page, user_id, rarity_filter = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("It's Not Your Harem", show_alert=True)
        return

    rarity_filter = rarity_filter if rarity_filter != "None" else None

    await harem(update, context, page, rarity_filter)

# Register the command and callback handlers
application.add_handler(CommandHandler("harem", harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
