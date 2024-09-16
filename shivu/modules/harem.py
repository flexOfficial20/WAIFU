from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from shivu import collection, user_collection, db, application
from html import escape
import math
from itertools import groupby

# Helper function to save rarity preference in the database
async def save_rarity_preference(user_id, rarity):
    await user_collection.update_one(
        {'_id': user_id},
        {'$set': {'rarity_preference': rarity}},
        upsert=True
    )

# Function to handle harem display based on rarity preference
async def harem(update: Update, context: CallbackContext, page: int = 1) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'_id': user_id})
    if user:
        rarity_preference = user.get('rarity_preference', None)
    else:
        rarity_preference = None

    # Find characters based on rarity preference
    if rarity_preference:
        characters = await collection.find({'user_id': user_id, 'rarity': rarity_preference}).to_list(None)
    else:
        characters = await collection.find({'user_id': user_id}).to_list(None)

    total_characters = len(characters)

    # Pagination logic
    characters_per_page = 5
    total_pages = math.ceil(total_characters / characters_per_page)
    if page > total_pages:
        page = 1
    start_idx = (page - 1) * characters_per_page
    end_idx = start_idx + characters_per_page

    # Create the harem message to display
    harem_message = f"{update.effective_user.first_name}'s Harem - Page {page}/{total_pages}\n"
    for character in characters[start_idx:end_idx]:
        harem_message += f"𒄬 {character['id']} [{character['rarity']}] {character['name']} ×{character['count']}\n"
        harem_message += "⚋" * 15 + "\n"

    # Inline buttons for pagination
    keyboard = [
        [
            InlineKeyboardButton("◀️ Prev", callback_data=f"harem:{page - 1}"),
            InlineKeyboardButton("Next ▶️", callback_data=f"harem:{page + 1}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display the harem message
    if update.callback_query:
        await update.callback_query.edit_message_text(text=harem_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=harem_message, reply_markup=reply_markup)

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
        _, page = data.split(':')
        await harem(update, context, int(page))
    except ValueError:
        # Handle cases where the data split results in too many values
        await query.answer("Invalid page data!")

# Command handler to start the /harem interface
async def harem_command(update: Update, context: CallbackContext) -> None:
    await harem(update, context, page=1)

# Add handlers to the application
application.add_handler(CommandHandler('hmode', hmode))
application.add_handler(CallbackQueryHandler(hmode_callback, pattern=r'hmode_'))
application.add_handler(CommandHandler('harem', harem_command))
application.add_handler(CallbackQueryHandler(harem_callback, pattern=r'harem:'))
