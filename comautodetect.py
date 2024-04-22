import serial.tools.list_ports
import sys
from datetime import datetime

sys.stdout = open('main.log', 'a')

def log_with_timestamp(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{timestamp} {message}")

def get_com_ports():
    com_ports = serial.tools.list_ports.comports()
    return [(port.device, port.description) for port in com_ports]

def get_list_atol():
    com_ports = get_com_ports()
    atol_ports = []
    if com_ports:
        for port, description in com_ports:
            if 'ATOL' in description:
                atol_ports.append(port)
    else:
        log_with_timestamp("COM-порты не найдены.")
    return atol_ports

def get_atol_port_dict():
    atol_ports = get_list_atol()
    atol_port_dict = {}  # Создаем словарь для хранения портов

    for i, port in enumerate(atol_ports, start=1):
        atol_port_dict[f"port{i}"] = port
    return atol_port_dict