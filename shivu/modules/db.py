from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext
from shivu import collection, application
import io

async def handle_photo(update: Update, context: CallbackContext) -> None:
    # Get the file_id of the photo
    photo_file = update.message.photo[-1].get_file()
    photo_file_id = update.message.photo[-1].file_id

    # Download the photo file
    photo_bytes = io.BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)  # Reset the file pointer to the beginning

    # Search the database for a matching image
    found_character = await collection.find_one({"image_id": photo_file_id})

    if found_character:
        character_name = found_character.get('name', 'Unknown')
        await update.message.reply_text(f"Character Name: {character_name}")
    else:
        await update.message.reply_text("No matching character found.")

# Add handlers for the /name command and photo messages
application.add_handler(CommandHandler("name", handle_photo))
application.add_handler(MessageHandler(filters._Photo, handle_photo))
