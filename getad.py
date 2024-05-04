#0.4.8.5
import json
import os, sys
import subprocess
from comautodetect import get_atol_port_dict, log_with_timestamp, current_time
from get_remote import get_server_url, get_teamviewer_id, get_anydesk_id, get_disk_info, get_hostname

def file_exists_in_root(filename):
    try:
        root_path = os.path.join(os.getcwd(), filename)  # Получаем путь к файлу в корне
        return os.path.isfile(root_path)  # Возвращает True, если файл существует, иначе False
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def read_config_json(json_file):
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def create_config_file(config, file_path="config.json"):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def create_new_config():
    try:
        config_data = {
            "type_connect": 3,
            "com_port": "COM4",
            "com_baudrate": "115200",
            "ip": "10.25.1.22",
            "ip_port": "5555"
        }
        create_config_file(config_data)
        log_with_timestamp("Создан новый config.json")
    except Exception as e:
        log_with_timestamp(f"Не удалось создать конфиг файл: {e}")

def create_date_file(date_json, file_name, folder_name):
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        file_path = os.path.join(folder_name, f"{file_name}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(date_json, file, ensure_ascii=False, indent=4)
            log_with_timestamp(f"Данные сохранены в файле {file_path}")
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def status_connect(fptr, port):
    try:
        isOpened = fptr.isOpened()  # спрашиваем состояние подключения
        if isOpened == 1:
            log_with_timestamp(f"Соединение с ККТ установлено ({port})")
            return isOpened
        elif isOpened == 0:
            log_with_timestamp(f"Соединение с ККТ разорвано ({port})")
            return isOpened
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def checkstatus_getdate(fptr, IFptr, port):
    try:
        isOpened = status_connect(fptr, port)  # првоверяем статус подключения к ККТ
        if isOpened == 1:
            get_date_kkt(fptr, IFptr, port)  # получаем и сохраняем данные
        elif isOpened == 0:
            del fptr
            return isOpened
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def connect_kkt(fptr, IFptr):
    try:
        json_file = os.path.join(os.getcwd(), "config.json")
        config = read_config_json(json_file) or {}  # если нет конфигурации, используем пустой словарь

        settings_map = {
            1: {
                IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
                IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
                IFptr.LIBFPTR_SETTING_COM_FILE: config.get("com_port"),
                IFptr.LIBFPTR_SETTING_BAUDRATE: getattr(IFptr,
                                                        "LIBFPTR_PORT_BR_" + str(config.get("com_baudrate"))) if config.get(
                    "com_baudrate") else None
            },
            2: {
                IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
                IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
                IFptr.LIBFPTR_SETTING_IPADDRESS: config.get("ip"),
                IFptr.LIBFPTR_SETTING_IPPORT: config.get("ip_port")
            }
        }

        settings = settings_map.get(config.get("type_connect"), {})  # Получаем настройки по типу подключения
        if not settings:  # Если тип подключения не определен в конфигурации
            settings = {
                IFptr.LIBFPTR_SETTING_MODEL: str(IFptr.LIBFPTR_MODEL_ATOL_AUTO),
                IFptr.LIBFPTR_SETTING_PORT: str(IFptr.LIBFPTR_PORT_USB)
            }
            fptr.applySingleSettings()
            fptr.open()  # подключаемся к ККТ
            return "USB"

        if settings:
            settings_str = json.dumps(settings)
            fptr.setSettings(settings_str)
            fptr.applySingleSettings()
            fptr.open()  # подключаемся к ККТ

            ip_with_port = f"{config.get('ip')}:{config.get('ip_port')}"
            return settings.get(IFptr.LIBFPTR_SETTING_COM_FILE, None) or ip_with_port
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def get_date_kkt(fptr, IFptr, port):
    try:
        # общая инфа об ФР
        fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        fptr.queryData()

        modelName = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)  # название модели
        serialNumber = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)  # серийник ФР

        # запрос регистрационных данных
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
        fptr.fnQueryData()

        RNM = fptr.getParamString(1037)
        ofdName = fptr.getParamString(1046)
        organizationName = fptr.getParamString(1048)
        INN = fptr.getParamString(1018)
        attribute_excise = fptr.getParamBool(1207)
        attribute_marked = fptr.getParamBool(IFptr.LIBFPTR_PARAM_TRADE_MARKED_PRODUCTS)
    except Exception as e:
        log_with_timestamp(f"Error: {e}")
        attribute_marked = "Не поддерживается в текущей версии драйвера"

    # запрос общей инфы из ФН
    try:
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
        fptr.fnQueryData()

        fn_serial = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        fnExecution = fptr.getParamString(IFptr.LIBFPTR_PARAM_FN_EXECUTION)
        # Используйте значение fn_execution здесь
    except Exception as e:
        # Обработка случая, когда атрибут LIBFPTR_PARAM_FN_EXECUTION отсутствует
        log_with_timestamp(f"Error: {e}")
        fnExecution = "Не поддерживается в текущей версии драйвера"

    # функция запроса даты регистрации, если регистрация была первой
    def datetime_reg_check(fptr):
        try:
            fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_REGISTRATION)
            fptr.fnQueryData()
            registrationsCount = fptr.getParamInt(IFptr.LIBFPTR_PARAM_REGISTRATIONS_COUNT)
            if registrationsCount == 1:
                dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
                return dateTime
            else:
                fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE,
                              IFptr.LIBFPTR_FNDT_DOCUMENT_BY_NUMBER)  # запрос информациия о фд 1
                fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, 1)
                fptr.fnQueryData()
                dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
                return dateTime
        except Exception as e:
            log_with_timestamp(f"Error: {e}")

    datetime_reg = datetime_reg_check(fptr)

    try:
        # запрос даты окончания ФН
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_VALIDITY)
        fptr.fnQueryData()

        dateTime_end = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

        # версия загрузчика
        fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
        fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, IFptr.LIBFPTR_UT_BOOT)
        fptr.queryData()
        bootVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)

        # запрос версии ФФД
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FFD_VERSIONS)
        fptr.fnQueryData()

        ffdVersion = fptr.getParamInt(IFptr.LIBFPTR_PARAM_FFD_VERSION)

        log_with_timestamp(f"Данные от ККТ получены")

        fptr.close()
        status_connect(fptr, port)
        del fptr

        hostname, url_rms, teamviever_id, anydesk_id, total_space_gb, free_space_gb = get_remote()
        get_current_time = current_time()

        date_json = {
            "modelName": str(modelName),
            "serialNumber": str(serialNumber),
            "RNM": str(RNM),
            "organizationName": str(organizationName),
            "fn_serial": str(fn_serial),
            "datetime_reg": str(datetime_reg),
            "dateTime_end": str(dateTime_end),
            "ofdName": str(ofdName),
            "bootVersion": str(bootVersion),
            "ffdVersion": str(ffdVersion),
            "INN": str(INN),
            "attribute_excise": str(attribute_excise),
            "attribute_marked": str(attribute_marked),
            "fnExecution": str(fnExecution),
            "hostname": str(hostname),
            "url_rms": str(url_rms),
            "teamviever_id": str(teamviever_id),
            "anydesk_id": str(anydesk_id),
            "total_space_sys": str(f"{total_space_gb} Gb"),
            "free_space_sys": str(f"{free_space_gb} Gb"),
            "current_time": str(get_current_time)
        }
        folder_name = "date"
        create_date_file(date_json, serialNumber, folder_name)
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def get_date_non_kkt():
    hostname, url_rms, teamviever_id, anydesk_id, total_space_gb, free_space_gb = get_remote()
    get_current_time = current_time()

    date_json = {
        "hostname": str(hostname),
        "url_rms": str(url_rms),
        "teamviever_id": str(teamviever_id),
        "anydesk_id": str(anydesk_id),
        "total_space_sys": str(f"{total_space_gb} Gb"),
        "free_space_sys": str(f"{free_space_gb} Gb"),
        "current_time": str(get_current_time)
    }
    folder_name = "date"
    json_name = f"TV{teamviever_id}_AD{anydesk_id}"
    create_date_file(date_json, json_name, folder_name)

