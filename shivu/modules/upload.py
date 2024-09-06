import requests
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

# Rarity Map
rarity_map = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🔴 Rare",
    4: "🟡 Legendary",
    5: "🔮 Limited Edition",
    6: "💠 Cosmic"
}

WRONG_FORMAT_TEXT = """Wrong ❌ format... e.g., /upload Img_url character-name anime-name rarity-number

Use rarity numbers accordingly:
1 = 🟢 Common, 2 = 🔵 Medium, 3 = 🔴 Rare, 4 = 🟡 Legendary, 5 = 🔮 Limited Edition, 6 = 💠 Cosmic"""

# Check if URL is valid (for any source, including Pinterest, Google, etc.)
def is_valid_url(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Get next sequence number for ID
async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, {'$inc': {'sequence_value': 1}}, return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

# Upload handler
async def upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT)
            return

        character_name = args[1].replace('-', ' ').title()
        anime_name = args[2].replace('-', ' ').title()
        img_url = args[0]

        if not is_valid_url(img_url):
            await update.message.reply_text('Invalid URL. Please check and try again.')
            return

        try:
            rarity = rarity_map[int(args[3])]
        except KeyError:
            await update.message.reply_text('Invalid rarity. Use 1-6 for rarity.')
            return

        char_id = str(await get_next_sequence_number('character_id')).zfill(2)

        character = {
            'img_url': img_url,
            'name': character_name,
            'anime': anime_name,
            'rarity': rarity,
            'id': char_id
        }

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=f'<b>Character Name:</b> {character_name}\n<b>Anime Name:</b> {anime_name}\n<b>Rarity:</b> {rarity}\n<b>ID:</b> {char_id}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.insert_one(character)
            await update.message.reply_text('Character added successfully.')
        except Exception as e:
            await collection.insert_one(character)
            await update.message.reply_text(f"Added to database, but failed to post in channel. Error: {str(e)}")

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}\nContact support: {SUPPORT_CHAT}')

# Delete handler
async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Please use the format: /delete ID')
            return

        character = await collection.find_one_and_delete({'id': args[0]})
        if character:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            await update.message.reply_text('Character deleted.')
        else:
            await update.message.reply_text('Character not found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# Command Handlers
UPLOAD_HANDLER = CommandHandler('uploads', upload, block=False)
DELETE_HANDLER = CommandHandler('deletes', delete, block=False)

application.add_handler(UPLOAD_HANDLER)
application.add_handler(DELETE_HANDLER)
