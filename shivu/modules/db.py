from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import MessageHandler, filters

async def handle_photo(update: Update, context: CallbackContext):
    try:
        # Check if the message contains photos
        if update.message.photo:
            # Get the largest photo (last one in the list)
            photo = update.message.photo[-1]
            # Get the file object of the photo
            photo_file = await photo.get_file()
            
            # Download the photo
            file_path = await photo_file.download()

            # Perform your logic to process the image file here
            await update.message.reply_text(f"Photo received and saved to {file_path}")

        else:
            await update.message.reply_text("No photo found in the message.")

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Ensure you use the correct filter for photos
application.add_handler(MessageHandler(filters._Photo handle_photo))
