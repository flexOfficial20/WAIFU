@shivuu.on_message(filters.command(["status", "mystatus"]))
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

        # Fetch user-specific rarity counts
        rarity_counts = {
            '⚪ Common': sum(1 for char in user_characters if char.get('rarity') == '⚪ Common'),
            '🟢 Medium': sum(1 for char in user_characters if char.get('rarity') == '🟢 Medium'),
            '🟠 Rare': sum(1 for char in user_characters if char.get('rarity') == '🟠 Rare'),
            '🟡 Legendary': sum(1 for char in user_characters if char.get('rarity') == '🟡 Legendary'),
            '💠 Cosmic': sum(1 for char in user_characters if char.get('rarity') == '💠 Cosmic'),
            '💮 Exclusive': sum(1 for char in user_characters if char.get('rarity') == '💮 Exclusive'),
            '🔮 Limited Edition': sum(1 for char in user_characters if char.get('rarity') == '🔮 Limited Edition')
        }

        # Automatically fetch user profile photo
        user_profile_photo = message.from_user.photo.big_file_id if message.from_user.photo else None

        rarity_message = (
            "╔════════ • ✧ • ════════╗\n"
            "          ⛩  『𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲』  ⛩\n"
            "══════════════════════\n"
            f"➣ ❄️ 𝗡𝗮𝗺𝗲: {html.escape(message.from_user.full_name)}\n"
            f"➣ 🍀 𝗨𝘀𝗲𝗿 𝗜𝗗: {user_id}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 👾 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿𝘀 𝗖𝗼𝗹𝗹𝗲𝗰𝘁𝗲𝗱: {total_count}\n"
            f"➣ 💯 𝗣𝗲𝗿𝗰𝗲𝗻𝘁𝗮𝗀𝗲: {progress_percent:.2f}%\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"➣ 🏅 𝗥𝗮𝗻𝗄: {rank}\n"
            f"➣ 📈 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 𝗕𝗮𝗿:\n"
            f"[{progress_bar}]\n"
            f"({current_xp}/{next_level_xp} XP)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 𝗖𝗵𝗮𝘁 𝗧𝗼𝗽: {chat_top}\n"
            f"🌍 𝗚𝗹𝗼𝗯𝗮𝗹 𝗧𝗼𝗽: {global_top}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "               ✨ 𝐊𝐞𝐞𝐩 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐧𝐠 ✨\n"
            "╚════════ • ☆ • ════════╝\n"
            "╔════════ • ✧ • ════════╗\n"
            + "\n".join(f"├─➩ {rarity} Rarity: {count}" for rarity, count in rarity_counts.items()) + "\n"
            "╚════════ • ☆ • ════════╝"
        )

        if user_profile_photo:
            # Download and send user profile photo
            user_photo = await client.download_media(user_profile_photo)
            await message.reply_photo(
                photo=user_photo,
                caption=rarity_message
            )
        else:
            await message.reply_text(rarity_message)

        await loading_message.delete()

    except Exception as e:
        print(f"Error: {e}")
