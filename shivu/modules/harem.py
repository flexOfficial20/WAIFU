from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from html import escape
import math
from shivu import collection, user_collection, db, application

# Helper function to update the user's rarity preference
async def update_rarity_preference(user_id, rarity):
    user = await user_collection.find_one({'user_id': user_id})
    if user:
        await user_collection.update_one({'user_id': user_id}, {'$set': {'rarity_preference': rarity}})
    else:
        await user_collection.insert_one({'user_id': user_id, 'rarity_preference': rarity})

# Callback function for handling rarity preference
async def hmode_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if len(data) == 2:
        rarity = data[1]
        user_id = query.from_user.id
        await update_rarity_preference(user_id, rarity)
        await query.edit_message_text(
            text=f"Rarity Preference Set To\n{rarity} Rarity\nHarem Interface: 🐉 Default"
        )

# Callback function for handling harem command
async def harem_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if len(data) == 3:
        page = int(data[1])
        user_id = int(data[2])
        rarity_filter = data[0]
        await harem(update, context, page, rarity_filter, user_id)
    else:
        await harem(update, context, 1, '⚪ Common', query.from_user.id)

# Function to display harem characters based on rarity preference
async def harem(update: Update, context: CallbackContext, page: int, rarity_filter: str, user_id: int):
    user = await user_collection.find_one({'user_id': user_id})
    rarity_preference = user.get('rarity_preference', '⚪ Common') if user else '⚪ Common'
    
    # Fetch characters with the selected rarity
    characters = [character async for character in collection.find({'rarity': rarity_filter})]
    total_characters = len(characters)
    characters_per_page = 10
    total_pages = math.ceil(total_characters / characters_per_page)

    # Ensure the page is within valid range
    page = max(1, min(page, total_pages))
    
    # Paginate characters
    start = (page - 1) * characters_per_page
    end = start + characters_per_page
    characters_on_page = characters[start:end]

    # Format message
    harem_message = f"ᴛᴀɴᴊɪʀᴏ ┊𝗘 𝗠 𝗫 ™ 🐰's Harem - Page {page}/{total_pages}\n"
    if characters_on_page:
        for character in characters_on_page:
            harem_message += f"\n𖤍 {character.get('series', 'Unknown Series')} {character.get('id', 'Unknown ID')}/{total_characters}\n"
            harem_message += "⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n"
            harem_message += f"𒄬 {character.get('id', 'Unknown ID')} [{character.get('rarity', 'Unknown Rarity')}] {escape(character.get('name', 'Unknown Name'))} ×{character.get('quantity', 1)}\n"
            harem_message += "⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n"
    else:
        harem_message += "No characters found for this rarity."

    # Create inline keyboard for pagination
    keyboard = [
        [
            InlineKeyboardButton("Previous", callback_data=f"harem:{page - 1}:{user_id}:{rarity_filter}") if page > 1 else InlineKeyboardButton("Previous", callback_data="no_action"),
            InlineKeyboardButton("Next", callback_data=f"harem:{page + 1}:{user_id}:{rarity_filter}") if page < total_pages else InlineKeyboardButton("Next", callback_data="no_action"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Update message with character list
    if update.callback_query:
        await update.callback_query.edit_message_text(text=harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=harem_message, parse_mode='HTML', reply_markup=reply_markup)

# Command handler for harem command
async def harem_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = await user_collection.find_one({'user_id': user_id})
    rarity_preference = user.get('rarity_preference', '⚪ Common') if user else '⚪ Common'
    await harem(update, context, page=1, rarity_filter=rarity_preference, user_id=user_id)

# Command handler for hmode command
async def hmode_command(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("⚪ Common", callback_data="hmode:⚪ Common")],
        [InlineKeyboardButton("🟠 Rare", callback_data="hmode:🟠 Rare")],
        [InlineKeyboardButton("🟡 Legendary", callback_data="hmode:🟡 Legendary")],
        [InlineKeyboardButton("🟢 Medium", callback_data="hmode:🟢 Medium")],
        [InlineKeyboardButton("💠 Cosmic", callback_data="hmode:💠 Cosmic")],
        [InlineKeyboardButton("💮 Exclusive", callback_data="hmode:💮 Exclusive")],
        [InlineKeyboardButton("🔮 Limited Edition", callback_data="hmode:🔮 Limited Edition")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text="Select your rarity preference:",
        reply_markup=reply_markup
    )

# Register handlers
application.add_handler(CommandHandler('harem', harem_command))
application.add_handler(CommandHandler('hmode', hmode_command))
application.add_handler(CallbackQueryHandler(hmode_callback, pattern='^hmode:'))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem:'))


