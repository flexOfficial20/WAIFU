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
        # Handle case where user doesn't have any characters
        if update.message:
            await update.message.reply_text('You have not guessed any characters yet.')
        else:
            await update.callback_query.edit_message_text('You have not guessed any characters yet.')
        return

    # Sort the characters by anime and id
    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

    # Count the occurrences of each character
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    # Get unique characters
    unique_characters = list({character['id']: character for character in characters}.values())

    # Set the number of characters to show per page
    characters_per_page = 5
    total_pages = math.ceil(len(unique_characters) / characters_per_page)

    if page < 0 or page >= total_pages:
        page = 0

    # Start the message
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"

    # Get characters for the current page
    current_characters = unique_characters[page*characters_per_page:(page+1)*characters_per_page]

    # Group characters by anime
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    # Add character info to the message with the desired format
    for anime, characters in current_grouped_characters.items():
        for character in characters:
            count = character_counts[character['id']]
            rarity = character.get('rarity', 'Unknown')  # Assuming rarity is stored in the character object
            harem_message += (
                f"☘️ Name: {escape(character['name'])} (x{count})\n"
                f"🟡 Rarity: {escape(rarity)}\n"
                f"⚜️ Anime: {escape(anime)} ({len(characters)}/{await collection.count_documents({'anime': anime})})\n\n"
            )

    total_count = len(user['characters'])

    # Create buttons
    keyboard = [[InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    
    # Pagination controls
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # If the user has favorites, show the favorite character's image
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
        # If no favorites, show a random character's image if available
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
                await update.message.reply_text("Your list is empty :)")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    # Split the callback data to get page and user_id
    _, page, user_id = data.split(':')
    page = int(page)
    user_id = int(user_id)

    # Ensure only the correct user can interact with the harem message
    if query.from_user.id != user_id:
        await query.answer("It's not your harem.", show_alert=True)
        return

    # Call the main harem function with the new page number
    await harem(update, context, page)

# Add command handlers for "harem" and "collection"
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
harem_handler = CallbackQueryHandler(harem_callback, pattern='^harem', block=False)
application.add_handler(harem_handler)
