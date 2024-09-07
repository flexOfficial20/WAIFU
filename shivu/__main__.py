import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES


locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

# Set your main group chat ID where limited edition characters can spawn
MAIN_GROUP_CHAT_ID = "-1002139024353"  # Replace with the actual main group chat ID

# Tracks how many characters have been spawned of each rarity in the current sequence
rarity_spawn_count = {
    'common': 0,
    'medium': 0,
    'rare': 0,
    'legendary': 0,
    'cosmic': 0,
    'limited': 0
}

# Track total messages to control cosmic and limited spawns
total_message_count = 0
limited_spawn_count = 0  # Tracks how many limited characters have been spawned

# Spawn sequence: 4 common, 3 medium, 2 rare, 1 legendary
spawn_sequence = ['common'] * 4 + ['medium'] * 3 + ['rare'] * 2 + ['legendary'] * 1

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)


last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


async def message_counter(update: Update, context: CallbackContext) -> None:
    global total_message_count
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        total_message_count += 1
        
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0


async def send_image(update: Update, context: CallbackContext) -> None:
    global total_message_count, limited_spawn_count
    chat_id = update.effective_chat.id

    # Check if cosmic or limited edition should spawn based on total message count
    if total_message_count >= 5000 and limited_spawn_count < 25 and chat_id == MAIN_GROUP_CHAT_ID:
        rarity = 'limited'
        limited_spawn_count += 1
    elif total_message_count >= 3000:
        rarity = 'cosmic'
    else:
        # Follow the sequence: 4 common, 3 medium, 2 rare, 1 legendary
        rarity = get_next_rarity()

    # Get a random character of the chosen rarity
    all_characters = list(await collection.find({'rarity': rarity}).to_list(length=None))
    
    if not all_characters:
        await update.message.reply_text(f"No characters available for rarity: {rarity}")
        return

    character = random.choice(all_characters)

    # Track the last character for this chat and store in sent_characters
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []
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


def get_next_rarity():
    """Cycle through the predefined spawn sequence."""
    global rarity_spawn_count

    # Check the current sequence status
    for rarity in spawn_sequence:
        if rarity_spawn_count[rarity] < spawn_sequence.count(rarity):
            rarity_spawn_count[rarity] += 1
            return rarity

    # Reset if the sequence is complete
    rarity_spawn_count = {k: 0 for k in rarity_spawn_count}
    return spawn_sequence[0]  # Start from 'common' again


async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌️ Already Guessed By Someone.. Try Next Time Bruhh ')
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
        return


    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        await add_character_to_user_harem(update, context, user_id, chat_id)


async def add_character_to_user_harem(update, context, user_id, chat_id):
    """Add the correctly guessed character to the user's harem."""
    character = last_characters[chat_id]
    
    user = await user_collection.find_one({'id': user_id})
    if user:
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    else:
        await user_collection.insert_one({
            'id': user_id,
            'username': update.effective_user.username,
            'first_name': update.effective_user.first_name,
            'characters': [character],
        })

    # Additional logic for updating user and group totals as in the original code...
    
    keyboard = [[InlineKeyboardButton(f"See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
    await update.message.reply_text(
        f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> '
        f'You Guessed a New Character ✅️ \n\n𝗡𝗔𝗠𝗘: <b>{character["name"]}</b> '
        f'\n𝗔𝗡𝗜𝗠𝗘: <b>{character["anime"]}</b> \n𝗥𝗔𝗥𝗜𝗧𝗬: <b>{character["rarity"]}</b>\n\n'
        f'This Character added in Your harem.. use /harem To see your harem',
        parse_mode='HTML', 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    
    if not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    character_id = context.args[0]

    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have not Guessed any characters yet....')
        return


    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await update.message.reply_text('This Character is Not In your collection')
        return

    
    user['favorites'] = [character_id]

    
    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    await update.message.reply_text(f'Character {character["name"]} has been added to your favorite...')
    


def main() -> None:
    """Run bot."""

    application.add_handler(CommandHandler("guess", guess))
    application.add_handler(CommandHandler("fav", fav))

    application.add_handler(MessageHandler(filters.TEXT, message_counter))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

