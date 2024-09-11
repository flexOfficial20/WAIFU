from pyrogram import Client, filters
from shivu import shivuu, collection, user_collection, group_user_totals_collection
import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define waifu categories and their respective icons
WAIFU_CATEGORIES = {
    "Limited Edition": "🔮",
    "Cosmic": "💠",
    "Exclusive": "💮",
    "Legendary": "🟡",
    "Rare": "🟠",
    "Medium": "🟢",
    "Common": "⚪"
}

# Get user waifu counts based on category
async def get_user_waifu_count_by_category(user_id):
    user = await user_collection.find_one({'id': user_id})
    waifu_counts = {category: 0 for category in WAIFU_CATEGORIES}

    if user:
        for waifu in user.get('characters', []):
            waifu_category = waifu.get('rarity')
            if waifu_category in waifu_counts:
                waifu_counts[waifu_category] += 1

    return waifu_counts

# Get progress bar
async def get_progress_bar(user_waifus_count, total_waifus_count):
    current = user_waifus_count
    total = total_waifus_count
    bar_width = 10

    progress = current / total if total != 0 else 0
    progress_percent = progress * 100

    filled_width = int(progress * bar_width)
    empty_width = bar_width - filled_width

    progress_bar = "▰" * filled_width + "▱" * empty_width
    status = f"{progress_bar}"
    return status, progress_percent

# Get chat top rank
async def get_chat_top(chat_id: int, user_id: int) -> int:
    pipeline = [
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    cursor = group_user_totals_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('user_id') == user_id:
            return i
    
    return 0

# Get global top rank
async def get_global_top(user_id: int) -> int:
    pipeline = [
        {"$project": {"id": 1, "characters_count": {"$size": {"$ifNull": ["$characters", []]}}}},
        {"$sort": {"characters_count": -1}}
    ]
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('id') == user_id:
            return i
    
    return 0

# Status command with buttons
@shivuu.on_message(filters.command(["status", "mystatus"]))
async def send_grabber_status(client, message):
    try:
        user_id = message.from_user.id

        # Fetch user and waifu information
        user_waifu_counts = await get_user_waifu_count_by_category(user_id)
        total_waifus_count = await collection.count_documents({})

        # Get waifu counts and rank
        total_count = sum(user_waifu_counts.values())
        progress_bar, progress_percent = await get_progress_bar(total_count, total_waifus_count)
        chat_top = await get_chat_top(message.chat.id, user_id)
        global_top = await get_global_top(user_id)

        # Generate the buttons
        buttons = []
        for category, icon in WAIFU_CATEGORIES.items():
            buttons.append([InlineKeyboardButton(f"{icon} {category} → {user_waifu_counts[category]}", callback_data=f"waifu_{category}")])

        buttons.append([InlineKeyboardButton("Waifus 💫", callback_data="waifu_collection")])
        reply_markup = InlineKeyboardMarkup(buttons)

        # Create the user profile message
        grabber_status = (
            f"╔════════ • ✧ • ════════╗\n"
            f"⛩  『𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲』  ⛩\n"
            f"══════════════════════\n"
            f"➣ ❄️ 𝗡𝗮𝗺𝗲: {message.from_user.first_name}\n"
            f"➣ 🍀 𝗨𝘀𝗲𝗿 𝗜𝗗: {message.from_user.id}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 👾 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗲𝗱: {total_count}\n"
            f"➣ 💯 𝗣𝗲𝗿𝗰𝗲𝗻𝘁𝗮𝗴𝗲: {progress_percent:.2f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 📈 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 𝗕𝗮𝗿: [{progress_bar}]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 𝗖𝗵𝗮𝘁 𝗧𝗼𝗽: {chat_top}\n"
            f"🌍 𝗚𝗹𝗼𝗯𝗮𝗹 𝗧𝗼𝗽: {global_top}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨  𝐊𝐞𝐞𝐩 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐧𝐠 ✨\n"
            f"╚════════ • ☆ • ════════╝"
        )

        await client.send_message(
            chat_id=message.chat.id,
            text=grabber_status,
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"Error: {e}")

# Callback handler for buttons
@shivuu.on_callback_query(filters.regex(r"^waifu_"))
async def handle_waifu_category(client, callback_query):
    try:
        category = callback_query.data.split("_")[1]
        user_id = callback_query.from_user.id

        # Fetch the user's waifus in the selected category
        user = await user_collection.find_one({'id': user_id})
        if user:
            waifus = [waifu for waifu in user.get('characters', []) if waifu.get('rarity') == category]
            waifu_list = "\n".join([f"{waifu['name']} ({waifu['anime']})" for waifu in waifus])

            if waifu_list:
                await callback_query.message.edit_text(f"Your {category} Waifus:\n{waifu_list}")
            else:
                await callback_query.message.edit_text(f"You don't have any {category} waifus yet.")
        else:
            await callback_query.message.edit_text(f"You don't have any {category} waifus yet.")

        # Add a back button
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_to_profile")]])
        await callback_query.message.edit_reply_markup(reply_markup=back_button)

    except Exception as e:
        print(f"Error: {e}")

# Callback handler to go back to the profile
@shivuu.on_callback_query(filters.regex("back_to_profile"))
async def back_to_profile(client, callback_query):
    try:
        await send_grabber_status(client, callback_query.message)
    except Exception as e:
        print(f"Error: {e}")
