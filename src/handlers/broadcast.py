import logging
from aiohttp import web
import aiohttp_jinja2
import aiohttp


class BroadcastHandlers:
    """Обработчики рассылок."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)

    @aiohttp_jinja2.template('broadcast.html')
    async def _handle_broadcast(self, request):
        """Рассылка сообщений."""
        return {'active_page': 'broadcast'}

    async def _api_send_broadcast(self, request):
        """Отправка рассылки (прокси к Bot API)."""
        # Проверяем тип контента
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            # Пересылаем multipart данные
            reader = await request.multipart()
            data = aiohttp.FormData()

            async for field in reader:
                if field.filename:
                    # Это файл
                    self.logger.debug('Data from file {}'.format(field.filename))
                    file_data = await field.read()
                    data.add_field(
                        field.name,
                        file_data,
                        filename=field.filename,
                        content_type=field.headers.get('Content-Type')
                    )
                else:
                    # Это текстовое поле
                    self.logger.debug('Data from text {} '.format(field.text))
                    text_data = await field.text()
                    data.add_field(field.name, text_data)

            return web.json_response(
                await self.panel.api_request('POST', '/api/broadcast', data=data)
            )
        else:
            # Обычный JSON запрос (обратная совместимость)
            self.logger.debug('Data from json {}'.format(content_type))
            data = await request.json()
            return web.json_response(
                await self.panel.api_request('POST', '/api/broadcast', json=data)
            )

    async def _api_get_broadcasts(self, request):
        """Получение рассылок (прокси к Bot API)."""
        return web.json_response(
            await self.panel.api_request('GET', '/api/broadcast')
        )
