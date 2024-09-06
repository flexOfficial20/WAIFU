from pyrogram import Client, filters
import requests
from shivu import application as app
# Initialize your Pyrogram client

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
@app.on_message(filters.command(["imgbb"]))
def imgbb_upload(client, message):
    reply = message.reply_to_message
    if reply and reply.media:
        i = message.reply("𝐔ᴘʟᴏᴀᴅɪɴɢ 𝙔ᴏᴜʀ 𝐈ᴍᴀɢᴇ...")
        file_path = reply.download()
        imgbb_url = upload_to_imgbb(file_path)
        if imgbb_url:
            i.edit(f'Yᴏᴜʀ ɪᴍᴀɢᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ! Hᴇʀᴇ\'s ᴛʜᴇ ᴜʀʟ:\n{imgbb_url}')
        else:
            i.edit('Failed to upload image to ImgBB.')
    else:
        message.reply("Please reply to an image with this command.")

# Start the bot
