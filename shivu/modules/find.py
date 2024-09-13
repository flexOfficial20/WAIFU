from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from html import escape

from shivu import collection, application

async def find_character(update: Update, context: CallbackContext):
    # Get the character ID from the command arguments
    character_id = " ".join(context.args).strip()

    if not character_id:
        await update.message.reply_text("Please provide a character ID to search for.")
        return

    # Search for the character by ID in the collection
    character = await collection.find_one({"id": character_id})

    if not character:
        await update.message.reply_text("No character found with that ID.")
        return

    # Prepare the response message with character details
    response_message = (
        f"🧩 𝖶𝖺𝗂𝖿𝗎 𝖨𝗇𝖿𝗈𝗋𝗆𝖺𝗍𝗂𝗈𝗇:\n\n"
        f"🪭 𝖭𝖺𝗆𝖾: {escape(character['name'])}\n"
        f"⚕️ 𝖱𝖺𝗋𝗂𝗍𝗒: {escape(character['rarity'])}\n"
        f"⚜️ 𝖠𝗇𝗂𝗆𝖾: {escape(character['anime'])}\n"
        f"🪅 𝖨𝖣: {escape(character['id'])}\n\n"
    )

    # Send the image if it exists
    if 'image_url' in character:
        await update.message.reply_photo(photo=character['image_url'], caption=response_message)
    else:
        await update.message.reply_text(response_message)

    # Prepare user list
    user_list_message = "✳️ 𝖧𝖾𝗋𝖾 𝗂𝗌 𝗍𝗁𝖾 𝗅𝗂𝗌𝗍 𝗈𝖿 𝗎𝗌𝖾𝗋𝗌 𝗐𝗁𝗈 𝗁𝖺𝗏𝖾 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗋𝖺𝑐𝗍𝖾𝗋 〽️:\n"

    # Retrieve users who have the character
    user_cursor = collection.find({"character_id": character['id']})
    user_list = []
    async for user in user_cursor:
        user_list.append(f"{user['username']} x{user['count']}")

    if user_list:
        user_list_message += "\n".join(user_list)
    else:
        user_list_message += "No users found."

    await update.message.reply_text(user_list_message)

# Add handler for the /find command
application.add_handler(CommandHandler("find", find_character))

