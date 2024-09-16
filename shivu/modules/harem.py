from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, application
from html import escape
import math
import random
from itertools import groupby

# Helper function to save rarity preference in the database
async def save_rarity_preference(user_id, rarity):
    await user_collection.update_one(
        {'_id': user_id},
        {'$set': {'rarity_preference': rarity}},
        upsert=True
    )

# Function to handle harem display based on rarity preference
async def harem(update: Update, context: CallbackContext, page: int = 0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'_id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You have not guessed any characters yet.')
        else:
            await update.callback_query.edit_message_text('You have not guessed any characters yet.')
        return

    # Fetch characters with rarity preference
    rarity_preference = user.get('rarity_preference', None)
    if rarity_preference:
        characters = [c async for c in collection.find({'user_id': user_id, 'rarity': rarity_preference})]
    else:
        characters = [c async for c in collection.find({'user_id': user_id})]

    total_characters = len(characters)
    if total_characters == 0:
        if update.message:
            await update.message.reply_text(f"No characters found for rarity: {rarity_preference}")
        else:
            await update.callback_query.edit_message_text(f"No characters found for rarity: {rarity_preference}")
        return

    # Pagination logic
    characters_per_page = 15
    total_pages = math.ceil(total_characters / characters_per_page)
    if page < 0 or page >= total_pages:
        page = 0
    start_idx = page * characters_per_page
    end_idx = start_idx + characters_per_page

    # Create the harem message to display
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"
    for character in characters[start_idx:end_idx]:
        harem_message += f"𒄬 {character['id']} [{character['rarity']}] {escape(character['name'])} ×{character.get('count', 1)}\n"
        harem_message += "⚋" * 15 + "\n"

    # Inline buttons for pagination
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data=f"harem:{page-1}:{user_id}") if page > 0 else None,
            InlineKeyboardButton("Next ➡️", callback_data=f"harem:{page+1}:{user_id}") if page < total_pages - 1 else None
        ]
    ]
    keyboard = [btn for btn in keyboard if btn is not None]  # Remove None entries
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display the harem message
    if update.callback_query:
        await update.callback_query.edit_message_text(text=harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=harem_message, parse_mode='HTML', reply_markup=reply_markup)

# Callback handler for /hmode, handling the rarity preference setting
async def hmode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    # Map callback data to rarity levels
    rarity_map = {
        'common': '⚪ Common',
        'rare': '🟠 Rare',
        'legendary': '🟡 Legendary',
        'medium': '🟢 Medium',
        'cosmic': '💠 Cosmic',
        'exclusive': '💮 Exclusive',
        'limited': '🔮 Limited Edition'
    }

    if data.startswith('hmode_'):
        rarity_key = data.split('_')[1]
        rarity = rarity_map.get(rarity_key)

        # Save the rarity preference for the user
        user_id = update.effective_user.id
        await save_rarity_preference(user_id, rarity)

        # Respond with the chosen rarity and interface message
        message = f"Rarity Preference Set To\n {rarity}\nHarem Interface: 🐉 Default"
        await query.edit_message_text(text=message)

# Command handler for /hmode, presenting the rarity selection menu
async def hmode(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("⚪ Common", callback_data='hmode_common'),
            InlineKeyboardButton("🟠 Rare", callback_data='hmode_rare'),
        ],
        [
            InlineKeyboardButton("🟡 Legendary", callback_data='hmode_legendary'),
            InlineKeyboardButton("🟢 Medium", callback_data='hmode_medium'),
        ],
        [
            InlineKeyboardButton("💠 Cosmic", callback_data='hmode_cosmic'),
            InlineKeyboardButton("💮 Exclusive", callback_data='hmode_exclusive'),
            InlineKeyboardButton("🔮 Limited Edition", callback_data='hmode_limited')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select your rarity preference:", reply_markup=reply_markup)

# Callback handler for harem pagination
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    try:
        _, page, user_id = data.split(':')
        await harem(update, context, int(page))
    except ValueError:
        await query.answer("Invalid page data!")

# Command handler to start the /harem interface
async def harem_command(update: Update, context: CallbackContext) -> None:
    await harem(update, context, page=0)

# Add handlers to the application
application.add_handler(CommandHandler('hmode', hmode))
application.add_handler(CommandHandler('harem', harem_command))
application.add_handler(CallbackQueryHandler(hmode_callback, pattern=r'hmode_'))
application.add_handler(CallbackQueryHandler(harem_callback, pattern=r'harem:'))
