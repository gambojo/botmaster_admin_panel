import logging
from aiohttp import web
import aiohttp_jinja2


class GroupsHandlers:
    """Обработчики групп."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('groups.html')
    async def _handle_groups(self, request):
        """Управление группами."""
        return {'active_page': 'groups'}

    async def _api_get_groups(self, request):
        """Получение групп (прокси к Bot API)."""
        self.logger.debug('Get all groups')
        return web.json_response(
            await self.panel.api_request('GET', '/api/groups')
        )

    async def _api_create_group(self, request):
        """Создание группы (прокси к Bot API)."""
        self.logger.debug('Create new group')
        data = await request.json()
        return web.json_response(
            await self.panel.api_request('POST', '/api/groups', json=data)
        )

    async def _api_add_user_to_group(self, request):
        """Добавление пользователя в группу (прокси к Bot API)."""
        self.logger.debug('Add user to group')
        group_name = request.match_info['group_name']
        data = await request.json()
        return web.json_response(
            await self.panel.api_request('POST', f'/api/groups/{group_name}/users', json=data)
        )

    async def _api_delete_group(self, request):
        """Удаление группы (прокси к Bot API)."""
        self.logger.debug('Delete group')
        group_name = request.match_info['group_name']
        return web.json_response(
            await self.panel.api_request('DELETE', f'/api/groups/{group_name}')
        )

    async def _api_get_group_members(self, request):
        """Получение участников группы (прокси к Bot API)."""
        self.logger.debug('Get group members')
        group_name = request.match_info['group_name']
        return web.json_response(
            await self.panel.api_request('GET', f'/api/groups/{group_name}/members')
        )

    async def _api_remove_user_from_group(self, request):
        """Удаление пользователя из группы (прокси к Bot API)."""
        self.logger.debug('Remove user from group')
        group_name = request.match_info['group_name']
        user_id = request.match_info['user_id']
        return web.json_response(
            await self.panel.api_request('DELETE', f'/api/groups/{group_name}/users/{user_id}')
        )
