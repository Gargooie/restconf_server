#!/usr/bin/env python3

import os
import sys
from app import YANGManager, RPCHandler, RESTCONFServer
from app.utils import load_config


def main():
    """Основная функция запуска сервера"""
    try:
        # Загружаем конфигурацию
        config_file = "config/config.yaml"
        if len(sys.argv) > 1:
            config_file = sys.argv[1]

        config = load_config(config_file)
        print(f"Загружена конфигурация из: {config_file}")

        # Инициализируем YANG Manager
        yang_manager = YANGManager(
            library_file=config['yang']['library_file'],
            modules_dirs=config['yang']['modules_dir'], 
            data_file=config['datastore']['data_file']
        )

        # Инициализируем RPC Handler
        rpc_handler = RPCHandler(yang_manager)

        # Создаем и запускаем сервер
        server = RESTCONFServer(
            host=config['server']['host'],
            port=config['server']['port'],
            yang_manager=yang_manager,
            rpc_handler=rpc_handler
        )

        server.start()

    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания")
        sys.exit(0)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
