import logging
from aiohttp import web
import aiohttp_jinja2
import aiohttp


class UsersHandlers:
    """Обработчики пользователей."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('users.html')
    async def _handle_users(self, request):
        """Управление пользователями."""
        return {'active_page': 'users'}

    async def _api_get_users(self, request):
        """Получение пользователей (прокси к Bot API)."""
        query_string = request.query_string
        endpoint = f'/api/users?{query_string}' if query_string else '/api/users'
        self.logger.debug('Getting users')
        return web.json_response(
            await self.panel.api_request('GET', endpoint)
        )

    async def _api_get_user(self, request):
        """Получение пользователя (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Get user {user_id}')
        return web.json_response(
            await self.panel.api_request('GET', f'/api/users/{user_id}')
        )

    async def _api_update_user_role(self, request):
        """Обновление роли пользователя (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        data = await request.json()
        self.logger.debug(f'Update role for user {user_id}')
        return web.json_response(
            await self.panel.api_request('PUT', f'/api/users/{user_id}/role', json=data)
        )

    async def _api_block_user(self, request):
        """Блокировка пользователя (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Block user {user_id}')
        return web.json_response(
            await self.panel.api_request('POST', f'/api/users/{user_id}/block')
        )

    async def _api_unblock_user(self, request):
        """Разблокировка пользователя (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Unblock user {user_id}')
        return web.json_response(
            await self.panel.api_request('POST', f'/api/users/{user_id}/unblock')
        )

    async def _api_delete_user(self, request):
        """Удаление пользователя (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Delete user {user_id}')
        return web.json_response(
            await self.panel.api_request('DELETE', f'/api/users/{user_id}')
        )

    async def _api_send_message(self, request):
        """Отправка сообщения пользователю (прокси к Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Send message for user {user_id}')

        # Проверяем тип контента
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            # Пересылаем multipart данные
            reader = await request.multipart()
            data = aiohttp.FormData()

            async for field in reader:
                if field.filename:
                    # Это файл
                    file_data = await field.read()
                    data.add_field(
                        field.name,
                        file_data,
                        filename=field.filename,
                        content_type=field.headers.get('Content-Type')
                    )
                else:
                    # Это текстовое поле
                    text_data = await field.text()
                    data.add_field(field.name, text_data)

            return web.json_response(
                await self.panel.api_request('POST', f'/api/users/{user_id}/message', data=data)
            )
        else:
            # Обычный JSON запрос (обратная совместимость)
            data = await request.json()
            return web.json_response(
                await self.panel.api_request('POST', f'/api/users/{user_id}/message', json=data)
            )
