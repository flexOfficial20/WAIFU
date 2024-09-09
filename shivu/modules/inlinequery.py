import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING

from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext

from shivu import user_collection, collection, application, db

# Setup indexes for collection and user_collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Caches
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

# Rarity mapping
rarity_map = {
    '⚪ Common': 1,
    '🟠 Rare': 2,
    '🟡 Legendary': 3,
    '🟢 Medium': 4,
    '💠 Cosmic': 5,
    '💮 Exclusive': 6,
    '🔮 Limited Edition': 7
}

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

    # Pagination logic
    characters = all_characters[offset:offset + 20]
    next_offset = str(offset + len(characters)) if len(characters) == 20 else None

    results = []
    displayed_ids = set()

    for character in characters:
        if character['id'] in displayed_ids:
            continue
        displayed_ids.add(character['id'])

        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        # Rarity mapping
        rarity = character.get('rarity', '')
        rarity_symbol = [k for k, v in rarity_map.items() if rarity == v]

        # Caption creation
        caption = (
            f"🌸: {character['name']}\n"
            f"🏖️: {character['anime']}\n"
            f"{rarity_symbol[0] if rarity_symbol else ''} Rarity: {rarity}\n"
            f"🆔️: {character['id']}\n"
            f"🌎 Grabbed Globally: {global_count} Times\n"
        )

        # Inline button
        buttons = [[InlineKeyboardButton("Grab Details", callback_data=f"grab_{character['id']}")]]

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='HTML'
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Handle button callback for showing grab details
async def grab_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    character_id = query.data.split('_')[1]

    # Fetch character details
    character = await collection.find_one({'id': character_id})
    if not character:
        await query.answer("Character not found.", show_alert=True)
        return

    global_count = await user_collection.count_documents({'characters.id': character['id']})
    chat_grabbers = await user_collection.find({'characters.id': character['id']}).limit(10).to_list(length=10)

    # Build the message with top grabbers in the chat
    if chat_grabbers:
        top_grabbers_msg = "🎖️ Top 10 Grabbers Of This Waifu In This Chat\n"
        for grabber in chat_grabbers:
            grabber_count = sum(c['id'] == character['id'] for c in grabber['characters'])
            top_grabbers_msg += f"➥ {grabber['first_name']} x{grabber_count}\n"
    else:
        top_grabbers_msg = "🔐 Nobody Has Grabbed It Yet In This Chat! Who Will Be The First?\n"

    # Update message
    await query.edit_message_caption(
        caption=(
            f"🌸: {character['name']}\n"
            f"🏖️: {character['anime']}\n"
            f"🟡 Rarity: {character['rarity']}\n"
            f"🆔️: {character['id']}\n\n"
            f"🌎 Grabbed Globally: {global_count} Times\n\n"
            f"{top_grabbers_msg}"
        ),
        parse_mode='HTML'
    )

# Register handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))
application.add_handler(CallbackQueryHandler(grab_callback, pattern=r"grab_\d+"))

