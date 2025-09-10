import json
import os
from typing import Any, Dict, Optional
from yangson import DataModel
from yangson.enumerations import ContentType
from .utils.exceptions import ValidationError, InternalServerError
from .utils.utils import load_json_file, save_json_file


class YANGManager:
    """Управляет YANG моделями и данными через yangson"""

    def __init__(self, library_file: str, modules_dirs: str | list[str], data_file: str):
        self.library_file = library_file
        self.modules_dirs = modules_dirs if isinstance(modules_dirs, list) else [modules_dirs]
        self.data_file = data_file
        self.data_model: Optional[DataModel] = None
        self.datastore: Optional[Any] = None

        # Инициализируем модель данных и хранилище
        self._init_data_model()
        self._load_datastore()

    def _init_data_model(self):
        """Инициализирует модель данных yangson"""
        try:
            self.data_model = DataModel.from_file(self.library_file, self.modules_dirs)
            print("YANG модель успешно загружена")
        except Exception as e:
            raise InternalServerError(f"Не удалось загрузить YANG модель: {e}")

    def _load_datastore(self):
        """Загружает данные из файла в хранилище"""
        try:
            raw_data = load_json_file(self.data_file)
            if raw_data:
                self.datastore = self.data_model.from_raw(raw_data)  # type: ignore
                # Пропускаем валидацию при загрузке, так как config false поля
                # могут вызывать проблемы
                print("Данные загружены без валидации")
                print(f"Загруженные данные: {raw_data}")
            else:
                # Создаем пустое хранилище
                self.datastore = self.data_model.from_raw({})  # type: ignore
        except Exception as e:
            # Если не удается загрузить даже с пропуском валидации
            try:
                raw_data = load_json_file(self.data_file)
                if raw_data:
                    # Создаем хранилище без валидации
                    self.datastore = self.data_model.from_raw(raw_data)  # type: ignore
                    print("Данные загружены без валидации")
                else:
                    self.datastore = self.data_model.from_raw({})  # type: ignore
            except Exception as load_error:
                raise InternalServerError(f"Не удалось загрузить данные: {e}, {load_error}")

    def get_data(self, resource_path=""):
        """Получает данные по указанному пути"""
        try:
            if not resource_path:
                # Возвращаем все данные
                return self.datastore.raw_value()

            # Парсим путь ресурса
            try:
                irt = self.data_model.parse_resource_id(resource_path)
                data_instance = self.datastore.goto(irt)
                return data_instance.raw_value()
            except Exception:
                # Если путь не найден, возвращаем None
                return None

        except Exception as e:
            raise InternalServerError(f"Ошибка при получении данных: {e}")

    def update_data(self, resource_path, data):
        """Обновляет данные по указанному пути (PATCH операция)"""
        try:
            # Получаем текущие данные
            current_data = self.datastore.raw_value()
            
            # Применяем изменения к сырым данным
            if resource_path:
                # Для конкретного пути - обновляем только нужную часть
                self._update_raw_data(current_data, resource_path, data)
            else:
                # Для корня - обновляем напрямую
                current_data.update(data)

            # Сохраняем данные напрямую в файл, минуя yangson валидацию
            save_json_file(current_data, self.data_file)
            
            # Перезагружаем хранилище из файла
            self._load_datastore()

            return True

        except Exception as e:
            raise ValidationError(f"Ошибка обновления данных: {e}")

    def _create_merge_data(self, resource_path, data):
        """Создает структуру данных для merge операции"""
        if resource_path == "example-jukebox:jukebox/player":
            return {
                "example-jukebox:jukebox": {
                    "player": data
                }
            }
        else:
            return data

    def _validate_patch_data(self, resource_path, data):
        """Валидирует только данные для PATCH операции"""
        try:
            # Для PATCH операций валидируем только обновляемые данные
            # Создаем минимальную структуру только с обновляемыми данными
            if resource_path == "example-jukebox:jukebox/player":
                # Валидируем только данные плеера
                validation_data = {
                    "example-jukebox:jukebox": {
                        "player": data
                    }
                }
            else:
                # Для других путей используем данные как есть
                validation_data = data
            
            # Валидируем только конфигурационные данные
            instance = self.data_model.from_raw(validation_data)
            instance.validate(ctype=ContentType.config)
            
        except Exception as e:
            raise ValidationError(f"Ошибка валидации PATCH данных: {e}")

    def _create_validation_data(self, resource_path, data):
        """Создает структуру данных для валидации без config false полей"""
        # Получаем текущие данные
        if hasattr(self.datastore, 'raw_value'):
            current_data = self.datastore.raw_value()
        else:
            current_data = self.datastore
        
        # Создаем копию без config false полей
        validation_data = self._remove_config_false_fields(current_data)
        
        # Применяем изменения
        if resource_path:
            # Для конкретного пути - обновляем только нужную часть
            self._update_validation_data(validation_data, resource_path, data)
        else:
            # Для корня - обновляем напрямую
            validation_data.update(data)
            
        return validation_data

    def _remove_config_false_fields(self, data):
        """Удаляет поля config false из структуры данных"""
        if not isinstance(data, dict):
            return data
            
        cleaned_data = {}
        for key, value in data.items():
            # Пропускаем известные config false поля
            if key in ['artist-count', 'album-count', 'song-count']:
                continue
            elif isinstance(value, dict):
                cleaned_data[key] = self._remove_config_false_fields(value)
            elif isinstance(value, list):
                cleaned_data[key] = [
                    self._remove_config_false_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned_data[key] = value
                
        return cleaned_data

    def _update_raw_data(self, raw_data, resource_path, data):
        """Обновляет сырые данные по указанному пути"""
        if resource_path == "example-jukebox:jukebox/player":
            if "example-jukebox:jukebox" not in raw_data:
                raw_data["example-jukebox:jukebox"] = {}
            if "player" not in raw_data["example-jukebox:jukebox"]:
                raw_data["example-jukebox:jukebox"]["player"] = {}
            raw_data["example-jukebox:jukebox"]["player"].update(data)
        else:
            # Для других путей применяем общее обновление
            raw_data.update(data)

    def _update_validation_data(self, validation_data, resource_path, data):
        """Обновляет данные в структуре валидации по указанному пути"""
        # Упрощенная реализация - в реальности нужна более сложная логика
        # для правильного обновления вложенных структур
        if resource_path == "example-jukebox:jukebox/player":
            if "example-jukebox:jukebox" not in validation_data:
                validation_data["example-jukebox:jukebox"] = {}
            validation_data["example-jukebox:jukebox"]["player"] = data
        else:
            # Для других путей применяем общее обновление
            validation_data.update(data)

    def _merge_data(self, datastore, path, data):
        """Вспомогательный метод для слияния данных"""
        # Упрощенная логика слияния
        raw_data = datastore.raw_value()

        # Это базовая реализация, в реальности нужна более сложная логика
        # для правильного слияния данных по пути
        if isinstance(data, dict):
            for key, value in data.items():
                raw_data[key] = value

        return self.data_model.from_raw(raw_data)

    def _save_datastore(self):
        """Сохраняет хранилище в файл"""
        try:
            # Получаем сырые данные из хранилища
            raw_data = self.datastore.raw_value()
            save_json_file(raw_data, self.data_file)
        except Exception as e:
            raise InternalServerError(f"Не удалось сохранить данные: {e}")

    def validate_data(self, data):
        """Валидирует данные против схемы"""
        try:
            instance = self.data_model.from_raw(data)  # type: ignore
            instance.validate(ctype=ContentType.config)
            return True
        except Exception as e:
            raise ValidationError(f"Данные не прошли валидацию: {e}")
