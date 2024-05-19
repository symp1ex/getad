import serial.tools.list_ports
import sys
import os
import traceback
from datetime import datetime, timedelta

def log_with_timestamp(message):
    try:
        log_folder = 'l'
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        # Получаем текущую дату
        current_date = datetime.now()

        # Определяем дату, старше которой логи будут удаляться
        old_date_limit = current_date - timedelta(days=14)

        # Удаляем логи старше 10 дней
        for file_name in os.listdir(log_folder):
            file_path = os.path.join(log_folder, file_name)
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_creation_time < old_date_limit:
                os.remove(file_path)

        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_folder, f"{timestamp}-getad.log")
        default_stdout = sys.stdout
        sys.stdout = open(log_file, 'a', encoding='utf-8')

        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f")[:-3]+"]"
        print(f"{timestamp} {message}")
        sys.stdout.close()
        sys.stdout = default_stdout
    except:
        pass


def log_console_out(message):
    try:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f")[:-3] + "]"
        print(f"{timestamp} {message}")
        log_with_timestamp(message)
    except:
        pass


def exception_handler(exc_type, exc_value, exc_traceback):
    try:
        error_message = f"ERROR: An exception occurred + \n"
        error_message += ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_with_timestamp(error_message)
        # Вызываем стандартный обработчик исключений для вывода на экран
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    except:
        pass

def get_com_ports():
    try:
        com_ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in com_ports]
    except Exception as e:
        log_console_out(f"Error: Не удалось получить список COM-портов")
        exception_handler(type(e), e, e.__traceback__)

def get_list_atol():
    try:
        com_ports = get_com_ports()
        atol_ports = []
        if com_ports:
            for port, description in com_ports:
                if 'ATOL' in description:
                    atol_ports.append(port)
        else:
            log_with_timestamp("COM-порты не найдены.")
        return atol_ports
    except Exception as e:
        log_console_out(f"Error: Не удалось получить список com-портов c 'ATOL' в названии")
        exception_handler(type(e), e, e.__traceback__)

def get_atol_port_dict():
    try:
        atol_ports = get_list_atol()
        atol_port_dict = {}  # Создаем словарь для хранения портов

        for i, port in enumerate(atol_ports, start=1):
            atol_port_dict[f"port{i}"] = port
        return atol_port_dict
    except Exception as e:
        log_console_out(f"Error: Не удалось создать словарь со списком com-портов")
        exception_handler(type(e), e, e.__traceback__)

def current_time():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return timestamp
    except Exception as e:
        log_console_out(f"Error: Не удалось получить текущее время")
        exception_handler(type(e), e, e.__traceback__)
