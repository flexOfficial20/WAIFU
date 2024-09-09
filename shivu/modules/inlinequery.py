import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import ASCENDING

from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import user_collection, collection, application, db


# Rarity map for displaying correct emoji
rarity_map = {
    "1": "⚪ Common",
    "2": "🟠 Rare",
    "3": "🟡 Legendary",
    "4": "🟢 Medium",
    "5": "💠 Cosmic",
    "6": "💮 Exclusive",
    "7": "🔮 Limited Edition"
}

# collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

# user_collection
db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Cache for performance improvement
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            if user_id in user_collection_cache:
                user = user_collection_cache[user_id]
            else:
                user = await user_collection.find_one({'id': int(user_id)})
                user_collection_cache[user_id] = user

            if user:
                all_characters = list({v['id']: v for v in user['characters']}.values())
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    all_characters = [character for character in all_characters if regex.search(character['name']) or regex.search(character['anime'])]
            else:
                all_characters = []
        else:
            all_characters = []
    else:
        if query:
            regex = re.compile(query, re.IGNORECASE)
            all_characters = list(await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=None))
        else:
            if 'all_characters' in all_characters_cache:
                all_characters = all_characters_cache['all_characters']
            else:
                all_characters = list(await collection.find({}).to_list(length=None))
                all_characters_cache['all_characters'] = all_characters

    characters = all_characters[offset:offset + 50]
    next_offset = str(offset + 50) if len(characters) > 50 else str(offset + len(characters))

    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        # Get the rarity label and emoji from the rarity_map, default to "Unknown"
        rarity_value = str(character.get('rarity', '0'))  # Default to '0' if 'rarity' is missing
        rarity_label = rarity_map.get(rarity_value, "Unknown")

        if query.startswith('collection.'):
            user_character_count = sum(c['id'] == character['id'] for c in user['characters'])
            user_anime_characters = sum(c['anime'] == character['anime'] for c in user['characters'])
            caption = (f"<b> Look At <a href='tg://user?id={user['id']}'>{(escape(user.get('first_name', user['id'])))}</a>'s Character</b>\n\n"
                       f"🌸: <b>{character['name']} (x{user_character_count})</b>\n"
                       f"🏖️: <b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n"
                       f"<b>{rarity_label}</b>\n\n"
                       f"<b>🆔️:</b> {character['id']}")
        else:
            caption = (f"<b>Look At This Character !!</b>\n\n"
                       f"🌸: <b>{character['name']}</b>\n"
                       f"🏖️: <b>{character['anime']}</b>\n"
                       f"<b>{rarity_label}</b>\n"
                       f"🆔️: <b>{character['id']}</b>\n\n"
                       f"<b>Globally Guessed {global_count} Times...</b>")
        
        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML'
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Register the inline query handler
application.add_handler(InlineQueryHandler(inlinequery, block=False))
