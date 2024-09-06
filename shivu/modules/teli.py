from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
from shivu import application
IMGBB_API_KEY = '5a5dadd79df17356e7250672f8b1b00b'

# Function to upload file to ImgBB
def upload_to_imgbb(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={'key': IMGBB_API_KEY},
                files={'image': f}
            )
        response_data = response.json()
        if response_data['success']:
            return response_data['data']['url']
        return None
    except Exception as e:
        print(f"Error uploading to ImgBB: {str(e)}")
        return None

# Command handler for /imgbb
async def imgbb_upload(update: Update, context: CallbackContext) -> None:
    reply = update.message.reply_to_message
    if reply and reply.photo:
        i = await update.message.reply_text("𝐔ᴘʟᴏᴀᴅɪɴɢ 𝙔ᴏᴜʀ 𝐈ᴍᴀɢᴇ...")
        file = await reply.photo[-1].get_file()
        file_path = await file.download_as_bytearray()
        
        # Save the downloaded file temporarily
        with open("temp_image.jpg", "wb") as f:
            f.write(file_path)
        
        imgbb_url = upload_to_imgbb("temp_image.jpg")
        
        if imgbb_url:
            await i.edit_text(f'Yᴏᴜʀ ɪᴍᴀɢᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ! Hᴇʀᴇ\'s ᴛʜᴇ ᴜʀʟ:\n{imgbb_url}')
        else:
            await i.edit_text('Failed to upload image to ImgBB.')
    else:
        await update.message.reply_text("Please reply to an image with this command.")

# Initialize your Application object

# Add the command handler to the application
imgbb_handler = CommandHandler('imgbb', imgbb_upload)
application.add_handler(imgbb_handler)

# Run the bot
