# Минималистичный YANG/RESTCONF сервер на Python

Реализация минималистичного RESTCONF сервера на Python с использованием библиотеки yangson для работы с YANG моделями

## Описание

Этот проект реализует HTTP-сервер, который:
- Загружает и парсит YANG модели с помощью библиотеки yangson
- Хранит конфигурационные данные в памяти с валидацией по схеме
- Обслуживает HTTP-запросы по протоколу RESTCONF (RFC 8040)
- Предоставляет endpoint для вызова RPC операций
- Поддерживает формат данных JSON

## Функциональность

### Поддерживаемые операции:
- **GET /restconf/data/<path>** - чтение данных по пути
- **PATCH /restconf/data/<path>** - обновление данных (merge операция)
- **POST /restconf/operations/<rpc-name>** - вызов RPC операций

### Дополнительные возможности:
- Валидация данных согласно YANG схеме при загрузке и изменении
- Поддержка заголовков Accept и Content-Type (application/yang-data+json)
- Обработка ошибок в формате RESTCONF
- Автоматическое сохранение изменений в файл

## Установка и запуск

### 1. Установка зависимостей

# Установить зависимости
pip install -r requirements.txt


### 2. Запуск сервера

python3 main.py


Сервер по умолчанию запустится на `http://localhost:8080`

### 3. Проверка работы

- `http://localhost:8080/.well-known/host-meta` - обнаружение корня API
- `http://localhost:8080/restconf` - корневой ресурс RESTCONF
- `http://localhost:8080/restconf/data` - все данные

## Примеры использования

### GET - Получение данных

# Получить все данные
curl -H "Accept: application/yang-data+json" \
     http://localhost:8080/restconf/data

# Получить данные библиотеки
curl -H "Accept: application/yang-data+json" \
     http://localhost:8080/restconf/data/example-jukebox:jukebox/library

# Получить конкретного исполнителя
curl -H "Accept: application/yang-data+json" \
     http://localhost:8080/restconf/data/example-jukebox:jukebox/library/artist=The%20Beatles


### PATCH - Обновление данных


# Добавить новую песню в альбом
curl -X PATCH \
     -H "Content-Type: application/yang-data+json" \
     -H "Accept: application/yang-data+json" \
     -d '{
       "song": [
         {
           "name": "Here Comes The Sun",
           "location": "/music/beatles/abbey_road/here_comes_the_sun.mp3",
           "format": "MP3",
           "length": 185
         }
       ]
     }' \
     http://localhost:8080/restconf/data/example-jukebox:jukebox/library/artist=The%20Beatles/album=Abbey%20Road

# Обновить настройки плеера
curl -X PATCH \
     -H "Content-Type: application/yang-data+json" \
     -d '{
       "gap": 1.5
     }' \
     http://localhost:8080/restconf/data/example-jukebox:jukebox/player


### POST - Вызов RPC операций


# Вызвать RPC операцию "play"
curl -X POST \
     -H "Content-Type: application/yang-data+json" \
     -H "Accept: application/yang-data+json" \
     -d '{
       "input": {
         "playlist": "Favorites",
         "song-number": 1
       }
     }' \
     http://localhost:8080/restconf/operations/example-jukebox:play

# Получить список доступных операций
curl -H "Accept: application/yang-data+json" \
     http://localhost:8080/restconf/operations

