from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from shivu import shivuu, collection, user_collection, group_user_totals_collection
import asyncio

# Define button callback data
WAIFU_CATEGORIES = {
    "limited": "🔮 Limited Edition",
    "cosmic": "💠 Cosmic",
    "exclusive": "💮 Exclusive",
    "legendary": "🟡 Legendary",
    "rare": "🟠 Rare",
    "medium": "🟢 Medium",
    "common": "⚪ Common",
}

async def get_user_waifu_count_by_category(user_id):
    """Returns a dictionary of waifu counts by category for a user."""
    user = await user_collection.find_one({"id": user_id})
    if not user or 'characters' not in user:
        return {category: 0 for category in WAIFU_CATEGORIES}
    
    waifu_counts = {category: 0 for category in WAIFU_CATEGORIES}

    for waifu in user.get('characters', []):
        category = waifu.get('category')  # Assuming waifus have a 'category' field
        if category in waifu_counts:
            waifu_counts[category] += 1

    return waifu_counts

async def get_progress_bar(user_waifus_count, total_waifus_count):
    current = user_waifus_count
    total = total_waifus_count
    bar_width = 10

    progress = current / total if total != 0 else 0
    progress_percent = progress * 100

    filled_width = int(progress * bar_width)
    empty_width = bar_width - filled_width

    progress_bar = "▰" * filled_width + "▱" * empty_width
    return progress_bar, progress_percent

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

    return "Grandmaster"

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
        rank = get_rank(progress_percent)

        # Prepare the grabber status message
        grabber_status = (
            f"╔════════ • ✧ • ════════╗\n"
            f"          ⛩  『𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲』  ⛩\n"
            f"══════════════════════\n"
            f"➣ ❄️ 𝗡𝗮𝗺𝗲: `{message.from_user.first_name}`\n"
            f"➣ 🍀 𝗨𝘀𝗲𝗿 𝗜𝗗: `{message.from_user.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 👾 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗲𝗱: {total_count}\n"
            f"➣ 💯 𝗣𝗲𝗿𝗰𝗲𝗻𝘁𝗮𝗴𝗲: {progress_percent:.2f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 🏅 𝗥𝗮𝗻𝗸: {rank}\n"
            f"➣ 📈 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 𝗕𝗮𝗿:\n"
            f"[{progress_bar}]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"               ✨ 𝐊𝐞𝐞𝐩 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐧𝐠 ✨\n"
            f"╚════════ • ☆ • ════════╝"
        )

        # Create the inline keyboard with waifu categories
        buttons = [
            [InlineKeyboardButton(f"{icon} {name} → {user_waifu_counts[key]}", callback_data=f"waifu_{key}")]
            for key, name in WAIFU_CATEGORIES.items()
        ]

        buttons.append([InlineKeyboardButton("Waifus 💫", callback_data="waifu_main")])

        reply_markup = InlineKeyboardMarkup(buttons)

        # Send status message with buttons
        await message.reply_text(grabber_status, reply_markup=reply_markup)

    except Exception as e:
        print(f"Error: {e}")

# Handle button clicks for waifu categories
@shivuu.on_callback_query(filters.regex(r"^waifu_"))
async def handle_waifu_category(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")[1]

    if data == "main":
        # Main button redirect (back to profile or main waifu list)
        await send_grabber_status(client, callback_query.message)
    else:
        # Show waifus by category
        user_waifu_counts = await get_user_waifu_count_by_category(user_id)
        selected_category = WAIFU_CATEGORIES.get(data, "Unknown Category")

        # Simulate fetching waifus from the database based on category
        waifus_in_category = [f"Waifu {i+1}" for i in range(user_waifu_counts[data])]

        waifus_text = "\n".join(waifus_in_category) if waifus_in_category else "No waifus in this category."

        # Add a back button to return to the profile
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="waifu_main")]]
        )

        await callback_query.message.edit_text(
            f"🔮 **Category:** {selected_category}\n"
            f"👾 **Waifus:**\n{waifus_text}",
            reply_markup=back_button
        )
