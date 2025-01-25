import ast
import datetime as dt
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from secrets import token_hex

import aiofiles
import python_socks
import pytz
from fs.osfs import OSFS
from opentele.tl import TelegramClient
from requests import get
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from app.logger import perror, pinfo

# Constants
TELEGRAM_DATA_FILE = "./data.telegram$bsp.txt"
SEEDS_FILE = "./seeds$bsp.txt"
WIFS_FILE = "./wifs$bsp.txt"
HEXS_FILE = "./hexs$bsp.txt"
SEEDS_AND_PATH_FILE = "./seeds_and_path$bsp.txt"

def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def run(cmd: str) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, check=True, encoding="utf-8")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        return None


def guid() -> str:
    """Get the machine UUID based on the OS."""
    if sys.platform == "darwin":
        return "BCEC5B4C-223D-11B2-A85C-D4D33CBE644F"
    elif sys.platform in ["win32", "cygwin", "msys"]:
        return run("wmic csproduct get uuid").split("\n")[2].strip()
    elif sys.platform.startswith("linux"):
        return run("cat /var/lib/dbus/machine-id").strip() or run("cat /etc/machine-id").strip()
    elif sys.platform.startswith("openbsd") or sys.platform.startswith("freebsd"):
        return "ERR"
    return "Unsupported OS"


async def save_result_checker(config: dict, checker, type: str):
    """Save result checker data."""
    pinfo("Saving data")
    if config["ЧЕК_ТЕЛЕГРАММ"]["копировать_валид"]:
        save_path = fix_path(f"./{type}.valid$bsp/")
        create_dir(save_path)
        valid_items = checker.valid_tdatas if type == "tdatas" else checker.valid_sessions
        for item in valid_items:
            try:
                save_dir = fix_path(save_path, f"/{type[:-1]}#{token_hex(2)}$bsp/")
                copy_dir(item[0], save_dir)
                pinfo(f"Copied {item[0]} to {save_dir} successfully")
            except Exception as e:
                perror(f"Error copying {item[0]}: {e}")

    if config["ЧЕК_ТЕЛЕГРАММ"]["сохранять_данные_телеграмм"]:
        for item in checker.valid_tdatas if type == "tdatas" else checker.valid_sessions:
            try:
                save_path = fix_path(TELEGRAM_DATA_FILE)
                await write_file(save_path, item[1], True)
            except Exception as e:
                perror(f"Error saving telegram data {item[0]}: {e}")

    valid_count = len(checker.valid_tdatas) if type == "tdatas" else len(checker.valid_sessions)
    pinfo(f"Valid count: {valid_count}")


async def save_result_parser(config, parser):
    """Save result parser data."""
    pinfo("Saving data")

    is_save_seed_path = config["ОСНОВНЫЕ"]["сохранять_путь_с_сидкой_при_парсе"]
    seeds = parser.seeds
    wifs = list(set(parser.wifs))
    hexs = list(set(parser.hexs))
    if is_save_seed_path:
        seeds_new = list(map(lambda x: f"{x[0]} ------ {x[1]}", seeds))
        pinfo(f"Saving {len(seeds)} seed phrases with paths")
        await write_file(SEEDS_AND_PATH_FILE, "\n".join(seeds_new), True)
    seeds = list(map(lambda x: x[0], seeds))
    if seeds:
        pinfo(f"Saving {len(seeds)} seed phrases")
        await write_file(SEEDS_FILE, "\n".join(seeds), True)
    if wifs:
        pinfo(f"Saving {len(wifs)} WIF keys")
        await write_file(WIFS_FILE, "\n".join(wifs), True)
    if hexs:
        pinfo(f"Saving {len(hexs)} hex keys")
        await write_file(HEXS_FILE, "\n".join(hexs), True)


def clear_console():
    """Clear console."""
    if sys.platform == "win32" or sys.platform == "cygwin" or sys.platform == "msys":
        os.system("cls")
    else:
        os.system("clear")


def get_unix() -> int:
    """Get timestamp."""
    return int(time.time())


def get_date() -> dt.datetime:
    """Get datetime."""
    tz = pytz.timezone("Europe/Moscow")
    return dt.datetime.now(tz=tz)


