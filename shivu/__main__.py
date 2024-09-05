import importlib
import time
import random
import re
import asyncio
import itertools
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, InlineQueryHandler, CallbackQueryHandler, CallbackContext

# Import custom modules and collections
from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES
from shivu.config import TOKEN
# Initialize locks and counters for managing state
locks = {}
message_counters = {}
last_user = {}
warned_users = {}
message_counts = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}

# Rarity spawn sequence for characters
rarity_sequence = (
    ['🟢 Common'] * 10 + 
    ['🔵 Medium'] * 9 + 
    ['🔴 Rare'] * 5 + 
    ['🟡 Legendary'] * 1
)
rarity_cycle = itertools.cycle(rarity_sequence)

# Custom counters for special rarities
limited_edition_counter = 0
cosmic_counter = 0
limited_edition_spawned = False
cosmic_spawned = False

def escape_markdown(text):
    """Escape special characters for markdown."""
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext):
    """Count messages and handle character spawns."""
    global limited_edition_counter, cosmic_counter, limited_edition_spawned, cosmic_spawned

    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    # Ensure lock exists for the chat
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        # Determine message frequency
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_frequency.get('message_frequency', 1) if chat_frequency else 1

        # Handle spam detection
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}... Your messages will be ignored for 10 minutes.")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        # Increment message count
        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

        if message_counts[chat_id] % message_frequency == 0:
            # Reset spawn flags
            limited_edition_spawned = False
            cosmic_spawned = False

            # Handle Limited Edition character spawn
            if limited_edition_counter >= 20000 and not limited_edition_spawned:
                if random.randint(1, 25) == 1:
                    await send_image(update, context, rarity='🔮 Limited Edition')
                    limited_edition_counter = 0
                    limited_edition_spawned = True
                else:
                    limited_edition_counter += 1
            # Handle Cosmic character spawn
            elif cosmic_counter >= 10000 and not cosmic_spawned:
                if random.randint(1, 200) == 1:
                    await send_image(update, context, rarity='💠 Cosmic')
                    cosmic_counter = 0
                    cosmic_spawned = True
                else:
                    cosmic_counter += 1
            # Spawn a regular character based on rarity
            else:
                await send_image(update, context)
                message_counts[chat_id] = 0

        # Increment special rarity counters
        limited_edition_counter += 1
        cosmic_counter += 1

async def send_image(update: Update, context: CallbackContext, rarity=None):
    """Send an image of a character to the chat."""
    chat_id = update.effective_chat.id

    if rarity is None:
        rarity = next(rarity_cycle)

    characters_of_rarity = list(await collection.find({'rarity': rarity}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    available_characters = [c for c in characters_of_rarity if c['id'] not in sent_characters[chat_id]]
    
    if not available_characters:
        sent_characters[chat_id] = []
        available_characters = characters_of_rarity

    character = random.choice(available_characters)

    sent_characters[chat_id].append(character['id'])
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""A New {character['rarity']} Character Appeared...\n/guess Character Name and add in Your Harem""",
        parse_mode='Markdown'
    )

async def guess(update: Update, context: CallbackContext):
    """Handle guessing the character's name."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌️ Already Guessed By Someone.. Try Next Time Bruhh ')
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("Nahh You Can't use These Types of words in your guess..❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):

        first_correct_guesses[chat_id] = user_id
        
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username') and hasattr(update.effective_user, 'first_name'):
            new_user = {
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]]
            }
            await user_collection.insert_one(new_user)
        
        await update.message.reply_text(f"🎉 {update.effective_user.first_name} guessed the character correctly and added it to their harem!")

    else:
        await update.message.reply_text(f"❌ Wrong guess, {update.effective_user.first_name}! Try again.")

# Inline query handler
async def inline_query_handler(update: Update, context: CallbackContext):
    """Handle inline queries."""
    query = update.inline_query.query.lower()
    
    if not query:
        return

    results = []
    async for character in collection.find({"name": {"$regex": f".*{query}.*", "$options": "i"}}):
        results.append(
            InlineQueryResultArticle(
                id=character['id'],
                title=character['name'],
                input_message_content=InputTextMessageContent(
                    message_text=f"Character: {character['name']}\nRarity: {character['rarity']}"
                ),
                description=f"Rarity: {character['rarity']}"
            )
        )

    await update.inline_query.answer(results)

# Callback query handler
async def callback_query_handler(update: Update, context: CallbackContext):
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    data = query.data

    if data.startswith("character_"):
        character_id = data.split("_")[1]
        character = await collection.find_one({'id': character_id})
        if character:
            await query.message.edit_text(
                f"Character: {character['name']}\nRarity: {character['rarity']}"
            )
    await query.answer()

def main():
    """Start the bot."""
    TOKEN = config.TOKEN
    # Load modules dynamically
    for module_name in ALL_MODULES:
        importlib.import_module("shivu.modules." + module_name)

    # Register handlers
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_counter))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
