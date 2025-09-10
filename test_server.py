#!/usr/bin/env python3
import requests
import json
import time
import sys

# Базовый URL сервера
BASE_URL = "http://localhost:8080"

def test_server_running():
    """Проверяет, запущен ли сервер"""
    try:
        response = requests.get(f"{BASE_URL}/.well-known/host-meta", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_get_root():
    """Тестирует получение корня API"""
    print("\n=== Тест: GET /restconf ===")
    try:
        response = requests.get(f"{BASE_URL}/restconf", 
                              headers={"Accept": "application/yang-data+json"})
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("Ответ:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def test_get_all_data():
    """Тестирует получение всех данных"""
    print("\n=== Тест: GET /restconf/data ===")
    try:
        response = requests.get(f"{BASE_URL}/restconf/data",
                              headers={"Accept": "application/yang-data+json"})
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("Данные получены успешно")
            data = response.json()
            print("Ключи верхнего уровня:", list(data.keys()))
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def test_get_library():
    """Тестирует получение данных библиотеки"""
    print("\n=== Тест: GET library ===")
    try:
        response = requests.get(f"{BASE_URL}/restconf/data/example-jukebox:jukebox/library",
                              headers={"Accept": "application/yang-data+json"})
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Исполнителей в библиотеке: {len(data.get('artist', []))}")
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def test_patch_player():
    """Тестирует обновление настроек плеера"""
    print("\n=== Тест: PATCH player settings ===")
    try:
        patch_data = {"gap": "1.5"}
        response = requests.patch(f"{BASE_URL}/restconf/data/example-jukebox:jukebox/player",
                                json=patch_data,
                                headers={
                                    "Content-Type": "application/yang-data+json",
                                    "Accept": "application/yang-data+json"
                                })
        print(f"Статус: {response.status_code}")
        if response.status_code in [200, 204]:
            print("Настройки плеера обновлены успешно")
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def test_rpc_play():
    """Тестирует RPC операцию play"""
    print("\n=== Тест: POST RPC play ===")
    try:
        rpc_data = {
            "input": {
                "playlist": "Favorites", 
                "song-number": 1
            }
        }
        response = requests.post(f"{BASE_URL}/restconf/operations/example-jukebox:play",
                               json=rpc_data,
                               headers={
                                   "Content-Type": "application/yang-data+json",
                                   "Accept": "application/yang-data+json"
                               })
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Результат RPC:", json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def test_get_operations():
    """Тестирует получение списка операций"""
    print("\n=== Тест: GET /restconf/operations ===")
    try:
        response = requests.get(f"{BASE_URL}/restconf/operations",
                              headers={"Accept": "application/yang-data+json"})
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            operations = response.json()
            print("Доступные операции:", json.dumps(operations, indent=2, ensure_ascii=False))
        else:
            print("Ошибка:", response.text)
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def main():
    print("🎵 Тестирование RESTCONF Jukebox сервера")
    print("=" * 50)

    # Проверяем, запущен ли сервер
    if not test_server_running():
        print(" Сервер не запущен!")
        print("Запустите сервер командой: python3 main.py")
        sys.exit(1)

    print(" Сервер запущен и отвечает на запросы")

    # Запускаем тесты
    test_get_root()
    test_get_all_data()
    test_get_library()
    test_get_operations()
    test_patch_player()
    test_rpc_play()

    print("\n" + "=" * 50)
    print(" Тестирование завершено!")

if __name__ == "__main__":
    main()
