import importlib
import re
import asyncio
from shivu import application, LOGGER
from shivu.modules import ALL_MODULES
for module_name in ALL_MODULES:
    importlib.import_module("shivu.modules." + module_name)


def main() -> None:
    """Run bot."""

    application.run_polling(drop_pending_updates=True)
    
if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
