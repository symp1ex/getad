import xml.etree.ElementTree as ET
import os
import winreg
from comautodetect import log_with_timestamp


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
        log_with_timestamp("Файл config.xml не найден.")
    except Exception:
        None


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
        log_with_timestamp(f"Произошла ошибка при чтении реестра: {e}")

    try:
        # Если значение не найдено в разделе для 64-битных приложений,
        # проверяем раздел реестра для 32-битных приложений
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\TeamViewer", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
            value, _ = winreg.QueryValueEx(key, "ClientID")
            if value:
                return value
    except FileNotFoundError:
        log_with_timestamp('Реестровый ключ "ClientID" для TeamViewer не найден.')
    except Exception as e:
        log_with_timestamp(f"Произошла ошибка при чтении реестра: {e}")


def get_anydesk_id():
    try:
        conf_path = os.path.join(os.getenv('APPDATA'), 'anydesk', 'system.conf')
        with open(conf_path, 'r') as file:
            for line in file:
                if line.startswith("ad.anynet.id"):
                    ad_anynet_id = line.split("=")[1].strip()
                    return ad_anynet_id
        log_with_timestamp("Параметр 'ad.anynet.id' не найден в system.conf.")
        return None
    except FileNotFoundError:
        log_with_timestamp("Файл system.conf не найден.")
    except Exception as e:
        log_with_timestamp(e)