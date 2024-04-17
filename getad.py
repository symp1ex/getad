#0.2.3-b
import json
import os

def file_exists_in_root(filename):
    root_path = os.path.join(os.getcwd(), filename)  # Получаем путь к файлу в корне
    return os.path.isfile(root_path)  # Возвращает True, если файл существует, иначе False

def read_config_json(json_file):
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def create_date_file(date_json, file_name):
    folder_name = "date"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    file_path = os.path.join(folder_name, f"{file_name}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(date_json, file, ensure_ascii=False, indent=4)
        print(f"Данные сохранены в файле {file_path}")


def status_connect(fptr):
    isOpened = fptr.isOpened()  # спрашиваем состояние подключения
    if isOpened == 1:
        print(f"Соединение с ККТ установлено")
        return isOpened
    elif isOpened == 0:
        print(f"Соединение с ККТ разорвано")
        return isOpened


def connect_kkt(fptr, IFptr):
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

    if settings:
        settings_str = json.dumps(settings)
        fptr.setSettings(settings_str)
    fptr.applySingleSettings()

    fptr.open()  # подключаемся к ККТ


def get_date_kkt(fptr, IFptr):
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
    attribute_podakciz = fptr.getParamBool(1207)
    try:
        attribute_marked = fptr.getParamBool(IFptr.LIBFPTR_PARAM_TRADE_MARKED_PRODUCTS)
    except Exception as e:
        attribute_marked = "Не поддерживается в текущей версии драйвера"

    # запрос общей инфы из ФН
    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
    fptr.fnQueryData()

    fn_serial = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
    try:
        fnExecution = fptr.getParamString(IFptr.LIBFPTR_PARAM_FN_EXECUTION)
        # Используйте значение fn_execution здесь
    except Exception as e:
        # Обработка случая, когда атрибут LIBFPTR_PARAM_FN_EXECUTION отсутствует
        print("Атрибут LIBFPTR_PARAM_FN_EXECUTION отсутствует в этой версии драйвера.")
        fnExecution = "None"

    # функция запроса даты регистрации, если регистрация была первой
    def datetime_reg_check(fptr):
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

    datetime_reg = datetime_reg_check(fptr)

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

    fptr.close()
    status_connect(fptr)
    del fptr

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
        "fnExecution": str(fnExecution),
        "attribute_podakciz": str(attribute_podakciz),
        "attribute_marked": str(attribute_marked)
    }
    create_date_file(date_json, serialNumber)

    print()
    print(str(modelName))
    print(str(serialNumber))
    print(str(RNM))
    print(str(organizationName))
    print(str(fn_serial))
    print(str(datetime_reg))
    print(str(dateTime_end))
    print(str(ofdName))
    print(str(bootVersion))
    print(str(ffdVersion))
    print(str(INN))
    print(str(fnExecution))
    print(str(attribute_podakciz))
    print(str(attribute_marked))


def main():
    try:
        from libfptr108 import IFptr  # подтягиваем библиотеку от 10.8 и проверяем версию
        if file_exists_in_root("fptr10.dll"):
            fptr = IFptr(r".\fptr10.dll")
        else:
            fptr = IFptr("")
        version_byte = fptr.version()
        version = version_byte.decode()
        print(f"Инициализирован драйвер версии {version}")

        parts = version.split('.')
        if len(parts) < 3:
            print("Некорректный формат версии")
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

    connect_kkt(fptr, IFptr)  # подключаемся к ККТ

    isOpened = status_connect(fptr)  # првоверяем статус подключения к ККТ
    if isOpened == 1:
        get_date_kkt(fptr, IFptr)  # получаем и сохраняем данные
    elif isOpened == 0:
        del fptr


if __name__ == "__main__":
    main()
