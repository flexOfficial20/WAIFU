import importlib
import time
import random
import re
import asyncio
import itertools
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters, InlineQueryHandler, CallbackQueryHandler

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES

# Locks and counters for message handling
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

# Load all modules
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

# Rarity spawn sequence with spawn frequencies:
rarity_sequence = (
    ['🟢 Common'] * 10 + 
    ['🔵 Medium'] * 9 + 
    ['🔴 Rare'] * 5 + 
    ['🟡 Legendary'] * 1
)

# Convert to an itertools cycle so it will keep repeating
rarity_cycle = itertools.cycle(rarity_sequence)

# Custom counters for Limited Edition and Cosmic rarities
limited_edition_counter = 0
cosmic_counter = 0
limited_edition_spawned = False
cosmic_spawned = False

async def message_counter(update: Update, context: CallbackContext) -> None:
    global limited_edition_counter, cosmic_counter, limited_edition_spawned, cosmic_spawned
    
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 1)
        else:
            message_frequency = 1

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
            # Reset flags for new spawn cycle
            limited_edition_spawned = False
            cosmic_spawned = False

            # Check if it's time to spawn a Limited Edition character
            if limited_edition_counter >= 20000 and not limited_edition_spawned:
                if random.randint(1, 25) == 1:
                    await send_image(update, context, rarity='🔮 Limited Edition')
                    limited_edition_counter = 0
                    limited_edition_spawned = True
                else:
                    limited_edition_counter += 1
            # Check if it's time to spawn a Cosmic character
            elif cosmic_counter >= 10000 and not cosmic_spawned:
                if random.randint(1, 200) == 1:
                    await send_image(update, context, rarity='💠 Cosmic')
                    cosmic_counter = 0
                    cosmic_spawned = True
                else:
                    cosmic_counter += 1
            # Otherwise, spawn based on the rarity cycle
            else:
                await send_image(update, context)
                message_counts[chat_id] = 0

        # Increment counters
        limited_edition_counter += 1
        cosmic_counter += 1

async def send_image(update: Update, context: CallbackContext, rarity=None) -> None:
    chat_id = update.effective_chat.id

    if rarity is None:
        # Select the next rarity from the cycle
        rarity = next(rarity_cycle)

    # Fetch all characters of that rarity
    characters_of_rarity = list(await collection.find({'rarity': rarity}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    # Avoid repetition within the same rarity
    available_characters = [c for c in characters_of_rarity if c['id'] not in sent_characters[chat_id]]
    
    if not available_characters:
        # Reset the sent characters if all have been sent
        sent_characters[chat_id] = []
        available_characters = characters_of_rarity

    # Select a random character from the available ones
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
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })

        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})
            
            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })

        keyboard = [[InlineKeyboardButton(f"See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You Guessed a New Character ✅️ \n\n𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n𝗥𝗔𝗜𝗥𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\nThis Character added in Your harem.. use /harem To see your harem', 
            parse_mode='HTML', 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text('Please Write Correct Character Name... ❌️')

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    character_id = context.args[0]

    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have no characters in your harem.')
        return

    if character_id not in [character['id'] for character in user.get('characters', [])]:
        await update.message.reply_text("This character isn't in your harem.")
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'favorite': character_id}})
    await update.message.reply_text(f'Character {character_id} has been set as your favorite.')

async def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    results = []

    if not query:
        return

    # Search for characters by name or ID
    characters = await collection.find({
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'id': query}
        ]
    }).to_list(length=10)

    for character in characters:
        character_id = character['id']
        keyboard = [
            [InlineKeyboardButton(f"Grabber Stats", callback_data=f"grabber_stats_{character_id}")]
        ]

        results.append(
            InlineQueryResultArticle(
                id=character_id,
                title=character['name'],
                input_message_content=InputTextMessageContent(
                    f"""☘️ Name: {character['name']}
                    🟡 Rarity: {character['rarity']}
                    ⚜️ Anime: {character['anime']}
                    🆔: {character_id}"""
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        )

    await update.inline_query.answer(results, cache_time=1)

async def callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data

    if callback_data.startswith("grabber_stats_"):
        character_id = callback_data.split("_")[2]
        character = await collection.find_one({'id': character_id})
        if not character:
            await query.answer("Character not found.")
            return

        grabber_stats = await group_user_totals_collection.find({'character_id': character_id}).sort([('count', -1)]).to_list(length=10)
        top_grabbers = '\n'.join(f"➥ <a href='tg://user?id={stat['user_id']}'>{stat['username']}</a> 🍅 x{stat['count']}" for stat in grabber_stats)
        global_grabs = await collection.count_documents({'id': character_id})

        message = f"""🌎 Grabbed Globally: {global_grabs} times
        🎖️ Top 10 Grabbers Of This Waifu In This Chat
        {top_grabbers}"""

        await query.edit_message_text(message, parse_mode='HTML')

application.add_handler(CommandHandler("guess", guess))
application.add_handler(CommandHandler("fav", fav))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_counter))
application.add_handler(InlineQueryHandler(inline_query))
application.add_handler(CallbackQueryHandler(callback_query))

async def main() -> None:
    await application.start()
    await application.updater.start_polling()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