def get_remote():
    try:
        hostname = get_hostname()
        url_rms = get_server_url()
        teamviever_id = get_teamviewer_id()
        anydesk_id = get_anydesk_id()

        drive = 'C:\\'
        total_space_gb, free_space_gb = get_disk_info(drive)
        return hostname, url_rms, teamviever_id, anydesk_id, total_space_gb, free_space_gb
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

def main():
    try:
        from libfptr108 import IFptr  # подтягиваем библиотеку от 10.8 и проверяем версию
        if file_exists_in_root("fptr10.dll"):
            fptr = IFptr(r".\fptr10.dll")
        else:
            fptr = IFptr("")
        version_byte = fptr.version()
        version = version_byte.decode()
        log_with_timestamp(f"Инициализирован драйвер версии {version}")

        parts = version.split('.')
        if len(parts) < 3:
            log_with_timestamp("Некорректный формат версии")
            return None

        major, minor, patch, null = map(int, parts)

        if major == 10 and minor >= 9:  # если версия от 10.9.0.0 и выше (поддержка ФФД 1.2) то загружаем библиотеку с поддержкой драйвера вплоть до 10.10
            del fptr
            from libfptr109 import IFptr
            if file_exists_in_root("fptr10.dll"):
                fptr = IFptr(r".\fptr10.dll")
            else:
                fptr = IFptr("")
    except ImportError:
        pass
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

    json_file = os.path.join(os.getcwd(), "config.json")
    config = read_config_json(json_file)

    try:
        if config is not None and not config.get("type_connect") == 0:
            port = connect_kkt(fptr, IFptr) # подключаемся к ККТ
            isOpened = checkstatus_getdate(fptr, IFptr, port)
            if isOpened == 0:
                get_date_non_kkt()
        elif config is not None and config.get("type_connect") == 0:
            port_number_ad = get_atol_port_dict()
            if not port_number_ad:
                get_date_non_kkt()
            elif not port_number_ad == {}:
                log_with_timestamp(f"Найдены порты: {port_number_ad}")
            baud_rate = config.get("com_baudrate")
            for port in port_number_ad.values():
                settings = "{{\"{}\": {}, \"{}\": {}, \"{}\": \"{}\", \"{}\": {}}}".format(
                    IFptr.LIBFPTR_SETTING_MODEL, IFptr.LIBFPTR_MODEL_ATOL_AUTO,
                    IFptr.LIBFPTR_SETTING_PORT, IFptr.LIBFPTR_PORT_COM,
                    IFptr.LIBFPTR_SETTING_COM_FILE, port,
                    IFptr.LIBFPTR_SETTING_BAUDRATE, getattr(IFptr, "LIBFPTR_PORT_BR_" + str(baud_rate)))
                fptr.setSettings(settings)

                fptr.open()

                checkstatus_getdate(fptr, IFptr, port)
        else:
            log_with_timestamp("config.json имеет некорректный формат данных или отсутствует")
            port = connect_kkt(fptr, IFptr)  # подключаемся к ККТ
            isOpened = checkstatus_getdate(fptr, IFptr, port)
            if isOpened == 0:
                get_date_non_kkt()
            create_new_config()
    except Exception as e:
        log_with_timestamp(f"Error: {e}")

    try:
        exe_path = ".\\updater\\updater.exe"
        main_file = os.path.abspath(sys.argv[0])
        working_directory = os.path.join(os.path.dirname(main_file),
                                         "updater")  # получаем абсолютный путь к основному файлу скрипта sys.argv[0], а затем с помощью os.path.dirname() извлекаем путь к директории, содержащей основной файл
        subprocess.Popen(exe_path, cwd=working_directory)
    except Exception:
        None

if __name__ == "__main__":
    main()