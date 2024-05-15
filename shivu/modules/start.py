import random
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID, PHOTO_URL
from shivu import pm_users as collection


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})

        await context.bot.send_message(chat_id=GROUP_ID,
                                       text=f"New user Started The Bot..\n User: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
                                       parse_mode='HTML')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if update.effective_chat.type == "private":
        caption = """
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫   
  ✾ Wᴇʟᴄᴏᴍɪɴɢ ʏᴏᴜ ᴛᴏ ᴛʜᴇ Oᴛᴀᴋᴜ Cᴜʟᴛᴜʀᴇ   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
┠ ➻  I ᴡɪʟʟ Sᴜᴍᴍᴏɴ Wᴀɪғᴜ Cʜᴀʀᴀᴄᴛᴇʀs Iɴ
┃        ʏᴏᴜʀ Gʀᴏᴜᴘ Cʜᴀᴛ. 
┠ ➻  Yᴏᴜ ᴄᴀɴ sᴇᴀʟ ᴛʜᴇᴍ ʙʏ /catch ᴄᴏᴍᴍᴀɴᴅ 
┃         ᴀɴᴅ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ.
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
  Tᴀᴘ ᴏɴ "Hᴇʟᴘ" ғᴏʀ ᴍᴏʀᴇ ᴄᴏᴍᴍᴀɴᴅs."""
        keyboard = [
            [InlineKeyboardButton("➕ 𝖠𝖽𝖽 𝖬𝖾 I𝗇 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ➕", url=f'http://t.me/nudeXcatcherbot?startgroup=new')],
            [InlineKeyboardButton("𝖲𝗎𝗉𝗉𝗈𝗋𝗍 🍁", url=f'https://t.me/blade_x_support'),
             InlineKeyboardButton("𝖴𝗉𝖽𝖺𝗍𝖾𝗌 📈", url=f'https://t.me/blade_x_community')],
            [InlineKeyboardButton("𝖧𝖾𝗅𝗉 ⚙️", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption,
                                     reply_markup=reply_markup, parse_mode='markdown')

    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("➕ 𝖠𝖽𝖽 𝖬𝖾 I𝗇 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ➕", url=f'http://t.me/nudeXcatcherbot?startgroup=new')],
            [InlineKeyboardButton("𝖲𝗎𝗉𝗉𝗈𝗋𝗍 🍁", url=f'https://t.me/blade_x_support'),
             InlineKeyboardButton("𝖴𝗉𝖽𝖺𝗍𝖾𝗌 📈", url=f'https://t.me/blade_x_community')],
            [InlineKeyboardButton("𝖧𝖾𝗅𝗉 ⚙️", callback_data='help')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption,
                                     reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
    ***Help Section:***

***/guess: To Guess character (only works in group)***
***/fav: Add Your fav***
***/trade : To trade Characters***
***/gift: Give any Character from Your Collection to another user.. (only works in groups)***
***/collection: To see Your Collection***
***/topgroups : See Top Groups.. Ppl Guesses Most in that Groups***
***/top: Too See Top Users***
***/ctop : Your ChatTop***
***/changetime: Change Character appear time (only works in Groups)***
   """
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=query.message.message_id,
                                                caption=help_text, reply_markup=reply_markup, parse_mode='markdown')

    elif query.data == 'back':
        caption = """
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫   
  ✾ Wᴇʟᴄᴏᴍɪɴɢ ʏᴏᴜ ᴛᴏ ᴛʜᴇ Oᴛᴀᴋᴜ Cᴜʟᴛᴜʀᴇ   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
┠ ➻  I ᴡɪʟʟ Sᴜᴍᴍᴏɴ Wᴀɪғᴜ Cʜᴀʀᴀᴄᴛᴇʀs Iɴ
┃        ʏᴏᴜʀ Gʀᴏᴜᴘ Cʜᴀᴛ. 
┠ ➻  Yᴏᴜ ᴄᴀɴ sᴇᴀʟ ᴛʜᴇᴍ ʙʏ /catch ᴄᴏᴍᴍᴀɴᴅ 
┃         ᴀɴᴅ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ.
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━⧫
  Tᴀᴘ ᴏɴ "Hᴇʟᴘ" ғᴏʀ ᴍᴏʀᴇ ᴄᴏᴍᴍᴀɴᴅs.***
        """

        keyboard = [
            [InlineKeyboardButton("➕ 𝖠𝖽𝖽 𝖬𝖾 I𝗇 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ➕", url=f'http://t.me/nudeXcatcherbot?startgroup=new')],
            [InlineKeyboardButton("𝖲𝗎𝗉𝗉𝗈𝗋𝗍 🍁", url=f'https://t.me/blade_x_support'),
             InlineKeyboardButton("𝖴𝗉𝖽𝖺𝗍𝖾𝗌 📈", url=f'https://t.me/blade_x_community')],
            [InlineKeyboardButton("𝖧𝖾𝗅𝗉 ⚙️", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=query.message.message_id,
                                                caption=caption, reply_markup=reply_markup, parse_mode='markdown')


async def waifu_help(update: Update, context: CallbackContext) -> None:
    help_text = """
    ***Waifu Help Section:***

***/guess: To Guess character (only works in group)***
***/fav: Add Your fav***
***/trade : To trade Characters***
***/gift: Give any Character from Your Collection to another user.. (only works in groups)***
***/collection: To see Your Collection***
***/topgroups : See Top Groups.. Ppl Guesses Most in that Groups***
***/top: Too See Top Users***
***/ctop : Your ChatTop***
***/changetime: Change Character appear time (only works in Groups)***
   """
    help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(help_keyboard)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, reply_markup=reply_markup,
                                   parse_mode='markdown')


application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
application.add_handler(CallbackQueryHandler(waifu_help, pattern='^waifu$', block=False))
start_handler = CommandHandler('fucksstart', start, block=False)
application.add_handler(start_handler)
