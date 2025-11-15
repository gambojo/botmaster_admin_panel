import logging
from aiohttp import web
import aiohttp_jinja2
import aiohttp


class PluginsHandlers:
    """Обработчики плагинов."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('plugins.html')
    async def _handle_plugins(self, request):
        """Управление плагинами."""
        return {'active_page': 'plugins'}

    async def _api_get_plugins(self, request):
        """Получение плагинов (прокси к Bot API)."""
        self.logger.debug('Getting plugins')
        return web.json_response(
            await self.panel.api_request('GET', '/api/plugins')
        )

    async def _api_get_available_plugins(self, request):
        """Получение доступных плагинов (прокси к Bot API)."""
        self.logger.debug('Getting available plugins')
        return web.json_response(
            await self.panel.api_request('GET', '/api/plugins/available')
        )

    async def _api_enable_plugin(self, request):
        """Включение плагина (прокси к Bot API)."""
        plugin_name = request.match_info['plugin_name']
        self.logger.debug(f"Enabling plugin: {plugin_name}")
        return web.json_response(
            await self.panel.api_request('POST', f'/api/plugins/{plugin_name}/enable')
        )

    async def _api_disable_plugin(self, request):
        """Отключение плагина (прокси к Bot API)."""
        plugin_name = request.match_info['plugin_name']
        self.logger.debug(f"Disabling plugin: {plugin_name}")
        return web.json_response(
            await self.panel.api_request('POST', f'/api/plugins/{plugin_name}/disable')
        )

    async def _api_reload_plugin(self, request):
        """Перезагрузка плагина (прокси к Bot API)."""
        plugin_name = request.match_info['plugin_name']
        self.logger.debug(f"Reloading plugin: {plugin_name}")
        return web.json_response(
            await self.panel.api_request('POST', f'/api/plugins/{plugin_name}/reload')
        )

    async def _api_upload_plugin_file(self, request):
        """Загрузка плагина из файла (прокси к Bot API)."""
        # Пересылаем multipart данные
        reader = await request.multipart()
        data = aiohttp.FormData()
        self.logger.debug(f"Uploading plugin from file: {request.match_info['plugin_name']}")

        async for field in reader:
            if field.filename:
                file_data = await field.read()
                data.add_field(
                    field.name,
                    file_data,
                    filename=field.filename,
                    content_type=field.headers.get('Content-Type')
                )
            else:
                text_data = await field.text()
                data.add_field(field.name, text_data)

        return web.json_response(
            await self.panel.api_request('POST', '/api/plugins/upload', data=data)
        )

    async def _api_upload_plugin_url(self, request):
        """Загрузка плагина по URL (прокси к Bot API)."""
        data = await request.json()
        self.logger.debug(f"Uploading plugin from url: {request.match_info['plugin_name']}")
        return web.json_response(
            await self.panel.api_request('POST', '/api/plugins/upload-url', json=data)
        )

    async def _api_upload_plugin_github(self, request):
        """Загрузка плагина с GitHub (прокси к Bot API)."""
        data = await request.json()
        self.logger.debug(f"Uploading plugin from github: {request.match_info['plugin_name']}")
        return web.json_response(
            await self.panel.api_request('POST', '/api/plugins/upload-github', json=data)
        )
