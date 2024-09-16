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
        {'id': user_id},
        {'$set': {'rarity_preference': rarity}},
        upsert=True
    )

# Function to handle harem display based on rarity preference
async def harem(update: Update, context: CallbackContext, page: int = 0) -> None:
    user_id = update.effective_user.id

    # Retrieve user data
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
        characters = [c async for c in collection.find({'user_id': user_id})]

    # Check if any characters are found
    if not characters:
        if update.message:
            await update.message.reply_text(f"No characters found for rarity: {rarity_preference}")
        else:
            await update.callback_query.edit_message_text(f"No characters found for rarity: {rarity_preference}")
        return

    # Sorting and unique filtering
    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())

    # Pagination
    characters_per_page = 7
    total_pages = math.ceil(len(unique_characters) / characters_per_page)
    if page < 0 or page >= total_pages:
        page = 0
    start_idx = page * characters_per_page
    end_idx = start_idx + characters_per_page

    # Create harem message
    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}</b>\n"
    current_characters = unique_characters[start_idx:end_idx]
    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, chars in current_grouped_characters.items():
        harem_message += f'\n𖤍 {anime} {len(chars)}/{await collection.count_documents({"anime": anime})}\n'
        harem_message += '⚋' * 15 + '\n'
        for character in chars:
            count = character_counts[character['id']]
            harem_message += f'𒄬 {character["id"]} [{character["rarity"]}] {escape(character["name"])} ×{count}\n'
        harem_message += '⚋' * 15 + '\n'

    # Inline buttons for pagination
    keyboard = [[InlineKeyboardButton(f"See Collection ({len(user['characters'])})", switch_inline_query_current_chat=f"collection.{user_id}")]]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the harem message
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

# Callback handler for hmode, handling the rarity preference setting
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
