import serial.tools.list_ports
import sys
import os
from datetime import datetime, timedelta

def log_with_timestamp(message):
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
    sys.stdout = open(log_file, 'a')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{timestamp} {message}")

def get_com_ports():
    try:
        com_ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in com_ports]
    except Exception as e:
        log_with_timestamp(f'Error: {e}')

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
        log_with_timestamp(f'Error: {e}')

def get_atol_port_dict():
    try:
        atol_ports = get_list_atol()
        atol_port_dict = {}  # Создаем словарь для хранения портов

        for i, port in enumerate(atol_ports, start=1):
            atol_port_dict[f"port{i}"] = port
        return atol_port_dict
    except Exception as e:
        log_with_timestamp(f'Error: {e}')