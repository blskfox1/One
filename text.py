# -*- coding: utf-8 -*-

import re
import logging
from mnemonic import Mnemonic
from bs4 import BeautifulSoup
from string import punctuation
from typing import List, Tuple, Dict, Any

# Initialize logging
logging.basicConfig(level=logging.INFO)

def html_to_text(data: str) -> str:
    """
    Convert HTML content to plain text.

    Args:
        data (str): The HTML content.

    Returns:
        str: The plain text content.
    """
    try:
        data = data.strip()
        soup = BeautifulSoup(data, "lxml")
        text = BeautifulSoup(soup.prettify(), "lxml").get_text()
        return text if text else data
    except Exception as e:
        logging.error(f"Error converting HTML to text: {e}")
        return data


def is_mnemonic(data: str) -> bool:
    """
    Check if the given data is a valid mnemonic phrase.

    Args:
        data (str): The data to check.

    Returns:
        bool: True if the data is a valid mnemonic phrase, False otherwise.
    """
    try:
        data = data.strip()
        language = Mnemonic.detect_language(data)
        mnemo = Mnemonic(language)
        return mnemo.check(data)
    except Exception as e:
        logging.error(f"Error checking mnemonic: {e}")
        return False


def is_mnemonic_word(data: str, from_seed: str = "") -> bool:
    """
    Check if the given data is a mnemonic word.

    Args:
        data (str): The data to check.
        from_seed (str, optional): The seed to infer the language from. Defaults to "".

    Returns:
        bool: True if the data is a mnemonic word, False otherwise.
    """
    try:
        data = data.strip()
        if from_seed.strip():
            language = Mnemonic.detect_language(from_seed.strip())
        else:
            language = Mnemonic.detect_language(data)
        mnemo = Mnemonic(language)
        return data in mnemo.wordlist
    except Exception as e:
        logging.error(f"Error checking mnemonic word: {e}")
        return False


# Escaped punctuation characters
escaped_punctuation = '\\'.join(list(punctuation))

def is_mnemonic_no_words(data: str) -> bool:
    """
    Check if the given data is a mnemonic phrase without checking individual words.

    Args:
        data (str): The data to check.

    Returns:
        bool: True if the data is a mnemonic phrase without individual words, False otherwise.
    """
    try:
        data = data.strip()
        split = len(data.split(" "))
        if (split > 11) and (split < 25) and (len(list(re.finditer(f'[\d{escaped_punctuation}]', data, re.MULTILINE))) == 0):
            return True
    except Exception as e:
        logging.error(f"Error checking mnemonic without words: {e}")
        return False


def is_mnemonic_word_no_words(data: str, from_seed: str = "") -> bool:
    """
    Dummy function to always return True for mnemonic word check without words.

    Args:
        data (str): The data to check.
        from_seed (str, optional): The seed to infer the language from. Defaults to "".

    Returns:
        bool: Always returns True.
    """
    return True


async def parsing_crypto_from_string(main_data: str, config: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    """
    Parse cryptocurrency information from the given string data.

    Args:
        main_data (str): The main data string to parse.
        config (Dict[str, Any]): Configuration dictionary.

    Returns:
        Tuple[List[str], List[str], List[str]]: Lists of seeds, WIFs, and HEXs found in the data.
    """
    seeds_ret = []
    wifs_ret = []
    hexs_ret = []

    main_data = html_to_text(main_data).lower()

    if config.get("парсить_сидки", False):
        is_mnemonic_func = is_mnemonic if config.get("проверять_сидки_по_словарю", False) else is_mnemonic_no_words
        is_mnemonic_word_func = is_mnemonic_word if config.get("проверять_сидки_по_словарю", False) else is_mnemonic_word_no_words

        temp_1 = []
        main_data_split = (main_data + "\n").split("\n")

        for data_old in main_data_split:
            data_old = data_old.strip().replace("\n", " ").replace(",", " ")
            if not data_old:
                continue
            data_new = []
            for splitter in [":", ";", "-", " - ", "\t"]:
                try:
                    s = data_old.strip().split(splitter)
                    if s and data_old:
                        data_new.extend(s)
                except Exception as e:
                    logging.error(f"Error splitting data with {splitter}: {e}")

            for data in data_new:
                data = data.strip().replace("\n", " ").replace(",", " ")
                if len(data.split(" ")) > 11:
                    if data and is_mnemonic_func(data) and data not in seeds_ret:
                        seeds_ret.append(data)

                if config.get("детальный_парсинг", False):
                    if len(temp_1) > 11:
                        temp_1_join = " ".join(temp_1)
                        if is_mnemonic_func(temp_1_join) and temp_1_join not in seeds_ret:
                            seeds_ret.append(temp_1_join)
                            temp_1.clear()

                    if len((main_data + "\n").split("\n")) > 11:
                        temp_1_join = " ".join(temp_1)
                        line_normal = re.sub(r"[^\w\s]+|[\d]+", "", data).strip()
                        if is_mnemonic_word_func(line_normal, temp_1_join) and line_normal not in temp_1:
                            temp_1.append(line_normal)

                    if len(temp_1) > 24:
                        temp_1.clear()

    if config.get("парсить_виф_ключи", False):
        try:
            data = main_data.replace(" ", "").replace("\n", "")
            regex_wif = r"^5[HJK][1-9A-Za-z][^OIl]{48}$"
            wifs = re.findall(regex_wif, data)
            for wif in wifs:
                if wif not in wifs_ret:
                    wifs_ret.append(wif)
        except Exception as e:
            logging.error(f"Error parsing WIF keys: {e}")

    if config.get("парсить_хекс_ключи", False):
        try:
            data = main_data.replace(" ", "").replace("\n", "")
            regex_hex = r"[a-f0-9]{64}"
            hexs = re.findall(regex_hex, data)
            for hex in hexs:
                if hex not in hexs_ret:
                    hexs_ret.append(hex)
        except Exception as e:
            logging.error(f"Error parsing HEX keys: {e}")

    return seeds_ret, wifs_ret, hexs_ret