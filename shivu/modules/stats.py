from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, db


groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

async def stat(update: Update, context: CallbackContext) -> None:
    try:
        
        total_groups = await groups_collection.count_documents({})
        total_users = await users_collection.count_documents({})
        total_characters = await characters_collection.count_documents({})
        total_harem_count = await characters_collection.count_documents({'rarity': 'harem'})  # Change criteria if needed

        common_count = await characters_collection.count_documents({'rarity': '⚪ Common'})
        medium_count = await characters_collection.count_documents({'rarity': '🟢 Medium'})
        rare_count = await characters_collection.count_documents({'rarity': '🟠 Rare'})
        legendary_count = await characters_collection.count_documents({'rarity': '🟡 Legendary'})
        cosmic_count = await characters_collection.count_documents({'rarity': '💠 Cosmic'})
        exclusive_count = await characters_collection.count_documents({'rarity': '💮 Exclusive'})
        limited_edition_count = await characters_collection.count_documents({'rarity': '🔮 Limited Edition'})

        
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

        
        await update.message.reply_text(stats_message)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


application.add_handler(CommandHandler("stats", stat))
