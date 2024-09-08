import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING

from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext

from shivu import user_collection, collection, application, db

# Ensure the indexes are created
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

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

            # Handle case where user is not found
            if not user:
                await update.inline_query.answer([], cache_time=5, switch_pm_text="No characters found", switch_pm_parameter="start")
                return  # Exit early to prevent further errors

            # If user exists, proceed with fetching characters
            all_characters = list({v['id']: v for v in user['characters']}.values())
            if search_terms:
                regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                all_characters = [character for character in all_characters if regex.search(character['name']) or regex.search(character['anime'])]
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
    if len(characters) > 50:
        characters = characters[:50]
        next_offset = str(offset + 50)
    else:
        next_offset = str(offset + len(characters))

    results = []
    for character in characters:
        # Global count of the character
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        # Check if users in the current chat have this character
        chat_id = update.effective_chat.id
        chat_users = list(await user_collection.find({'chat_id': chat_id, 'characters.id': character['id']}).to_list(length=None))

        if chat_users:
            top_grabbers = sorted(
                [(user['first_name'], sum(c['id'] == character['id'] for c in user['characters']))
                 for user in chat_users],
                key=lambda x: x[1], reverse=True
            )[:10]  # Get the top 10 grabbers

            top_grabbers_message = "\n".join([f"➥ {grabber[0]} x{grabber[1]}" for grabber in top_grabbers])
            top_grabbers_text = f"🎖️ Top 10 Grabbers Of This Waifu In This Chat\n{top_grabbers_message}"
        else:
            top_grabbers_text = "🔐 Nobody Has Grabbed It Yet In This Chat! Who Will Be The First?"

        # Caption for the character, including the global count and top grabbers
        caption = (
            f"<b>Look At This Character !!</b>\n\n"
            f"🌸: <b>{character['name']}</b>\n"
            f"🏖️: <b>{character['anime']}</b>\n"
            f"🆔️: <b>{character['id']}</b>\n"
            f"⚜️: <b>{character['rarity']}</b>\n\n"
            f"🌎 Grabbed Globally: {global_count} Times\n\n"
            f"{top_grabbers_text}"
        )

        # Add inline keyboard button
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Grab Character", callback_data=f"grab_{character['id']}")]]
        )

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard  # Add inline keyboard
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Register the inline query handler
application.add_handler(InlineQueryHandler(inlinequery, block=False))