def copy_dir(src: str, dist: str) -> bool:
    """Copy folder."""
    try:
        shutil.copytree(src, dist, dirs_exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error copying directory {src} to {dist}: {e}")
        return False


def copy_file(src: str, dist: str) -> bool:
    """Copy file."""
    try:
        shutil.copyfile(src, dist)
        return True
    except Exception as e:
        logging.error(f"Error copying file {src} to {dist}: {e}")
        return False


def isClass(obj, class_target) -> bool:
    """Check if object is instance of class_target."""
    try:
        class_target(obj)
        return True
    except TypeError:
        return False


def line_crop(line: str, max_len: int = 18, crop_type: str = "end") -> str:
    """Crop line (add ... and crop)."""
    if len(line) > max_len:
        if crop_type == "end":
            return line[: max_len - 3] + "..."
        elif crop_type == "start":
            return "..." + line[max_len - 3 :]
        else:
            return line[: max_len - 3] + "..."
    else:
        return line


def remove_dir(path: str) -> bool:
    """Remove directory."""
    try:
        shutil.rmtree(path, True)
        return True
    except Exception as e:
        logging.error(f"Error removing directory {path}: {e}")
        return False


def remove_file(path: str) -> bool:
    """Remove file."""
    try:
        os.remove(path)
        return True
    except Exception as e:
        logging.error(f"Error removing file {path}: {e}")
        return False


def create_dir(path: str) -> str:
    """Create directory."""
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception as e:
        logging.error(f"Error creating directory {path}: {e}")
        return ""


def get_root_path() -> str:
    """Get current working directory."""
    try:
        return os.getcwd()
    except Exception as e:
        logging.error(f"Error getting current working directory: {e}")
        return "./"


async def read_file(path: str, as_bytes: bool = False):
    """Read file asynchronously."""
    mode = "rb" if as_bytes else "r"
    try:
        async with aiofiles.open(path, mode, encoding=None if as_bytes else "utf-8", errors="ignore") as file:
            return await file.read()
    except Exception as e:
        logging.error(f"Error reading file {path}: {e}")
        return b"" if as_bytes else ""


async def write_file(path: str, data, append: bool = False, as_bytes: bool = False) -> bool:
    """Write data to a file asynchronously."""
    mode = "ab+" if append and as_bytes else "wb" if as_bytes else "a+" if append else "w+"
    try:
        async with aiofiles.open(path, mode, encoding=None if as_bytes else "utf-8", errors="ignore") as file:
            await file.write(data)
        return True
    except Exception as e:
        logging.error(f"Error writing to file {path}: {e}")
        return False


def to_format_code(data: str):
    """Convert string to formatted code."""
    try:
        data = str(data)
        js = ast.literal_eval(data)
        return js
    except Exception:
        return data


def to_json(data: str) -> dict:
    """Convert string to JSON."""
    try:
        data = str(data)
        js = ast.literal_eval(data)
        if type(js) != dict:
            return {}
        return js
    except Exception:
        return {}


def to_list(data: str) -> list:
    """Convert string to list."""
    try:
        data = str(data)
        js = ast.literal_eval(data)
        if type(js) != list:
            return []
        return js
    except Exception:
        return []


def fix_path(root: str, *paths) -> str:
    """Fix path."""
    if paths:
        paths = map(fix_path, paths)
    if root.startswith("./"):
        path = os.path.normpath(root.replace("\\", "/"))
        path = os.path.normpath(get_root_path() + "//" + root)
        if paths:
            path = os.path.normpath(path + "/".join(paths))
    else:
        path = os.path.normpath(root.replace("\\", "/"))
        if paths:
            path = os.path.normpath(path + "/".join(paths))
    return path


def find_files(root: str, keywords: list = None, print_log: bool = False, black_list_files=[]) -> list:
    """Find files."""
    try:
        osfs = OSFS(root)
        result = []
        if black_list_files == []:
            black_list_files = None
        if print_log:
            pinfo("Searching for data...")
        result = [
            file
            for file in osfs.walk.files(
                filter=keywords, exclude=black_list_files, ignore_errors=True, search="depth"
            )
        ]
        if result and print_log:
            pinfo(f"Search completed: {len(result)} files found")
        return result
    except KeyboardInterrupt:
        pinfo(f"Search interrupted: {len(result)} files found")
        return []
    except Exception as e:
        perror(f"Error during search: {e}")
        return []


def proxy_format(proxies: list) -> list:
    """Format proxies to standard format."""
    result = []
    for proxy in proxies:
        try:
            proxy_dict = {}
            type = proxy.split("://")[0]
            data = proxy.split("://")[1]
            if type == "http":
                type = python_socks.ProxyType.HTTP
            elif type == "socks4":
                type = python_socks.ProxyType.SOCKS4
            elif type == "socks5":
                type = python_socks.ProxyType.SOCKS5
            else:
                continue
            isAuthProxy = "@" in proxy
            if isAuthProxy:
                auth = data.split("@")[0]
                con_data = data.split("@")[1]
                user, password = auth.split(":")
                addr, port = con_data.split(":")
                proxy_dict.update(type=type, user=user, password=password, addr=addr, port=int(port))
            else:
                con_data = data
                addr, port = con_data.split(":")
                proxy_dict.update(type=type, addr=addr, port=int(port))
            result.append(proxy_dict)
        except Exception as e:
            logging.error(f"Error formatting proxy {proxy}: {e}")
            pass
    return result


def proxy_get(proxies: list):
    """Get a random proxy."""
    if proxies:
        default_ip = get("https://ipinfo.io/ip").text
        proxy_dict: dict = random.choice(proxies)
        type = proxy_dict.get("type")
        if type == python_socks.ProxyType.HTTP:
            type = "http"
        elif type == python_socks.ProxyType.SOCKS4:
            type = "socks4"
        elif type == python_socks.ProxyType.SOCKS5:
            type = "socks5"
        else:
            return None
        try:
            addr, port = proxy_dict.get("addr"), proxy_dict.get("port")
            auth = proxy_dict.get("username")
            if auth:
                username, password = proxy_dict.get("username"), proxy_dict.get("password")
                auth = f"{username}{password}@"
            proxy = {"http": f"{type}://{auth}{addr}:{port}", "https": f"{type}://{auth}{addr}:{port}"}
            new_ip = get("https://ipinfo.io/ip", proxies=proxy, timeout=10).text
            if new_ip != default_ip:
                return proxy_dict
        except Exception as e:
            logging.error(f"Error getting proxy: {e}")
            return None


async def checkValidTelegramClient(client: TelegramClient, close: bool = True):
    """Check if a Telegram client is valid."""
    try:
        me = await client.get_me()
        assert me and me.phone
        return me
    except Exception as e:
        logging.error(f"Invalid Telegram client: {e}")
        return False


def progress_create(total: int, text: str):
    """Create a progress bar."""
    progress = Progress(
        TextColumn("[progress.description]{task.description}"), BarColumn(), MofNCompleteColumn("/")
    )
    task = progress.add_task(text, total=total)
    return progress, task


def update_progress(task, progress: Progress, add: int = 1):
    """Update progress bar."""
    progress.update(task, advance=add)