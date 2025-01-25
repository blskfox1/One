import logging
from secrets import token_hex
from opentele.api import UseCurrentSession
from opentele.td import TDesktop
from app import fix_path, remove_file


async def telethonsFromTdata(path: str):
    """
    Create a list of Telethon client instances from a tdata folder.

    Args:
        path (str): Path to the tdata folder.

    Returns:
        list: List containing a single Telethon client instance, or False if an error occurs.
    """
    try:
        # Initialize TDesktop with the given tdata path
        tdesk = TDesktop(path)
        account = tdesk.mainAccount
        
        # Generate a unique session file name
        name = fix_path(path, f"/id{account.UserId}#{token_hex(2)}$bsp.session")
        
        # Remove any existing session file with the same name
        remove_file(name)
        
        # Create a Telethon client instance using the current session
        client = await account.ToTelethon(name, UseCurrentSession, timeout=3)
        
        # Return the client instance in a list
        return [client]
    except Exception as e:
        logging.error(f"Error creating Telethon client from tdata: {e}")
        return False

# Example usage:
# Ensure to call this function within an async context
# clients = await telethonsFromTdata('/path/to/tdata')