import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING

from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, CallbackQueryHandler

from shivu import user_collection, collection, application, db

# Rarity map for displaying correct emoji
rarity_map = {
    "1": "⚪ Rarity: Common",
    "2": "🟠 Rarity: Rare",
    "3": "🟡 Rarity: Legendary",
    "4": "🟢 Rarity: Medium",
    "5": "💠 Rarity: Cosmic",
    "6": "💮 Rarity: Exclusive",
    "7": "🔮 Rarity: Limited Edition"
}

# Create indexes for faster querying
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Caching to improve performance
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    # Optimizing search with cached data or simple query
    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = user_collection_cache.get(user_id) or await user_collection.find_one({'id': int(user_id)}, projection={'characters': 1, 'id': 1, 'first_name': 1})
            user_collection_cache[user_id] = user if user else {}
            all_characters = user.get('characters', []) if user else []
            if search_terms:
                regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                all_characters = [character for character in all_characters if regex.search(character['name']) or regex.search(character['anime'])]
        else:
            all_characters = []
    else:
        if query:
            regex = re.compile(query, re.IGNORECASE)
            all_characters = list(await collection.find({"$or": [{"name": regex}, {"anime": regex}]}, projection={'name': 1, 'anime': 1, 'rarity': 1, 'id': 1, 'img_url': 1}).to_list(length=20))
        else:
            if 'all_characters' in all_characters_cache:
                all_characters = all_characters_cache['all_characters']
            else:
                all_characters = list(await collection.find({}, projection={'name': 1, 'anime': 1, 'rarity': 1, 'id': 1, 'img_url': 1}).to_list(length=20))
                all_characters_cache['all_characters'] = all_characters

    characters = all_characters[offset:offset + 20]  # Limit to 20 results for faster response
    next_offset = str(offset + len(characters)) if len(characters) == 20 else None

    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        
        # Get the rarity label and emoji from the rarity_map
        rarity_emoji = rarity_map.get(str(character['rarity']), "Unknown")

        # Inline button for grabbing information
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton(f"🌎 Grab Stats", callback_data=f"grab_{character['id']}")]]
        )

        # Initial caption when user hasn't clicked on the button
        caption = (f"🌸: {character['name']}\n"
                   f"🏖️: {character['anime']}\n"
                   f"{rarity_emoji}\n"
                   f"🆔️: {character['id']}")

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
                reply_markup=buttons
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    character_id = query.data.split('_')[1]

    # Fetch global grabs for the character
    global_grabs = await user_collection.count_documents({'characters.id': int(character_id)})

    # Get the rarity label and emoji from the rarity_map
    rarity_emoji = rarity_map.get(str(character['rarity']), "Unknown")

    # Full caption after clicking the button
    full_caption = (f"🌸: {query.message.caption.splitlines()[0].split(': ')[1]}\n"
                    f"🏖️: {query.message.caption.splitlines()[1].split(': ')[1]}\n"
                    f"{rarity_emoji}\n"
                    f"🆔️: {character_id}\n\n"
                    f"🌎 Grabbed Globally: {global_grabs} Times")

    await query.answer()
    await query.edit_message_caption(caption=full_caption, parse_mode='HTML')

# Register the handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))
application.add_handler(CallbackQueryHandler(button_click))
