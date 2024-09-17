from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from shivu import shivuu, collection, user_collection, group_user_totals_collection, db

# MongoDB Collections
groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

async def get_user_collection():
    return await user_collection.find({}).to_list(length=None)

async def get_user_rarity_counts(user_id):
    rarity_counts = {
        "Legendary": 0,
        "Rare": 0,
        "Medium": 0,
        "Common": 0
    }

    user = await user_collection.find_one({'id': user_id})
    if user:
        characters = user.get('characters', [])
        for char in characters:
            rarity = char.get('rarity', 'Common')
            if rarity == 'Legendary':
                rarity_counts['Legendary'] += 1
            elif rarity == 'Rare':
                rarity_counts['Rare'] += 1
            elif rarity == 'Medium':
                rarity_counts['Medium'] += 1
            elif rarity == 'Common':
                rarity_counts['Common'] += 1

    return rarity_counts

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

def get_rank(progress_percent):
    ranks = [
        (5, "Bronze 1"),
        (10, "Bronze 2"),
        (15, "Bronze 3"),
        (20, "Gold 1"),
        (25, "Gold 2"),
        (30, "Gold 3"),
        (35, "Platinum 1"),
        (40, "Platinum 2"),
        (45, "Platinum 3"),
        (50, "Platinum 4"),
        (55, "Diamond 1"),
        (60, "Diamond 2"),
        (65, "Diamond 3"),
        (70, "Diamond 4"),
        (75, "Master"),
    ]

    for percent, rank in ranks:
        if progress_percent <= percent:
            return rank

    return "Grandmaster"  # If progress_percent is above 75%

@shivuu.on_message(filters.command(["status", "mystatus"]))
async def send_grabber_status(client, message):
    try:
        loading_message = await message.reply("🔄 Fetching Grabber Status...")

        for i in range(1, 6):
            await asyncio.sleep(1)
            await loading_message.edit_text("🔄 Fetching Grabber Status" + "." * i)

        user_collection_data = await get_user_collection()
        user_collection_count = len(user_collection_data)

        user_id = message.from_user.id
        user = await user_collection.find_one({'id': user_id})

        if user:
            total_count = len(user.get('characters', []))
        else:
            total_count = 0

        total_waifus_count = await collection.count_documents({})

        chat_top = await get_chat_top(message.chat.id, user_id)
        global_top = await get_global_top(user_id)

        progress_bar, progress_percent = await get_progress_bar(total_count, total_waifus_count)
        rank = get_rank(progress_percent)
        current_xp = total_count
        next_level_xp = 100  # Adjust as needed

        rarity_counts = await get_user_rarity_counts(user_id)

        # Fetch user profile photo
        user_profile_photo = message.from_user.photo.big_file_id if message.from_user.photo else None

        grabber_status = (
            f"╔════════ • ✧ • ════════╗\n"
            f"          ⛩  『𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲』  ⛩\n"
            f"══════════════════════\n"
            f"➣ ❄️ 𝗡𝗮𝗺𝗲: `{message.from_user.first_name}` ┊𝗘 𝗠 𝗫 ™ 🐰\n"
            f"➣ 🍀 𝗨𝘀𝗲𝗿 𝗜𝗗: `{message.from_user.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 👾 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗲𝗱: {total_count}\n"
            f"➣ 💯 𝗣𝗲𝗿𝗰𝗲𝗻𝘁𝗮𝗀𝗲: {progress_percent:.2f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 🏅 𝗥𝗮𝗻𝗄: {rank}\n"
            f"➣ 📈 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 𝗕𝗮𝗿:\n"
            f"[{progress_bar}]\n"
            f"({current_xp}/{next_level_xp} XP)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 𝗖𝗵𝗮𝘁 𝗧𝗼𝗽: {chat_top}\n"
            f"🌍 𝗚𝗹𝗼𝗯𝗮𝗹 𝗧𝗼𝗽: {global_top}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"               ✨ 𝐊𝐞𝐞𝐩 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐧𝐠 ✨\n"
            f"╚════════ • ☆ • ════════╝"
        )

        rarity_status = (
            f"╔════════ • ✧ • ════════╗\n"
            f"├─➩ 🟡 Rarity: Legendary: {rarity_counts['Legendary']}\n"
            f"├─➩ 🟠 Rarity: Rare: {rarity_counts['Rare']}\n"
            f"├─➩ 🔴 Rarity: Medium: {rarity_counts['Medium']}\n"
            f"├─➩ 🔵 Rarity: Common: {rarity_counts['Common']}\n"
            f"╚════════ • ☆ • ════════╝"
        )

        if user_profile_photo:
            # Download and send user profile photo
            user_photo = await client.download_media(user_profile_photo)
            await message.reply_photo(photo=user_photo, caption=grabber_status, reply_markup=None)
        else:
            await message.reply_text(grabber_status, reply_markup=None)

        await message.reply_text(rarity_status)

        await loading_message.delete()

    except Exception as e:
        print(f"Error: {e}")

# Add other handlers and start the bot
# For example:
# application.add_handler(CommandHandler('status', send_grabber_status))
