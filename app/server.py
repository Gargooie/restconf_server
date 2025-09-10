from http.server import HTTPServer
from .restconf import create_restconf_handler


class RESTCONFServer:
    """HTTP сервер для обработки RESTCONF запросов"""

    def __init__(self, host, port, yang_manager, rpc_handler):
        self.host = host
        self.port = port
        self.yang_manager = yang_manager
        self.rpc_handler = rpc_handler
        self.httpd = None

    def start(self):
        """Запускает HTTP сервер"""
        try:
            # Создаем обработчик с зависимостями
            handler_class = create_restconf_handler(self.yang_manager, self.rpc_handler)

            # Создаем HTTP сервер
            self.httpd = HTTPServer((self.host, self.port), handler_class)

            print(f"RESTCONF сервер запущен на {self.host}:{self.port}")
            print(f"Доступ к API: http://{self.host}:{self.port}/restconf")
            print("Для остановки нажмите Ctrl+C")

            # Запускаем сервер
            self.httpd.serve_forever()

        except KeyboardInterrupt:
            print("\nОстанавливаем сервер...")
            self.stop()
        except Exception as e:
            print(f"Ошибка запуска сервера: {e}")
            raise

    def stop(self):
        """Останавливает HTTP сервер"""
        if self.httpd:
            self.httpd.shutdown()
            print("Сервер остановлен")
