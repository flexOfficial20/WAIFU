from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
import asyncio
import html
from shivu import shivuu, collection, user_collection, group_user_totals_collection, db, application as app

# MongoDB Collections
groups_collection = db['top_global_groups']
users_collection = db['user_collection_lmaoooo']
characters_collection = db['anime_characters_lol']

async def get_chat_top(chat_id, user_id):
    # Function to fetch chat top
    # Placeholder for actual implementation
    return 3

async def get_global_top(user_id):
    # Function to fetch global top
    # Placeholder for actual implementation
    return 1

async def get_progress_bar(current_xp, next_level_xp):
    # Function to calculate the progress bar
    progress_percent = (current_xp / next_level_xp) * 100
    progress_bar = "▰" * int(progress_percent // 6) + "▱" * (16 - int(progress_percent // 6))
    return progress_bar, progress_percent

def get_rank(progress_percent):
    # Function to determine the rank based on progress percent
    if progress_percent >= 100:
        return "Heroic I"
    elif progress_percent >= 80:
        return "Heroic II"
    elif progress_percent >= 60:
        return "Elite"
    elif progress_percent >= 40:
        return "Advanced"
    else:
        return "Beginner"

async def get_user_rarity_counts(user_id):
    # Function to fetch rarity counts for the user
    user = await user_collection.find_one({'id': user_id})
    rarity_counts = user.get('rarity_counts', {})
    return {
        'Legendary': rarity_counts.get('Legendary', 0),
        'Rare': rarity_counts.get('Rare', 0),
        'Medium': rarity_counts.get('Medium', 0),
        'Common': rarity_counts.get('Common', 0)
    }

@app.on_message(filters.command(["status", "mystatus"]))
async def send_grabber_status(client, message):
    try:
        loading_message = await message.reply("🔄 Fetching Grabber Status...")

        for i in range(1, 6):
            await asyncio.sleep(1)
            await loading_message.edit_text("🔄 Fetching Grabber Status" + "." * i)

        user_id = message.from_user.id
        user = await user_collection.find_one({'id': user_id})

        if user:
            user_characters = user.get('characters', [])
            total_count = len(user_characters)
        else:
            total_count = 0

        total_waifus_count = await user_collection.count_documents({})

        chat_top = await get_chat_top(message.chat.id, user_id)
        global_top = await get_global_top(user_id)

        progress_bar, progress_percent = await get_progress_bar(total_count, total_waifus_count)
        rank = get_rank(progress_percent)
        current_xp = total_count
        next_level_xp = min(100, total_waifus_count)  # Ensure XP does not exceed total character count

        rarity_counts = await get_user_rarity_counts(user_id)

        profile_image_url = user.get('profile_image_url', None)

        rarity_message = (
            f"╔════════ • ✧ • ════════╗\n"
            f"          ⛩  『𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲』  ⛩\n"
            f"══════════════════════\n"
            f"➣ ❄️ 𝗡𝗮𝗺𝗲: {message.from_user.full_name}\n"
            f"➣ 🍀 𝗨𝘀𝗲𝗿 𝗜𝗗: {user_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 👾 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗲𝗱: {total_count}\n"
            f"➣ 💯 𝗣𝗲𝗿𝗰𝗲𝗻𝘁𝗮𝗀𝗲: {progress_percent:.2f}%\n"
            f"➣ 🎯 𝗥𝗮𝗻𝗸: {rank}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 🏅 𝗖𝗵𝗮𝘁 𝗧𝗼𝗽: {chat_top}\n"
            f"➣ 🌍 𝗚𝗹𝗼𝗯𝗮𝗹 𝗧𝗼𝗽: {global_top}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"               ✨ 𝐊𝐞𝐞𝐩 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐧𝐠 ✨\n"
            f"╚════════ • ☆ • ════════╝\n\n"
            f"╔════════ • ✧ • ════════╗\n"
            f"├─➩ 🟡 Rarity: Legendary: {rarity_counts['Legendary']}\n"
            f"├─➩ 🟠 Rarity: Rare: {rarity_counts['Rare']}\n"
            f"├─➩ 🔴 Rarity: Medium: {rarity_counts['Medium']}\n"
            f"├─➩ 🔵 Rarity: Common: {rarity_counts['Common']}\n"
            f"╚════════ • ☆ • ════════╝"
        )

        if profile_image_url:
            await message.reply_photo(
                photo=profile_image_url,
                caption=rarity_message
            )
        else:
            await message.reply_text(rarity_message)

        await loading_message.delete()

    except Exception as e:
        print(f"Error: {e}")

# Start the Pyrogram Client
