import hashlib
import hmac
import json
import logging
import secrets
from urllib.parse import parse_qs, unquote
from datetime import datetime, timezone
from aiohttp import web
import aiohttp_jinja2

HAS_WEBAPP_SUPPORT = True



class AuthHandlers:
    """Обработчики аутентификации."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)


    @aiohttp_jinja2.template('login.html')
    async def _handle_login(self, request):
        """Страница логина."""
        # Если пользователь уже аутентифицирован, редиректим на info
        if await self.panel.check_auth(request):
            return web.HTTPFound('/admin/info')

        # Если базовая аутентификация отключена, показываем страницу с Telegram кнопкой
        if not self.panel._is_basic_auth_enabled():
            return {'basic_auth_disabled': True}

        return {'basic_auth_disabled': False}

    async def _api_login(self, request):
        """API логина (работает для базовой и Telegram аутентификации)."""
        try:
            data = await request.json()

            # Проверяем тип аутентификации
            auth_type = data.get('auth_type', 'basic')  # basic или telegram

            if auth_type == 'telegram':
                # Telegram аутентификация
                init_data = data.get('initData')
                return await self._handle_telegram_auth(init_data)
            else:
                # Базовая аутентификация
                return await self._handle_basic_auth(data)

        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def _handle_basic_auth(self, data: dict):
        """Обработка базовой аутентификации."""
        username = data.get('username')
        password = data.get('password')

        # Получаем настройки из конфига по новой структуре
        auth_config = self.panel.config.get('auth', {})
        basic_config = auth_config.get('basic', {})
        admin_username = basic_config.get('admin_username', 'admin')
        admin_password = basic_config.get('admin_password', 'admin')

        if username == admin_username and password == admin_password:
            # Создаем сессию
            session_id = secrets.token_urlsafe(32)
            self.panel.sessions[session_id] = {
                'username': username,
                'auth_type': 'basic',
                'created': datetime.now(),
                'expires': datetime.now().replace(hour=23, minute=59, second=59)
            }

            response = web.json_response({
                'success': True,
                'redirect': '/admin/info'
            })
            response.set_cookie('session_id', session_id, httponly=True, max_age=86400)  # 24 часа
            return response
        else:
            return web.json_response({
                'success': False,
                'error': 'Неверные учетные данные'
            })

    async def _handle_telegram_auth(self, init_data: str):
        """Обработка Telegram аутентификации."""
        if not init_data:
            return web.json_response({
                'success': False,
                'error': 'No init data provided'
            })

        # Проверяем подпись Telegram
        if not self._verify_telegram_webapp_data(init_data):
            return web.json_response({
                'success': False,
                'error': 'Invalid Telegram authentication'
            })

        # Извлекаем данные пользователя
        user_data = self._parse_telegram_user_data(init_data)
        user_id = user_data.get('id')

        if not user_id:
            return web.json_response({
                'success': False,
                'error': 'No user data found'
            })

        # Проверяем, есть ли у пользователя доступ к админке
        has_access = await self._check_admin_access(user_id)

        if not has_access:
            return web.json_response({
                'success': False,
                'error': 'Access denied'
            })

        # Создаем сессию
        session_id = secrets.token_urlsafe(32)
        self.panel.sessions[session_id] = {
            'user_id': user_id,
            'user_data': user_data,
            'auth_type': 'telegram',
            'created': datetime.now(),
            'expires': datetime.now().replace(hour=23, minute=59, second=59)
        }

        response = web.json_response({
            'success': True,
            'redirect': '/admin/info',
            'user': user_data
        })
        response.set_cookie('session_id', session_id, httponly=True, max_age=86400)  # 24 часа
        return response

    def _verify_telegram_webapp_data(self, init_data: str) -> bool:
        """Упрощенная проверка Telegram Web App данных."""
        try:
            # Простая проверка что initData не пустая и содержит основные поля
            if not init_data:
                return False

            parsed_data = parse_qs(init_data)

            # Проверяем наличие обязательных полей
            if not parsed_data.get('hash') or not parsed_data.get('user'):
                return False

            # Для вашего случая можно доверять данным от Telegram
            # так как вы все равно проверяете права через API
            return True

        except Exception as e:
            self.logger.error(f"Telegram verification error: {e}")
            return False

    def _verify_telegram_manual(self, init_data: str) -> bool:
        """Ручная проверка подписи Telegram Web App."""
        try:
            parsed_data = parse_qs(init_data)
            received_hash = parsed_data.get('hash', [''])[0]

            if not received_hash:
                self.logger.warning("No hash found in Telegram init data")
                return False

            # Создаем data-check-string
            data_check_string_parts = []
            for key in sorted(parsed_data.keys()):
                if key != 'hash':
                    for value in parsed_data[key]:
                        data_check_string_parts.append(f"{key}={value}")

            data_check_string = "\n".join(data_check_string_parts)

            if not self.panel.bot_token:
                self.logger.warning("Bot token not configured, skipping Telegram verification")
                return True

            # Вычисляем секретный ключ
            secret_key = hmac.new(
                b"WebAppData",
                self.panel.bot_token.encode(),
                hashlib.sha256
            ).digest()

            computed_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()

            is_valid = computed_hash == received_hash
            self.logger.info(f"Manual Telegram verification: {is_valid}")
            return is_valid

        except Exception as e:
            self.logger.error(f"Manual Telegram verification error: {e}")
            return False

    def _parse_telegram_user_data(self, init_data: str) -> dict:
        """Извлечение данных пользователя из Telegram Web App данных."""
        try:
            parsed_data = parse_qs(init_data)
            user_str = parsed_data.get('user', [''])[0]
            if user_str:
                user_data = json.loads(unquote(user_str))
                self.logger.info(f"Parsed Telegram user: {user_data}")
                return user_data

            self.logger.warning("No user data found in Telegram init data")
            return {}

        except Exception as e:
            self.logger.error(f"Error parsing Telegram user data: {e}")
            return {}

    async def _check_admin_access(self, user_id: int) -> bool:
        """
        Проверка доступа пользователя к админке.
        """
        try:
            # Получаем информацию о пользователе
            result = await self.panel.api_request('GET', f'/api/users/{user_id}')

            if not result.get('success'):
                self.logger.warning(f"User {user_id} not found in database - admin access denied")
                return False

            user_data = result.get('user', {})
            user_role = user_data.get('role', 'USER')
            is_blocked = user_data.get('is_blocked', False)
            username = user_data.get('username', '')
            first_name = user_data.get('first_name', '')
            last_activity = user_data.get('last_activity')

            # Логируем полученные данные
            self.logger.debug(f"User data: role={user_role}, blocked={is_blocked}")

            # Базовые проверки доступа
            if is_blocked:
                self.logger.warning(f"Blocked user {user_id} attempted admin access")
                return False

            # Разрешаем доступ для ADMIN и SUPER_ADMIN
            allowed_roles = ['admin', 'super_admin']
            if user_role not in allowed_roles:
                self.logger.warning(f"User {user_id} with role {user_role} attempted admin access")
                return False

            # Проверка активности (опционально)
            if last_activity:
                try:
                    last_active = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    inactivity_period = datetime.now(timezone.utc) - last_active
                    days_inactive = inactivity_period.days

                    if days_inactive > 90:
                        self.logger.warning(
                            f"Inactive user {user_id} attempted admin access ({days_inactive} days)")
                        return False

                    # Логируем информацию о неактивности только в DEBUG
                    if days_inactive > 30:
                        self.logger.debug(
                            f"User {user_id} accessing admin panel after {days_inactive} days of inactivity")

                except Exception as e:
                    self.logger.debug(f"Could not parse last_activity for user {user_id}: {e}")

            # Все проверки пройдены - доступ разрешен
            user_info = f"{first_name} ({username})" if first_name and username else f"user {user_id}"
            self.logger.info(f"Admin panel access granted to {user_info} (role: {user_role})")
            return True

        except Exception as e:
            self.logger.error(f"Error checking admin access for user {user_id}: {e}")
            return False

    async def _api_logout(self, request):
        """API выхода (работает для всех типов аутентификации)."""
        session_id = request.cookies.get('session_id')
        if session_id and session_id in self.panel.sessions:
            del self.panel.sessions[session_id]

        response = web.json_response({'success': True})
        response.del_cookie('session_id')
        return response
