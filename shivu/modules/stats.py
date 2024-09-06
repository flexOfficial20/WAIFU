from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, db

# Fetch from your specific collections
groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

async def stat(update: Update, context: CallbackContext) -> None:
    try:
        # Retrieve statistics from collections
        total_groups = await groups_collection.count_documents({})
        total_users = await users_collection.count_documents({})
        total_characters = await characters_collection.count_documents({})

        # Retrieve harem count (Adjust the collection or criteria if needed)
        total_harem_count = await characters_collection.count_documents({'rarity': 'harem'})  # Change criteria if needed

        # Count characters by rarity
        common_count = await characters_collection.count_documents({'rarity': 'common'})
        medium_count = await characters_collection.count_documents({'rarity': 'medium'})
        rare_count = await characters_collection.count_documents({'rarity': 'rare'})
        legendary_count = await characters_collection.count_documents({'rarity': 'legendary'})
        cosmic_count = await characters_collection.count_documents({'rarity': 'cosmic'})
        exclusive_count = await characters_collection.count_documents({'rarity': 'exclusive'})
        limited_edition_count = await characters_collection.count_documents({'rarity': 'limited'})

        # Format the statistics message
        stats_message = (
            f"📊 Bot Stats 📊\n\n"
            f"👥 Total Groups: {total_groups}\n"
            f"👤 Total Users: {total_users}\n"
            f"🎴 Total Characters: {total_characters}\n"
            f"🔢 Harem Count: {total_harem_count}\n"
            f"⚜️ Characters Count Sorted By Rarity\n\n"
            f"⚪ Common: {common_count}\n"
            f"🟢 Medium: {medium_count}\n"
            f"🟠 Rare: {rare_count}\n"
            f"🟡 Legendary: {legendary_count}\n"
            f"💠 Cosmic: {cosmic_count}\n"
            f"💮 Exclusive: {exclusive_count}\n"
            f"🔮 Limited Edition: {limited_edition_count}\n"
        )

        # Send the statistics message
        await update.message.reply_text(stats_message)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Register the command handler
application.add_handler(CommandHandler("stat", stat))
