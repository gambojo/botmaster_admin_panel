import logging
from aiohttp import web
import aiohttp_jinja2


class InfoHandlers:
    """Обработчики информации."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('info.html')
    async def _handle_info(self, request):
        """Объединенная страница информации."""
        return {'active_page': 'info'}

    async def _api_health_check(self, request):
        """Health check endpoint (прокси к Bot API)."""
        self.logger.debug('Health check endpoint.')
        return web.json_response(
            await self.panel.api_request('GET', '/api/health')
        )

    async def _api_get_statistics(self, request):
        """Получение статистики (прокси к Bot API)."""
        self.logger.debug('Get statistics')
        return web.json_response(
            await self.panel.api_request('GET', '/api/statistics')
        )

    async def _api_get_bot_info(self, request):
        """Получение информации о боте (прокси к Bot API)."""
        self.logger.debug('Get Bot info')
        return web.json_response(
            await self.panel.api_request('GET', '/api/bot/info')
        )
