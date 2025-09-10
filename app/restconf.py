import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils.exceptions import RESTCONFError, BadRequestError, NotFoundError
from .utils.utils import parse_resource_path, create_error_response


class RESTCONFHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для RESTCONF запросов"""

    def __init__(self, yang_manager, rpc_handler, *args, **kwargs):
        self.yang_manager = yang_manager
        self.rpc_handler = rpc_handler
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Обрабатывает GET запросы"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            # Обрабатываем различные типы GET запросов
            if path == "/.well-known/host-meta":
                self._handle_host_meta()
            elif path == "/restconf":
                self._handle_restconf_root()
            elif path == "/restconf/data":
                self._handle_get_data("")
            elif path.startswith("/restconf/data/"):
                resource_path = parse_resource_path(path)
                self._handle_get_data(resource_path)
            elif path == "/restconf/operations":
                self._handle_get_operations()
            elif path.startswith("/restconf/operations/"):
                operation_name = path.replace("/restconf/operations/", "")
                self._handle_get_operation(operation_name)
            else:
                self._send_error_response(NotFoundError(
                    error_message=f"Ресурс не найден: {path}"
                ))

        except RESTCONFError as e:
            self._send_error_response(e)
        except Exception as e:
            self._send_error_response(RESTCONFError(
                "protocol", "operation-failed", f"Внутренняя ошибка: {str(e)}", 500
            ))

    def do_PATCH(self):
        """Обрабатывает PATCH запросы"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            if not path.startswith("/restconf/data"):
                self._send_error_response(BadRequestError(
                    error_message="PATCH разрешен только для /restconf/data"
                ))
                return

            # Проверяем Content-Type
            content_type = self.headers.get('Content-Type', '')
            if 'application/yang-data+json' not in content_type:
                self._send_error_response(BadRequestError(
                    error_message="Требуется Content-Type: application/yang-data+json"
                ))
                return

            # Читаем данные из тела запроса
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error_response(BadRequestError(
                    error_message="Тело запроса не может быть пустым"
                ))
                return

            raw_data = self.rfile.read(content_length).decode('utf-8')
            try:
                patch_data = json.loads(raw_data)
            except json.JSONDecodeError:
                self._send_error_response(BadRequestError(
                    error_message="Неверный формат JSON"
                ))
                return

            # Определяем путь к ресурсу
            if path == "/restconf/data":
                resource_path = ""
            else:
                resource_path = parse_resource_path(path)

            # Применяем изменения
            self.yang_manager.update_data(resource_path, patch_data)

            # Отправляем успешный ответ
            self.send_response(204)  # No Content
            self.end_headers()

        except RESTCONFError as e:
            self._send_error_response(e)
        except Exception as e:
            self._send_error_response(RESTCONFError(
                "protocol", "operation-failed", f"Ошибка обработки PATCH: {str(e)}", 500
            ))

    def do_POST(self):
        """Обрабатывает POST запросы (RPC операции)"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            if not path.startswith("/restconf/operations/"):
                self._send_error_response(BadRequestError(
                    error_message="POST разрешен только для /restconf/operations/"
                ))
                return

            operation_name = path.replace("/restconf/operations/", "")

            # Читаем входные данные
            content_length = int(self.headers.get('Content-Length', 0))
            input_data = None

            if content_length > 0:
                raw_data = self.rfile.read(content_length).decode('utf-8')
                try:
                    input_data = json.loads(raw_data)
                    # Извлекаем данные из input контейнера если есть
                    if 'input' in input_data:
                        input_data = input_data['input']
                except json.JSONDecodeError:
                    self._send_error_response(BadRequestError(
                        error_message="Неверный формат JSON"
                    ))
                    return

            # Вызываем RPC операцию
            result = self.rpc_handler.handle_rpc(operation_name, input_data)

            # Отправляем результат
            self._send_json_response(result, 200)

        except RESTCONFError as e:
            self._send_error_response(e)
        except Exception as e:
            self._send_error_response(RESTCONFError(
                "protocol", "operation-failed", f"Ошибка выполнения RPC: {str(e)}", 500
            ))

    def _handle_host_meta(self):
        """Обрабатывает запрос к /.well-known/host-meta"""
        # Формируем XML ответ для host-meta
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>'
        xml_content += '<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">'
        xml_content += '<Link rel="restconf" href="/restconf"/>'
        xml_content += '</XRD>'

        self.send_response(200)
        self.send_header('Content-Type', 'application/xrd+xml')
        self.send_header('Content-Length', str(len(xml_content)))
        self.end_headers()
        self.wfile.write(xml_content.encode('utf-8'))

    def _handle_restconf_root(self):
        """Обрабатывает запрос к корневому ресурсу RESTCONF"""
        response = {
            "ietf-restconf:restconf": {
                "data": {},
                "operations": {},
                "yang-library-version": "2016-06-21"
            }
        }
        self._send_json_response(response)

    def _handle_get_data(self, resource_path):
        """Обрабатывает получение данных"""
        data = self.yang_manager.get_data(resource_path)

        if data is None:
            self._send_error_response(NotFoundError(
                error_message=f"Данные по пути '{resource_path}' не найдены"
            ))
        else:
            self._send_json_response(data)

    def _handle_get_operations(self):
        """Обрабатывает получение списка операций"""
        operations = self.rpc_handler.get_available_operations()
        self._send_json_response(operations)

    def _handle_get_operation(self, operation_name):
        """Обрабатывает получение информации об операции"""
        # Возвращаем пустой лист для указания что операция доступна
        self._send_json_response(None)

    def _send_json_response(self, data, status=200):
        """Отправляет JSON ответ"""
        json_response = json.dumps(data, indent=2, ensure_ascii=False)

        self.send_response(status)
        self.send_header('Content-Type', 'application/yang-data+json')
        self.send_header('Content-Length', str(len(json_response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_response.encode('utf-8'))

    def _send_error_response(self, error):
        """Отправляет ответ с ошибкой"""
        error_response = create_error_response(error)
        json_response = json.dumps(error_response, indent=2, ensure_ascii=False)

        self.send_response(error.status_code)
        self.send_header('Content-Type', 'application/yang-data+json') 
        self.send_header('Content-Length', str(len(json_response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_response.encode('utf-8'))

    def log_message(self, format, *args):
        """Логирование запросов"""
        print(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}")


def create_restconf_handler(yang_manager, rpc_handler):
    """Фабричная функция для создания обработчика с зависимостями"""
    def handler(*args, **kwargs):
        return RESTCONFHandler(yang_manager, rpc_handler, *args, **kwargs)
    return handler
