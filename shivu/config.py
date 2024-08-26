class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "7453770651"
    sudo_users = "7453770651", "6996612518", "6454320047", "6257270528", "6574393060", "1292648081", "6532639723", "6453545159", "6806075764", "5610811504"
    GROUP_ID = -1001975521991
    TOKEN = "6993647727:AAGEsZVoOEPpKuuGwrnHc1o1bQoCLRAykAI"
    mongo_url = "mongodb+srv://vikas:vikas@vikas.yfezexk.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://telegra.ph/file/dc0aa314d28a67af0ee83.jpg", "https://telegra.ph/file/e3bdc6e1f14191e058ea7.jpg", "https://telegra.ph/file/dc0aa314d28a67af0ee83.jpg"]
    SUPPORT_CHAT = "-1001975521991"
    UPDATE_CHAT = "Nᴀʀᴜᴛᴏ Uᴘᴅᴀᴛᴇs"
    BOT_USERNAME = "nudeXcatchrbot"
    CHARA_CHANNEL_ID = "-1001975521991"
    api_id = 22792918
    api_hash = "ff10095d2bb96d43d6eb7a7d9fc85f81"
    
    STRICT_GBAN = True
    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
