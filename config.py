from configparser import ConfigParser
from typing import Union, Dict, Any
from app import pinfo, perror, fix_path, to_format_code
import os

# Example configuration
EXAMPLE_CONFIG = ConfigParser(default_section='ОСНОВНЫЕ')
EXAMPLE_CONFIG["ОСНОВНЫЕ"] = {
    'ТИП_РАБОТЫ': '1',
    'ПАПКА_ДАННЫХ': './data$bsp',
    'сохранять_путь_с_сидкой_при_парсе': 'True',
}

EXAMPLE_CONFIG["ЧЕК_ТЕЛЕГРАММ"] = {
    'КОПИРОВАТЬ_ВАЛИД': 'True',
    'СОХРАНЯТЬ_ДАННЫЕ_ТЕЛЕГРАММ': 'True',
    'ФОРМАТ_ДАННЫХ_ТЕЛЕГРАММ': r'@{username}: {path}',
    'ЗАМЕНЯТЬ_КОГДА_НЕТ_НИКА': r'{phone}',
    'МАКС_ВРЕМЯ_РАБОТЫ_ПОТОКА': '20',
    'МАКС_ПОТОКОВ': '50',
    'проверять_сидки_по_словарю': 'False',
}

EXAMPLE_CONFIG["ПАРСИНГ_ТЕЛЕГРАММ"] = {
    'МАКС_ВРЕМЯ_РАБОТЫ_ПОТОКА': '20',
    'МАКС_ПОТОКОВ': '50',
    "ПАРСИТЬ_СИДКИ": 'True',
    'ДЕТАЛЬНЫЙ_ПАРСИНГ': 'False',
    "ПАРСИТЬ_ВИФ_КЛЮЧИ": 'False',
    "ПАРСИТЬ_ХЕКС_КЛЮЧИ": 'False',
    'проверять_сидки_по_словарю': 'False',
}

EXAMPLE_CONFIG["ПАРСИНГ_ФАЙЛОВ"] = {
    'МАКС_ВРЕМЯ_РАБОТЫ_ПОТОКА': '20',
    'МАКС_ПОТОКОВ': '50',
    'ДЕТАЛЬНЫЙ_ПАРСИНГ': 'False',
    'ЧЕРНЫЙ_СПИСОК_ФАЙЛОВ': '*.exe,*.dll',
    'БЕЛЫЙ_СПИСОК_ФАЙЛОВ': '',
    "ПАРСИТЬ_СИДКИ": 'True',
    "ПАРСИТЬ_ВИФ_КЛЮЧИ": 'False',
    "ПАРСИТЬ_ХЕКС_КЛЮЧИ": 'False',
    'проверять_сидки_по_словарю': 'False',
}


def get_config_path() -> Union[str, bool]:
    """Get the path to the configuration file, creating it if it doesn't exist."""
    try:
        config_path = './config.ini'
        if not os.path.exists(config_path):
            pinfo('config.ini не найден, создание...')
            with open(fix_path(config_path), 'w', encoding='utf-8', errors='ignore') as config_file:
                EXAMPLE_CONFIG.write(config_file)
        return config_path
    except Exception as e:
        perror(f'При получении путя до конфига произошла ошибка: {e}')
        return False


def read_config(path: str) -> Union[ConfigParser, bool]:
    """Read the configuration file."""
    try:
        pinfo('Чтение конфига')
        config = ConfigParser(default_section='ОСНОВНЫЕ')
        with open(path, 'r', encoding='utf-8', errors='ignore') as config_file:
            config.read_file(config_file)
        return config
    except Exception as e:
        perror(f'При чтении конфига произошла ошибка: {e}')
        return False


def check_config(config: ConfigParser) -> bool:
    """Check the values of configuration parameters."""
    try:
        pinfo('Проверка значений у параметров конфига')
        valid = True
        for section in EXAMPLE_CONFIG.keys():
            for option in EXAMPLE_CONFIG[section].keys():
                try:
                    user_value = config.get(section, option)
                    to_format = to_format_code(user_value)
                    if str(to_format) != user_value:
                        perror(f'У значения параметра [white]`{section}/{option}`[/white] неверный тип: {type(to_format).__name__} != {type(user_value).__name__}')
                        valid = False
                except Exception as e:
                    valid = False
                    perror(f'При проверки значения у параметра [white]`{section}/{option}`[/white] произошла ошибка: {e}')
        return valid
    except Exception as e:
        perror(f'При проверки значений у параметров конфига произошла ошибка: {e}')
        return False


def config_to_dict(config: ConfigParser) -> Union[Dict[str, Dict[str, Any]], bool]:
    """Convert the configuration to a dictionary format."""
    try:
        pinfo('Приведение конфига в формат программы')
        result = {}
        for section in EXAMPLE_CONFIG.keys():
            result[section] = {}
            for option in EXAMPLE_CONFIG[section].keys():
                user_value = str(config.get(section, option)).strip()
                to_format = to_format_code(user_value)
                result[section][option] = to_format
        return result
    except Exception as e:
        perror(f'При приведении конфига в формат программы произошла ошибка: {e}')
        return False


def get_config() -> Union[Dict[str, Dict[str, Any]], bool]:
    """Get and validate the configuration."""
    try:
        pinfo('Получение конфига')
        path = get_config_path()
        if not path:
            return False
        config = read_config(path)
        if not config:
            return False
        if not check_config(config):
            return False
        config_dict = config_to_dict(config)
        if not config_dict:
            return False
        pinfo('Конфиг получен без ошибок')
        return config_dict
    except Exception as e:
        perror(f'При получении конфига произошла ошибка: {e}')
        return False