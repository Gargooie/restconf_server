import json
import yaml
from urllib.parse import unquote


def load_config(config_file):
    """Загружает конфигурацию из YAML файла"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Возвращаем конфиг по умолчанию
        return {
            'server': {'host': 'localhost', 'port': 8080},
            'datastore': {'data_file': 'data/initial_data.json'},
            'yang': {'modules_dir': 'yang_modules', 'library_file': 'library.json'}
        }


def parse_resource_path(path):
    """Парсит путь к ресурсу RESTCONF"""
    # Убираем /restconf/data/ из начала
    if path.startswith('/restconf/data/'):
        path = path[15:]  # убираем префикс
    elif path.startswith('/restconf/data'):
        path = path[14:]

    # Декодируем URL
    path = unquote(path)

    return path


def create_error_response(error):
    """Создает ответ с ошибкой в формате RESTCONF"""
    return {
        "ietf-restconf:errors": {
            "error": [
                {
                    "error-type": error.error_type,
                    "error-tag": error.error_tag, 
                    "error-message": error.error_message
                }
            ]
        }
    }


def save_json_file(data, filename):
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json_file(filename):
    """Загружает данные из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
