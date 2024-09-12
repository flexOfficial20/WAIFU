from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import collection, application

async def search_character(update: Update, context: CallbackContext):
    # Get the name to search for from the command arguments
    name_to_search = " ".join(context.args).strip()

    if not name_to_search:
        await update.message.reply_text("Please provide a name to search for.")
        return

    # Search for characters by name in the total collection
    characters_cursor = collection.find({"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}})

    found_characters = []
    async for character in characters_cursor:
        found_characters.append(character)

    if not found_characters:
        await update.message.reply_text("No characters found with that name.")
        return

    # Prepare the response message with found characters
    response_message = "<b>Found Characters:</b>\n"
    for character in found_characters:
        response_message += f"ID: {character['id']}\n"
        response_message += f"Name: {escape(character['name'])}\n"
        response_message += f"Rarity: {escape(character['rarity'])}\n\n"

    await update.message.reply_text(response_message, parse_mode='HTML')

# Add handler for the /sips command
application.add_handler(CommandHandler("sips", search_character))
