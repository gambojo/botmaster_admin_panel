import logging
from aiohttp import web
import aiohttp_jinja2


class LogsHandlers:
    """Обработчики логов."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('logs.html')
    async def _handle_logs(self, request):
        """Логи системы."""
        return {'active_page': 'logs'}

    async def _api_get_logs(self, request):
        """Получение логов (прокси к Bot API)."""
        self.logger.debug('Getting logs')
        query_string = request.query_string
        endpoint = f'/api/logs?{query_string}' if query_string else '/api/logs'
        return web.json_response(
            await self.panel.api_request('GET', endpoint)
        )

    async def _api_get_logs_by_type(self, request):
        """Получение логов по типу (прокси к Bot API)."""
        self.logger.debug('Getting logs by type')
        log_type = request.match_info['log_type']
        query_string = request.query_string
        endpoint = f'/api/logs/{log_type}?{query_string}' if query_string else f'/api/logs/{log_type}'
        return web.json_response(
            await self.panel.api_request('GET', endpoint)
        )
