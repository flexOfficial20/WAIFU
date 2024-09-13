import random
import html
from telegram import Update, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackContext, CallbackQueryHandler, CommandHandler
from pymongo import ASCENDING
from shivu import user_collection, collection, application, db

# MongoDB Collections and Indexes
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Cache setup
from cachetools import TTLCache
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

# Inline Query Handler
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

    characters = all_characters[offset:offset+20]
    if len(characters) > 20:
        characters = characters[:20]
        next_offset = str(offset + 20)
    else:
        next_offset = str(offset + len(characters))

    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})

        if query.startswith('collection.'):
            user_character_count = sum(c['id'] == character['id'] for c in user['characters'])
            user_anime_characters = sum(c['anime'] == character['anime'] for c in user['characters'])
            anime_characters = await collection.count_documents({'anime': character['anime']})
            
            caption = (f"<b>Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', user['id']))}</a>'s Character</b>\n\n"
                       f"🌸: <b>{character['name']} (x{user_character_count})</b>\n"
                       f"🏖️: <b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n"
                       f"<b>{character['rarity']}</b>\n\n"
                       f"🆔️: <b>{character['id']}</b>")
        else:
            caption = (f"<b>Look At This Character !!</b>\n\n"
                       f"🌸: <b>{character['name']}</b>\n"
                       f"🏖️: <b>{character['anime']}</b>\n"
                       f"<b>{character['rarity']}</b>\n"
                       f"🆔️: <b>{character['id']}</b>\n\n"
                       f"<b>Globally Guessed {global_count} Times...</b>")

        # Add inline button for grabbing information
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌎 Grab Stats", callback_data=f"grab_{character['id']}")]]
        )

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

# Callback Query Handler
async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    character_id = int(query.data.split('_')[1])

    # Fetch global grabs for the character
    global_grabs = await user_collection.count_documents({'characters.id': character_id})

    # Get the top 10 grabbers in the current chat
    chat_id = query.message.chat_id if query.message else None
    if chat_id:
        pipeline = [
            {"$match": {"characters.id": character_id, "chat_id": chat_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": character_id}},
            {"$group": {"_id": "$id", "count": {"$sum": 1}, "name": {"$first": "$first_name"}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_grabbers = await user_collection.aggregate(pipeline).to_list(length=None)

        if top_grabbers:
            top_grabbers_text = "\n".join([f"➥ {grabber['name']} x{grabber['count']}" for grabber in top_grabbers])
        else:
            top_grabbers_text = "🔐 Nobody Has Grabbed It Yet In This Chat! Who Will Be The First?"

        # Full caption after clicking the button
        full_caption = (f"🌸 Name: {query.message.caption.splitlines()[0].split(': ')[1]}\n"
                        f"🏖️ Anime: {query.message.caption.splitlines()[1].split(': ')[1]}\n"
                        f"<b>{query.message.caption.splitlines()[2].split(': ')[1]}</b>\n"
                        f"🆔️: {character_id}\n\n"
                        f"🌎 Grabbed Globally: {global_grabs} Times\n\n"
                        f"🎖️ Top 10 Grabbers Of This Waifu In This Chat:\n{top_grabbers_text}")

        await query.answer()
        await query.edit_message_caption(caption=full_caption, parse_mode='HTML')

# Command Handler for Top 10
async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>TOP 10 USERS WHO GUESSED CHARACTERS MOST TIMES IN THIS GROUP..</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    photo_url = random.choice(PHOTO_URL)  # Assuming PHOTO_URL is defined elsewhere

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')

# Register the handlers
application.add_handler(InlineQueryHandler(inlinequery, block=False))
application.add_handler(CallbackQueryHandler(button_click))
application.add_handler(CommandHandler("fctop", ctop))
