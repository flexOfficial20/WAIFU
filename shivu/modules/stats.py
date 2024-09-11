from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from shivu import application, db

groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

# Function to get user status
async def get_status(update: Update, context: CallbackContext) -> None:
    try:
        total_groups = await groups_collection.count_documents({})
        total_users = await users_collection.count_documents({})
        total_characters = await characters_collection.count_documents({})
        total_harem_count = await characters_collection.count_documents({'rarity': 'harem'})  # Change criteria if needed

        stats_message = (
            f"📊 Bot Stats 📊\n\n"
            f"👥 Total Groups: {total_groups}\n"
            f"👤 Total Users: {total_users}\n"
            f"🎴 Total Characters: {total_characters}\n"
            f"🔢 Harem Count: {total_harem_count}\n"
        )

        # Inline keyboard with rarity button
        keyboard = [
            [InlineKeyboardButton("Waifus 💫", callback_data='show_rarity')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message with the button
        await update.message.reply_text(stats_message, reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Callback for when rarity button is clicked
async def rarity_callback(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        await query.answer()

        # Aggregate users by rarity
        rarity_users_counts = {}
        rarities = ['⚪ Common', '🟢 Medium', '🟠 Rare', '🟡 Legendary', '💠 Cosmic', '💮 Exclusive', '🔮 Limited Edition']

        for rarity in rarities:
            # Count unique users with characters of this rarity
            users_with_rarity = await characters_collection.distinct(
                'user_id', {'rarity': rarity}
            )
            rarity_users_counts[rarity] = len(users_with_rarity)

        rarity_message = (
            f"⚜️ Characters Count Sorted By Rarity\n\n"
            f"⚪ Common: {rarity_users_counts.get('⚪ Common', 0)} users\n"
            f"🟢 Medium: {rarity_users_counts.get('🟢 Medium', 0)} users\n"
            f"🟠 Rare: {rarity_users_counts.get('🟠 Rare', 0)} users\n"
            f"🟡 Legendary: {rarity_users_counts.get('🟡 Legendary', 0)} users\n"
            f"💠 Cosmic: {rarity_users_counts.get('💠 Cosmic', 0)} users\n"
            f"💮 Exclusive: {rarity_users_counts.get('💮 Exclusive', 0)} users\n"
            f"🔮 Limited Edition: {rarity_users_counts.get('🔮 Limited Edition', 0)} users\n"
        )

        # Edit the message to show rarity information
        await query.edit_message_text(rarity_message)

    except Exception as e:
        await query.message.reply_text(f"An error occurred: {str(e)}")


# Add command handler for /status and callback for rarity button
application.add_handler(CommandHandler("status", get_status))
application.add_handler(CallbackQueryHandler(rarity_callback, pattern='show_rarity'))
