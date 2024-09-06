from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, db

# Fetch from your specific collections
groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']
harem_collection = db['user_totals_lmaoooo']

async def stat(update: Update, context: CallbackContext) -> None:
    total_groups = await groups_collection.count_documents({})
    total_users = await users_collection.count_documents({})
    total_characters = await characters_collection.count_documents({})
    total_harem_count = await harem_collection.count_documents({})

    # Count characters by rarity
    common_count = await characters_collection.count_documents({'rarity': 'common'})
    medium_count = await characters_collection.count_documents({'rarity': 'medium'})
    rare_count = await characters_collection.count_documents({'rarity': 'rare'})
    legendary_count = await characters_collection.count_documents({'rarity': 'legendary'})
    cosmic_count = await characters_collection.count_documents({'rarity': 'cosmic'})
    exclusive_count = await characters_collection.count_documents({'rarity': 'exclusive'})
    limited_edition_count = await characters_collection.count_documents({'rarity': 'limited'})

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

# Register the command handler
application.add_handler(CommandHandler("stat", stat))
