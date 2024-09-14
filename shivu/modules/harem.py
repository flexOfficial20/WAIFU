from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from html import escape
from itertools import groupby
import math
import random

from shivu import collection, user_collection, application

# Mapping for rarity display
rarity_map = {
    1: "⚪ Common",
    2: "🟠 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💠 Cosmic",
    6: "💮 Exclusive",
    7: "🔮 Limited Edition"
}

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You have not guessed any characters yet.')
        else:
            await update.callback_query.edit_message_text('You have not guessed any characters yet.')
        return

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    unique_characters = list({character['id']: character for character in characters}.values())

    total_pages = math.ceil(len(unique_characters) / 5)  # Adjusted to show 5 characters per page

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n\n"

    current_characters = unique_characters[page * 5:(page + 1) * 5]

    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        harem_message += f"<b>{anime}</b>\n"
        for character in characters:
            count = character_counts[character['id']]
            harem_message += f"☘️ Name: {escape(character['name'])} (x{count})\n"
            harem_message += f"⚜️ Anime: {anime} ({count}/{await collection.count_documents({'anime': anime})})\n\n"

    keyboard = []
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"harem_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"harem_{page+1}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)


async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    # Add check for valid callback data structure
    if not query.data or '_' not in query.data:
        await query.answer("Invalid data", show_alert=True)
        return

    # Try parsing character ID safely
    try:
        action, page_number = query.data.split('_')
        page_number = int(page_number)
    except (ValueError, IndexError):
        await query.answer("Error parsing callback data", show_alert=True)
        return

    # Continue with the existing logic after parsing the ID
    if action == "harem":
        await harem(update, context, page=page_number)
    else:
        await query.answer("Unknown action", show_alert=True)


application.add_handler(CommandHandler(["harem"], harem))
application.add_handler(CallbackQueryHandler(button_click))

