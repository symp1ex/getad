import xml.etree.ElementTree as ET
import os
import winreg
#import ctypes
import socket
from comautodetect import exception_handler, log_console_out


def get_server_url():
    try:
        xml_path = os.path.join(os.getenv('APPDATA'), 'iiko', 'Cashserver', 'config.xml')

        # Загрузка XML-файла
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Находим элемент <serverUrl>
        server_url_element = root.find('serverUrl')

        # Получаем текст из элемента <serverUrl>
        return server_url_element.text
    except FileNotFoundError:
        log_console_out("Error: файл 'cashserver/config.xml' не найден.")
    except Exception as e:
        log_console_out(f"Error:Произошла ошибка при чтении файла 'cashserver/config.xml'")
        exception_handler(type(e), e, e.__traceback__)


def get_teamviewer_id():
    try:
        # Проверяем раздел реестра для 64-битных приложений
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\TeamViewer", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            value, _ = winreg.QueryValueEx(key, "ClientID")
            if value:
                return value
    except FileNotFoundError:
        pass  # Продолжаем проверку в другом разделе
    except Exception as e:
        log_console_out(f"Error:Произошла ошибка при чтении реестра")
        exception_handler(type(e), e, e.__traceback__)

    try:
        # Если значение не найдено в разделе для 64-битных приложений,
        # проверяем раздел реестра для 32-битных приложений
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\TeamViewer", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
            value, _ = winreg.QueryValueEx(key, "ClientID")
            if value:
                return value
    except FileNotFoundError:
        log_console_out('Реестровый ключ "ClientID" для TeamViewer не найден.')
    except Exception as e:
        log_console_out(f"Произошла ошибка при чтении реестра")
        exception_handler(type(e), e, e.__traceback__)

def get_litemanager_id():
    try:
        def search_key_recursively_64(key, subkey): #функция для рекурсивного перебора ключей во вложенных папках
            try:
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as current_key:
                    try:
                        value, _ = winreg.QueryValueEx(current_key, "ID (read only)")
                        return value
                    except FileNotFoundError:
                        pass

                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(current_key, i)
                            result = search_key_recursively_64(current_key, subkey_name)
                            if result:
                                return result
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                return None

        root_key = winreg.HKEY_LOCAL_MACHINE
        base_subkey = "SOFTWARE\\LiteManager"

        return search_key_recursively_64(root_key, base_subkey)

        id_value = get_litemanager_id()
        if id_value:
            return id_value
        else:
            return None
    except FileNotFoundError:
        log_console_out('Реестровый ключ "ID (read only)" для LiteManager не найден.')
    except Exception as e:
        log_console_out(f"Error:Произошла ошибка при чтении реестра")
        exception_handler(type(e), e, e.__traceback__)

def get_anydesk_id():
    try:
        conf_path = os.path.join(os.getenv('APPDATA'), 'anydesk', 'system.conf')
        with open(conf_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("ad.anynet.id"):
                    ad_anynet_id = line.split("=")[1].strip()
                    return ad_anynet_id
        log_console_out("Параметр 'ad.anynet.id' не найден в system.conf.")
        return None
    except FileNotFoundError:
        log_console_out("Файл system.conf не найден.")
    except Exception as e:
        log_console_out(f'Error: ошибка при получении anydesk_id')
        exception_handler(type(e), e, e.__traceback__)


# def get_disk_info(drive):
#     try:
#         free_bytes = ctypes.c_ulonglong(0)
#         total_bytes = ctypes.c_ulonglong(0)
#         ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(drive), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
#         total_space_gb = total_bytes.value / (1024 ** 3)  # Общий объем в гигабайтах
#         free_space_gb = free_bytes.value / (1024 ** 3)    # Свободное место в гигабайтах
#
#         # Ограничиваем количество знаков после запятой до 3
#         total_space_gb = "{:.2f}".format(total_space_gb)
#         free_space_gb = "{:.2f}".format(free_space_gb)
#
#         return total_space_gb, free_space_gb
#     except Exception as e:
#         log_console_out(f"Error: Не удалось получить информацию о диске")
#         exception_handler(type(e), e, e.__traceback__)

def get_hostname():
    try:
        hostname = socket.gethostname()
        return hostname
    except Exception as e:
        hostname = "hostname"
        log_console_out(f"Error: Не удалось получить имя хоста")
        exception_handler(type(e), e, e.__traceback__)
        return hostname