import json
from .utils.exceptions import BadRequestError, NotFoundError


class RPCHandler:
    """Обрабатывает вызовы RPC операций"""

    def __init__(self, yang_manager):
        self.yang_manager = yang_manager

    def handle_rpc(self, rpc_name, input_data=None):
        """Обрабатывает вызов RPC операции"""
        # Определяем доступные RPC операции
        if rpc_name == "example-jukebox:play":
            return self._handle_play_rpc(input_data)
        else:
            raise NotFoundError(
                error_tag="unknown-element",
                error_message=f"RPC операция '{rpc_name}' не найдена"
            )

    def _handle_play_rpc(self, input_data):
        """Обрабатывает RPC операцию 'play'"""
        if not input_data:
            raise BadRequestError(
                error_tag="missing-element", 
                error_message="Отсутствуют входные параметры для RPC 'play'"
            )

        # Проверяем обязательные параметры
        playlist_name = input_data.get("playlist")
        song_number = input_data.get("song-number")

        if not playlist_name:
            raise BadRequestError(
                error_tag="missing-element",
                error_message="Параметр 'playlist' обязателен"
            )

        if song_number is None:
            raise BadRequestError(
                error_tag="missing-element", 
                error_message="Параметр 'song-number' обязателен"
            )

        # Проверяем существование плейлиста
        try:
            playlists_data = self.yang_manager.get_data("example-jukebox:jukebox/playlist")
            if not playlists_data:
                raise NotFoundError(
                    error_tag="data-missing",
                    error_message="Плейлисты не найдены"
                )

            # Ищем нужный плейлист
            target_playlist = None
            if isinstance(playlists_data, list):
                for playlist in playlists_data:
                    if playlist.get("name") == playlist_name:
                        target_playlist = playlist
                        break
            elif isinstance(playlists_data, dict) and playlists_data.get("name") == playlist_name:
                target_playlist = playlists_data

            if not target_playlist:
                raise NotFoundError(
                    error_tag="data-missing",
                    error_message=f"Плейлист '{playlist_name}' не найден"
                )

            # Проверяем номер песни
            songs = target_playlist.get("song", [])
            if song_number < 1 or song_number > len(songs):
                raise BadRequestError(
                    error_tag="invalid-value",
                    error_message=f"Неверный номер песни: {song_number}"
                )

            # Имитируем воспроизведение
            selected_song = songs[song_number - 1]

            # Возвращаем результат (output пустой согласно YANG модели)
            return {
                "status": "success",
                "message": f"Воспроизведение начато: плейлист '{playlist_name}', песня номер {song_number}",
                "song_id": selected_song.get("id", "unknown")
            }

        except Exception as e:
            if isinstance(e, (BadRequestError, NotFoundError)):
                raise
            raise BadRequestError(
                error_tag="operation-failed",
                error_message=f"Ошибка при выполнении RPC 'play': {str(e)}"
            )

    def get_available_operations(self):
        """Возвращает список доступных RPC операций"""
        return {
            "operations": {
                "example-jukebox:play": None  # Пустое значение означает, что операция доступна
            }
        }
