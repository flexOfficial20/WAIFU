from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
import math
from html import escape 
import random

from shivu import collection, user_collection, application
from telegram.error import BadRequest  # Importing BadRequest here

MAX_CAPTION_LENGTH = 1024  # Define the maximum allowed caption length


async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        if update.message:
            await update.message.reply_text('You Have Not Guessed any Characters Yet..')
        else:
            await update.callback_query.edit_message_text('You Have Not Guessed any Characters Yet..')
        return

    characters = sorted(user['characters'], key=lambda x: (x['anime'], x['id']))

    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}

    rarity_mode = await get_user_rarity_mode(user_id)

    if rarity_mode != 'All':
        characters = [char for char in characters if char.get('rarity') == rarity_mode]

    total_pages = math.ceil(len(characters) / 15)

    if page < 0 or page >= total_pages:
        page = 0

    harem_message = f"{escape(update.effective_user.first_name)}'s Harem - Page {page+1}/{total_pages}\n"

    current_characters = characters[page*15:(page+1)*15]

    current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, characters in current_grouped_characters.items():
        harem_message += f'\n{anime}'

        for character in characters:
            count = character_counts[character['id']]
            rarity = character['rarity']
            harem_message += f'\nID: {character["id"]}\n'
            harem_message += f'RARITY: {rarity}\n'
            harem_message += f'CHARACTER: {character["name"]} ×{count}\n\n'

    # Truncate the harem message if it exceeds the maximum length
    if len(harem_message) > MAX_CAPTION_LENGTH:
        harem_message = harem_message[:MAX_CAPTION_LENGTH]

    total_count = len(user['characters'])

    keyboard = [
        [InlineKeyboardButton(f"See Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")],
        [InlineKeyboardButton("Change Rarity Mode", callback_data="haremmode")]
    ]

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}"))
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if 'favorites' in user and user['favorites']:
            fav_character_id = user['favorites'][0]
            fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)

            if fav_character and 'img_url' in fav_character:
                if update.message:
                    await update.message.reply_photo(photo=fav_character['img_url'], caption=harem_message, reply_markup=reply_markup)
                else:
                    try:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                    except BadRequest:
                        await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            else:
                if update.message:
                    await update.message.reply_text(harem_message, reply_markup=reply_markup)
                else:
                    try:
                        await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                    except BadRequest:
                        await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            if user['characters']:
                random_character = random.choice(user['characters'])

                if 'img_url' in random_character:
                    if update.message:
                        await update.message.reply_photo(photo=random_character['img_url'], caption=harem_message, reply_markup=reply_markup)
                    else:
                        try:
                            await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                        except BadRequest:
                            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
                else:
                    if update.message:
                        await update.message.reply_text(harem_message, reply_markup=reply_markup)
                    else:
                        try:
                            await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup)
                        except BadRequest:
                            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            else:
                if update.message:
                    await update.message.reply_text("Your List is Empty :)")
    except Exception as e:
        print(f"Failed to edit message: {e}")

async def haremmode(update: Update, context: CallbackContext):
    rarities_buttons = [
        [InlineKeyboardButton("⚪️ Common", callback_data="rarity:⚪️ Common"), InlineKeyboardButton("🟣 Rare", callback_data="rarity:🟣 Rare"), InlineKeyboardButton("🟡 Legendary", callback_data="rarity:🟡 Legendary")],
        [InlineKeyboardButton("🟢 Medium", callback_data="rarity:🟢 Medium"), InlineKeyboardButton("💮 Special Edition", callback_data="rarity:💮 Special Edition"), InlineKeyboardButton("🔮 Limited Edition", callback_data="rarity:🔮 Limited Edition")],
        [InlineKeyboardButton("🎐 Celestial", callback_data="rarity:🎐 Celestial")],
        [InlineKeyboardButton("All", callback_data="rarity:All")]
    ]

    reply_markup = InlineKeyboardMarkup(rarities_buttons)

    if update.message:
        await update.message.reply_text("Select a rarity mode:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("Select a rarity mode:", reply_markup=reply_markup)


async def haremmode_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    # Set the rarity mode in user collection
    user_id = update.effective_user.id
    await update_user_rarity_mode(user_id, data.split(':')[1])

    # Trigger the harem function
    await harem(update, context)



async def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")


async def get_user_rarity_mode(user_id: int) -> str:
    user = await user_collection.find_one({'id': user_id})
    if user and 'rarity_mode' in user:
        return user['rarity_mode']
    return 'All'  # Default rarity mode is 'All'


async def update_user_rarity_mode(user_id: int, rarity_mode: str) -> None:
    await user_collection.update_one({'id': user_id}, {'$set': {'rarity_mode': rarity_mode}}, upsert=True)




application.add_handler(CommandHandler("hmode", haremmode))
application.add_handler(CommandHandler("harem", harem))
application.add_handler(CallbackQueryHandler(haremmode_callback, pattern='^rarity:'))
application.add_error_handler(error)
