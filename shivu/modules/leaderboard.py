import os
import random
import html

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (
    application, PHOTO_URL, OWNER_ID,
    user_collection, top_global_groups_collection, 
    group_user_totals_collection, sudo_users as SUDO_USERS
)


async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = "<b>ᴛᴏᴘ 10 ɢʀᴀʙʙᴇʀs</b>\n\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'

    photo_url = random.choice(PHOTO_URL)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title or 'This Group'

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = f"<b>ᴛᴏᴘ 10 ɢʀᴀʙʙᴇʀs in {html.escape(chat_name)}</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <b>{first_name}</b> ➾ <b>{character_count}</b>\n'

    photo_url = random.choice(PHOTO_URL)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')




async def leaderboard(update: Update, context: CallbackContext) -> None:
    # Fetch all users with their character counts
    cursor = user_collection.find({}, {"_id": 0, "username": 1, "first_name": 1, "characters": 1})

    # Convert cursor to list
    leaderboard_data = await cursor.to_list(length=None)

    # Sort the list based on character count
    leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)

    # Limit to top 10 users
    leaderboard_data = leaderboard_data[:10]

    # Prepare the leaderboard message
    leaderboard_message = "<b>ᴛᴏᴘ 10 ᴜsᴇʀs ᴡɪᴛʜ ᴍᴏsᴛ ᴄʜᴀʀᴀᴄᴛᴇʀs</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = len(user.get('characters', []))  # Calculate character count
        leaderboard_message += f'{i}. <b>{first_name}</b> ➾ <b>{character_count}</b>\n'
    
    photo_url = random.choice(PHOTO_URL)

    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')


async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = await group_user_totals_collection.distinct('group_id')

    await update.message.reply_text(f'Total Users: {user_count}\nTotal groups: {len(group_count)}')


async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('Only for Sudo users...')
        return

    cursor = user_collection.find({})
    users = [document async for document in cursor]
    user_list = "\n".join(user['first_name'] for user in users)

    with open('users.txt', 'w') as f:
        f.write(user_list)

    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('users.txt')


async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in SUDO_USERS:
        update.message.reply_text('Only for Sudo users...')
        return

    cursor = top_global_groups_collection.find({})
    groups = [document async for document in cursor]
    group_list = "\n\n".join(group['group_name'] for group in groups)

    with open('groups.txt', 'w') as f:
        f.write(group_list)

    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('groups.txt')


# Add handlers for commands
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('statss', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))
