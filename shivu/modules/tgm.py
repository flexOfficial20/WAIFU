from telegram import Update
from telegram.ext import CommandHandler
from shivu import application
from telegraph import Telegraph

# Create a Telegraph account for your bot
telegraph = Telegraph()
telegraph.create_account(short_name='ShivuBot')

# Function to create telegraph page
async def telegraph_link(update: Update, context):
    if context.args:
        title = ' '.join(context.args[:2])  # First 2 arguments as the title
        content = ' '.join(context.args[2:])  # Rest as content

        # Create Telegraph page
        response = telegraph.create_page(title, html_content=content)
        link = f"https://telegra.ph/{response['path']}"

        await update.message.reply_text(f"Telegraph link: {link}")
    else:
        await update.message.reply_text("Usage: /telegraph [title] [content]")

# Add command to Shivu bot
application.add_handler(CommandHandler("telegraph", telegraph_link))

# Run the bot
