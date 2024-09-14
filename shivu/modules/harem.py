import re
from html import escape
from cachetools import TTLCache
from pymongo import ASCENDING
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  # Updated import
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from shivu import user_collection, collection, application, db

# Create indexes for faster querying
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

# Caching to improve performance
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def harem(update: Update, context: CallbackContext) -> None:
    query = update.message.text.split(maxsplit=1)
    if len(query) < 2:
        await update.message.reply_text("Please provide a valid character ID.")
        return

    character_id = query[1].strip()
    user_id = str(update.message.from_user.id)

    # Fetch the character data
    character = await collection.find_one({'id': int(character_id)})
    if not character:
        await update.message.reply_text("Character not found.")
        return

    # Fetch user data from cache or database
    if user_id in user_collection_cache:
        user = user_collection_cache[user_id]
    else:
        user = await user_collection.find_one({'id': int(user_id)})
        if user:
            user_collection_cache[user_id] = user
        else:
            user_collection_cache[user_id] = {}

    if user:
        user_characters = {c['id'] for c in user.get('characters', [])}
        is_favorite = character['id'] in user_characters
    else:
        is_favorite = False

    # Compose the caption message
    harem_message = (
        f"🌸 Name: {escape(character['name'])}\n"
        f"🟡 Rarity: {escape(character.get('rarity', 'Unknown'))}\n"
        f"🏖️ Anime: {escape(character['anime'])}\n"
        f"🆔️ ID: {character['id']}\n\n"
    )
    
    # Add inline button for favoriting the character
    favorite_button = InlineKeyboardButton(
        text="⭐ Favorite" if not is_favorite else "⭐ Unfavorite",
        callback_data=f"favorite_{character['id']}"
    )

    reply_markup = InlineKeyboardMarkup([[favorite_button]])

    try:
        await update.message.reply_photo(
            photo=character['img_url'],
            caption=harem_message,
            parse_mode=ParseMode.HTML,  # Updated usage
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def favorite(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    character_id = int(query.data.split('_')[1])
    user_id = str(query.from_user.id)

    # Fetch user data from cache or database
    if user_id in user_collection_cache:
        user = user_collection_cache[user_id]
    else:
        user = await user_collection.find_one({'id': int(user_id)})
        if user:
            user_collection_cache[user_id] = user
        else:
            user_collection_cache[user_id] = {}
            user = user_collection_cache[user_id]

    if user:
        user_characters = {c['id'] for c in user.get('characters', [])}

        if character_id in user_characters:
            user_characters.remove(character_id)
            await user_collection.update_one(
                {'id': int(user_id)},
                {'$pull': {'characters': {'id': character_id}}}
            )
            action = "removed from"
        else:
            user_characters.add(character_id)
            await user_collection.update_one(
                {'id': int(user_id)},
                {'$push': {'characters': {'id': character_id}}}
            )
            action = "added to"

        user_collection_cache[user_id] = {'characters': [{'id': cid} for cid in user_characters]}

        await query.answer(f"Character has been {action} your favorites.")
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    text="⭐ Unfavorite" if action == "added to" else "⭐ Favorite",
                    callback_data=f"favorite_{character_id}"
                )]]
            )
        )
    else:
        await query.answer("Error processing your request. Please try again later.")

# Register the handlers
application.add_handler(CommandHandler('harem', harem, block=False))
application.add_handler(CallbackQueryHandler(favorite, pattern='^favorite_', block=False))
