import random
import logging
from opentele.tl import TelegramClient
from opentele.td import API
from typing import Union

# Example API settings (consider securing these in environment variables or a config file)
api_settings = [
    {
        'api_id': 20137158,
        'api_hash': '473aeb73e73b2da67a2b252bfb7e5277'
    },
    {
        "api_id": 2227391,
        "api_hash": "81f7429140163b499a496abdcc49db2e"
    }
]

async def telethonFromSession(path: str) -> Union[TelegramClient, bool]:
    """
    Create a TelegramClient instance from a session file.

    Args:
        path (str): Path to the session file.

    Returns:
        Union[TelegramClient, bool]: TelegramClient instance if successful, False otherwise.
    """
    try:
        api = random.choice(api_settings)
        logging.info(f"Using API settings: {api}")
        
        client = TelegramClient(
            path,
            API.TelegramDesktop(
                api_id=api['api_id'],
                api_hash=api['api_hash'],
                device_model="Desktop",
                system_version="Windows 10",
                app_version="3.4.3 x64",
                lang_code="en",
                system_lang_code="en-US",
                lang_pack="tdesktop"
            ),
            timeout=3
        )
        
        logging.info("TelegramClient instance created successfully.")
        return client
    except Exception as e:
        logging.error(f"Error creating TelegramClient instance: {e}")
        return False

# Example usage:
# Make sure to call this function within an async context
# client = await telethonFromSession('path/to/session.file')