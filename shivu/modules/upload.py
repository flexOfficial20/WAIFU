import logging
import requests
import urllib.request
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

# Setup logging for debugging and error tracking
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR)

# Rarity Map
rarity_map = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🔴 Rare",
    4: "🟡 Legendary",
    5: "🔮 Limited Edition",
    6: "💠 Cosmic"
}

WRONG_FORMAT_TEXT = """Wrong ❌ format...  eg. /upload Img_url muzan-kibutsuji Demon-slayer 3

img_url character-name anime-name rarity-number

Use rarity number accordingly:

1 (🟢 Common), 2 (🔵 Medium), 3 (🔴 Rare), 4 (🟡 Legendary), 5 (🔮 Limited Edition), 6 (💠 Cosmic)"""

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

# Upload character command
async def upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT)
            return

        character_name = args[1].replace('-', ' ').title()
        anime = args[2].replace('-', ' ').title()

        try:
            urllib.request.urlopen(args[0])
        except:
            await update.message.reply_text('Invalid URL.')
            return

        try:
            rarity = rarity_map[int(args[3])]
        except KeyError:
            await update.message.reply_text('Invalid rarity. Please use 1, 2, 3, 4, 5, or 6.')
            return

        id = str(await get_next_sequence_number('character_id')).zfill(2)

        character = {
            'img_url': args[0],
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'id': id
        }

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=args[0],
                caption=f'<b>Character Name:</b> {character_name}\n<b>Anime Name:</b> {anime}\n<b>Rarity:</b> {rarity}\n<b>ID:</b> {id}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.insert_one(character)
            await update.message.reply_text('Character added.')
        except Exception as e:
            logging.error(f"Failed to send photo or insert into DB: {e}")
            await collection.insert_one(character)
            await update.message.reply_text("Character added but no database channel found. Consider adding one.")
        
    except Exception as e:
        logging.error(f'Character upload unsuccessful. Error: {str(e)}')
        await update.message.reply_text(f'Character upload unsuccessful. Error: {str(e)}\nIf you think this is a source error, forward to: {SUPPORT_CHAT}')

# Delete character command
async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('Ask my Owner to use this Command...')
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format... Please use: /delete ID')
            return

        character = await collection.find_one_and_delete({'id': args[0]})
        if character:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            await update.message.reply_text('Character deleted successfully.')
        else:
            await update.message.reply_text('Character deleted from DB, but not found in Channel.')
    except Exception as e:
        logging.error(f"Error in delete command: {str(e)}")
        await update.message.reply_text(f'Error: {str(e)}')

# Update character command
async def update_character(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text('Incorrect format. Please use: /update id field new_value')
            return

        character = await collection.find_one({'id': args[0]})
        if not character:
            await update.message.reply_text('Character not found.')
            return

        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if args[1] not in valid_fields:
            await update.message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
            return

        new_value = args[2]
        if args[1] in ['name', 'anime']:
            new_value = new_value.replace('-', ' ').title()
        elif args[1] == 'rarity':
            try:
                new_value = rarity_map[int(new_value)]
            except KeyError:
                await update.message.reply_text('Invalid rarity. Please use 1, 2, 3, 4, 5, or 6.')
                return

        await collection.find_one_and_update({'id': args[0]}, {'$set': {args[1]: new_value}})

        if args[1] == 'img_url':
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=new_value,
                caption=f'<b>Character Name:</b> {character["name"]}\n<b>Anime Name:</b> {character["anime"]}\n<b>Rarity:</b> {character["rarity"]}\n<b>ID:</b> {character["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            await collection.find_one_and_update({'id': args[0]}, {'$set': {'message_id': message.message_id}})
        else:
            await context.bot.edit_message_caption(
                chat_id=CHARA_CHANNEL_ID,
                message_id=character['message_id'],
                caption=f'<b>Character Name:</b> {character["name"]}\n<b>Anime Name:</b> {character["anime"]}\n<b>Rarity:</b> {character["rarity"]}\n<b>ID:</b> {character["id"]}\nUpdated by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )

        await update.message.reply_text('Character updated.')
    except Exception as e:
        logging.error(f'Error in update command: {str(e)}')
        await update.message.reply_text('Error: Could not update the character.')

# Check character by ID
async def check(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check id')
            return

        character = await collection.find_one({'id': args[0]})
        if character:
            message = f"<b>Character Name:</b> {character['name']}\n" \
                      f"<b>Anime Name:</b> {character['anime']}\n" \
                      f"<b>Rarity:</b> {character['rarity']}\n" \
                      f"<b>ID:</b> {character['id']}\n"
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=character['img_url'], caption=message, parse_mode='HTML')
        else:
            await update.message.reply_text("Character not found.")
    except Exception as e:
        logging.error(f"Error in check command: {str(e)}")
        await update.message.reply_text(f"Error occurred: {e}")

# Check total characters
async def check_total_characters(update: Update, context: CallbackContext) -> None:
    try:
        total_characters = await collection.count_documents({})
        await update.message.reply_text(f"Total number of characters: {total_characters}")
    except Exception as e:
        logging.error(f"Error in total command: {str(e)}")
        await update.message.reply_text(f"Error occurred: {e}")

# Gen (Upload to Catbox) command
async def gen(update: Update, context: CallbackContext) -> None:
    file = None

    # Check if the user sent a document or an image
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
    elif update.message.photo:
        # Get the highest resolution of the image (last one in the array)
        file = await context.bot.get_file(update.message.photo[-1].file_id)
    else:
        await update.message.reply_text("Please reply with an image or upload a file to generate a link.")
        return

    try:
        # Download the file and upload it to Catbox
        file_path = await file.download()
        catbox_url = upload_to_catbox(file_path)
        await update.message.reply_text(f"File uploaded to Catbox: {catbox_url}")
    except Exception as e:
        logging.error(f"Error in gen command: {str(e)}")
        await update.message.reply_text(f"Error uploading file: {e}")

# Upload file to Catbox
def upload_to_catbox(file_path):
    url = 'https://catbox.moe/user/api.php'
    with open(file_path, 'rb') as f:
        response = requests.post(url, files={'fileToUpload': f}, data={'action': 'upload', 'format': 'json'})
    return response.json().get('url', '')

# Command handlers
application.add_handler(CommandHandler("upload", upload))
application.add_handler(CommandHandler("delete", delete))
application.add_handler(CommandHandler("update", update_character))
application.add_handler(CommandHandler("check", check))
application.add_handler(CommandHandler("total", check_total_characters))
application.add_handler(CommandHandler("gen", gen))

