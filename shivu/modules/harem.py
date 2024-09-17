from telegram import Update
from itertools import groupby
import math
from html import escape 
import random
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from shivu import collection, user_collection, application

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    # Fetch user from the database
    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    # Get user's rarity preference
    rarity_preference = user.get('rarity_preference', None)

    # Fetch characters with optional rarity filter
    if rarity_preference:
        characters = [c async for c in collection.find({'user_id': user_id, 'rarity': rarity_preference})]
    else:
        characters = user['characters']

    if not characters:
        if update.message:
            await update.message.reply_text(f"No characters found for rarity: {rarity_preference}")
        else:
            await update.callback_query.edit_message_text(f"No characters found for rarity: {rarity_preference}")
        return

    # Sort and group characters by anime and ID
    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())

    # Pagination setup
    total_pages = math.ceil(len(unique_characters) / 15)
    if page < 0 or page >= total_pages:
        page = 0  

    # Create the message for the current page
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"
    current_characters = unique_characters[page*15:(page+1)*15]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n<b>{anime} {len(characters)}/{await collection.count_documents({"anime": anime})}</b>\n'
        for character in characters:
            count = character_counts[character['id']]  
            harem_message += f'{character["id"]} {character["name"]} ×{count}\n'

    # Total character count and inline buttons for pagination
    total_count = len(user['characters'])
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display the message based on user preference
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

# Callback handler for pagination
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("It's Not Your Harem", show_alert=True)
        return

    await harem(update, context, page)

# Add handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
