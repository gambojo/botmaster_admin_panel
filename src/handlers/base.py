import logging
from aiohttp import web
import aiohttp_jinja2


class BaseHandlers:
    """Базовые обработчики."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    async def _handle_favicon(self, request):
        """Обработчик для фавикона."""
        return web.Response(status=404)

    async def _handle_root(self, request):
        """Обработчик корневого маршрута."""
        return web.HTTPFound('/admin')

    async def _handle_admin_root(self, request):
        """Обработчик главной страницы админки."""
        if await self.panel.check_auth(request):
            return web.HTTPFound('/admin/info')
        else:
            return web.HTTPFound('/admin/login')

    async def _api_get_themes(self, request):
        from pathlib import Path
        try:
            theme_dir = Path(self.panel.static_path) / 'css' / 'themes'
            themes = [f.stem for f in theme_dir.glob('*.css')]
            return web.json_response(themes)
        except Exception as e:
            import traceback
            self.logger.error(f"Ошибка при получении тем: {e}")
            self.logger.error(traceback.format_exc())
            return web.json_response({'error': 'Не удалось загрузить темы'}, status=500)
