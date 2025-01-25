import os
import shutil
import subprocess
import psutil
import time
import pylnk3

def move_files(src, dst):
    """Move all files from src directory to dst directory."""
    for filename in os.listdir(src):
        src_file = os.path.join(src, filename)
        dst_file = os.path.join(dst, filename)
        shutil.move(src_file, dst_file)

def clear_directory(directory):
    """Delete all files and subdirectories in the specified directory."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def close_telegram():
    """Terminate all running Telegram processes."""
    for proc in psutil.process_iter():
        try:
            if "telegram" in proc.name().lower():
                proc.terminate()
                proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def find_telegram():
    """Find the Telegram executable from a shortcut on the desktop."""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    for item in os.listdir(desktop_path):
        item_path = os.path.join(desktop_path, item)
        if item.lower().endswith('.lnk') and 'telegram' in item.lower():
            try:
                lnk = pylnk3.parse(item_path)
                exe_path = lnk.path
                if os.path.exists(exe_path):
                    return exe_path
            except Exception as e:
                print(f"Не удалось обработать запрос: {e}")

    print("Telegram не найден на рабочем столе.")
    return None

def main():
    """Main function to manage Telegram tdata accounts."""
    src_folder = input("Укажите путь до папки с tdata аккаунтами: ")

    if not os.path.isdir(src_folder):
        print(f"Указанная папка не найдена: {src_folder}")
        return

    telegram_exe = find_telegram()
    if not telegram_exe or not os.path.exists(telegram_exe):
        print("Пожалуйста, укажите путь к Telegram вручную.")
        telegram_exe = input("Укажите путь до папки с telegram.exe для запуска tdata: ")
        if not os.path.exists(telegram_exe):
            print(f"Исполняемый файл не найден: {telegram_exe}")
            return

    telegram_tdata = os.path.join(os.path.dirname(telegram_exe), 'tdata')

    for account_folder in os.listdir(src_folder):
        account_path = os.path.join(src_folder, account_folder)
        if not os.path.isdir(account_path):
            continue

        close_telegram()
        time.sleep(2)  # время ожидания между чеками
        clear_directory(telegram_tdata)
        move_files(account_path, telegram_tdata)

        subprocess.Popen([telegram_exe])
        is_valid = input("Выберите действие (1 - Valid, 2 - Error): ")

        if is_valid == "1":
            close_telegram()
            move_files(telegram_tdata, account_path)
            print(f"{account_folder}: valid")
        else:
            close_telegram()
            clear_directory(telegram_tdata)
            shutil.rmtree(account_path)
            print(f"{account_folder}: deleted")

if __name__ == "__main__":
    main()