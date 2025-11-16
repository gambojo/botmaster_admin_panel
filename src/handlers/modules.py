import logging
from aiohttp import web
import aiohttp_jinja2


class ModulesHandlers:
    """Handlers for module management."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)

    @aiohttp_jinja2.template('modules.html')
    async def _handle_modules(self, request):
        """Module management page."""
        return {'active_page': 'modules'}

    async def _api_get_modules(self, request):
        """Get all modules configuration (proxy to Bot API)."""
        self.logger.debug('Getting all modules')
        return web.json_response(
            await self.panel.api_request('GET', '/api/modules')
        )

    async def _api_get_module(self, request):
        """Get specific module configuration (proxy to Bot API)."""
        module_name = request.match_info['module_name']
        self.logger.debug(f'Getting module: {module_name}')
        return web.json_response(
            await self.panel.api_request('GET', f'/api/modules/{module_name}')
        )

    async def _api_enable_module(self, request):
        """Enable module (proxy to Bot API)."""
        module_name = request.match_info['module_name']
        self.logger.info(f'Enabling module: {module_name}')
        return web.json_response(
            await self.panel.api_request('POST', f'/api/modules/{module_name}/enable')
        )

    async def _api_disable_module(self, request):
        """Disable module (proxy to Bot API)."""
        module_name = request.match_info['module_name']
        self.logger.info(f'Disabling module: {module_name}')
        return web.json_response(
            await self.panel.api_request('POST', f'/api/modules/{module_name}/disable')
        )
