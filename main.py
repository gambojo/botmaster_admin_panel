"""
Standalone Admin Panel Application
===================================

Web-based admin panel as a standalone application,
connecting to the bot via REST API.
"""

import asyncio
from datetime import datetime
from typing import Dict
from pathlib import Path
from aiohttp import web, ClientSession
import aiohttp_jinja2
import aiohttp_cors
import jinja2
import logging

from src.config_manager import get_config
from src.logging_config import setup_logging
from src.handlers import (plugins, base)
from src.handlers import auth, users, info, logs, groups, broadcast, modules, referrals
from src.audit_logger import AuditLogger  # Добавьте этот импорт


class AdminPanelApp:
    """
    Standalone admin panel application.
    Connects to the bot via REST API.
    """

    def __init__(self, config_manager=None):
        """
        Initialize admin panel.

        Args:
            config_manager: Configuration manager instance
        """
        # Use config manager as primary configuration source
        self.config_manager = config_manager or get_config()

        # Initialize centralized logging FIRST
        setup_logging(self.config_manager.config)

        # Disable aiohttp access log
        if self.config_manager.get('logging.aiohttp_access_log.disable'):
            access_logger = logging.getLogger('aiohttp.access')
            access_logger.setLevel(logging.WARNING)
            access_logger.propagate = False

        # Initialize loggers
        self.logger = logging.getLogger(self.__class__.__name__)
        self.audit_logger = AuditLogger(self.config_manager)

        # Get configuration values using config manager
        self.bot_api_url = self.config_manager.get('api.url', 'http://localhost:8081')
        self.api_key = self.config_manager.get('api.key', '')

        # For backward compatibility, keep self.config
        self.config = self.config_manager.config

        # Session storage
        self.sessions = {}

        # Paths to templates and static files
        self.base_dir = Path(__file__).parent
        self.template_path = self.base_dir / "templates"
        self.static_path = self.base_dir / "static"

        # Create web application
        # self.app = web.Application(middlewares=[self.auth_middleware])
        self.app = web.Application(
            middlewares=[self.auth_middleware],
            logger=None
        )

        self.app.middlewares.append(self.logging_middleware)

        # Setup Jinja2 templates
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(str(self.template_path))
        )

        # Initialize handlers
        self._init_handlers()

        # Setup routes
        self._setup_routes()

        # HTTP client for API requests
        self.client_session = None

        # Flag for graceful shutdown
        self.is_shutting_down = False

        # Setup CORS if enabled
        if self._is_cors_enabled():
            self._setup_cors()

        self.logger.info("AdminPanelApp initialized with config manager and audit logger")

    def _is_basic_auth_enabled(self) -> bool:
        """Check if basic authentication is enabled."""
        return self.config_manager.get('auth.basic.enable', False)

    def _is_cors_enabled(self) -> bool:
        """Check if CORS is enabled."""
        return self.config_manager.get('auth.cors.enable', False)

    def _get_cors_config(self) -> Dict:
        """Get CORS configuration."""
        return {
            'allowed_origins': self.config_manager.get('auth.cors.allowed_origins', []),
            'allowed_methods': self.config_manager.get('auth.cors.allowed_methods', []),
            'allowed_headers': self.config_manager.get('auth.cors.allowed_headers', [])
        }

    def _get_basic_auth_config(self) -> Dict:
        """Get basic authentication configuration."""
        return {
            'admin_username': self.config_manager.get('auth.basic.admin_username', 'admin'),
            'admin_password': self.config_manager.get('auth.basic.admin_password', 'admin')
        }

    def _setup_cors(self):
        """Setup CORS configuration."""
        try:
            # Get CORS config
            cors_config = self._get_cors_config()

            # Configure CORS for all routes
            cors_options = {
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            }

            # Add origin-specific options if origins are specified
            if cors_config['allowed_origins']:
                for origin in cors_config['allowed_origins']:
                    cors_options[origin] = aiohttp_cors.ResourceOptions(
                        allow_credentials=True,
                        expose_headers="*",
                        allow_headers="*",
                    )

            cors = aiohttp_cors.setup(self.app, defaults=cors_options)

            # Apply CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)

            self.logger.info("CORS configured for all routes")

        except Exception as e:
            self.logger.error(f"Error setting up CORS: {e}")

    async def auth_middleware(self, app, handler):
        """Authentication middleware with Telegram Web App support."""

        async def middleware_handler(request):
            public_routes = [
                '/admin/login',
                '/admin/api/login',
                '/static/',
                '/favicon.ico'
            ]

            # Check if route is public
            is_public = any(request.path.startswith(route) for route in public_routes)

            if is_public:
                return await handler(request)

            # Check authentication
            is_authenticated = await self._check_authentication(request)

            if not is_authenticated:
                return await self._handle_unauthorized(request)

            return await handler(request)

        return middleware_handler

    @web.middleware
    async def logging_middleware(self, request, handler):
        if request.path.startswith("/static") or request.path == "/favicon.ico":
            return await handler(request)

        # Используем метод из audit_logger для получения клиентской информации
        client_info = self.audit_logger.get_client_info(request)
        display_name = self._get_display_name(request)

        # Временное отладочное логирование
        session_id = request.cookies.get("session_id")
        if session_id and session_id in self.sessions:
            session_data = self.sessions[session_id]
            self.logger.debug(f"Session data for {session_id}: {session_data}")
        else:
            self.logger.debug(f"No valid session for request to {request.path}")

        self.logger.debug(f"Display name resolved: {display_name}")

        start_time = datetime.now()

        try:
            response = await handler(request)
            processing_time = (datetime.now() - start_time).total_seconds()

            # Используем audit_logger для логирования API вызовов
            self.audit_logger.log_api_call(
                endpoint=request.path,
                method=request.method,
                username=display_name,
                response_status=response.status,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                processing_time=processing_time
            )

            return response

        except web.HTTPException as ex:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.audit_logger.log_api_call(
                endpoint=request.path,
                method=request.method,
                username=display_name,
                response_status=ex.status,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                processing_time=processing_time
            )
            raise
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.audit_logger.log_security_event(
                event_type="unhandled_exception",
                severity="HIGH",
                username=display_name,
                ip_address=client_info["ip_address"],
                details=f"{request.method} {request.path} ({processing_time:.3f}s): {str(e)}"
            )
            raise

    def _get_display_name(self, request) -> str:
        """
        Get display name for logging - works for both Telegram and basic auth.
        Returns formatted string that shows exactly who is making the request.
        """
        try:
            session_id = request.cookies.get("session_id")
            if not session_id or session_id not in self.sessions:
                return None

            session = self.sessions[session_id]

            # Check for Telegram user data
            if 'user_data' in session and session['user_data']:
                user_data = session['user_data']
                self.logger.debug(f"Found Telegram user_data: {user_data}")

                if isinstance(user_data, dict):
                    first_name = user_data.get('first_name', '').strip()
                    username = user_data.get('username', '').strip()

                    # Форматируем как в старом логгере: "Гама (@gambo_jo)" или "user_785818468"
                    if first_name and username:
                        return f"{first_name} (@{username})"
                    elif first_name:
                        return first_name
                    elif username:
                        return f"@{username}"
                    else:
                        user_id = user_data.get('id')
                        return f"user_{user_id}" if user_id else "telegram_user"

            # Check for basic auth username - возвращаем просто имя пользователя
            if 'username' in session and session['username']:
                username = session['username']
                self.logger.debug(f"Found basic auth username: {username}")
                return str(username)  # Просто "admin" как было раньше

            return None

        except Exception as e:
            self.logger.error(f"Error getting display name: {e}")
            return None

    def _get_session_user_info(self, request):
        """
        Get user information from session.
        Compatible with both auth types from your auth.py.
        """
        session_id = request.cookies.get("session_id")
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]

            # For Telegram auth - user_data contains full user info
            if 'user_data' in session and session['user_data']:
                return session['user_data']

            # For basic auth - only username is available
            if 'username' in session and session['username']:
                return session['username']

        return None

    async def _check_authentication(self, request):
        """
        Universal authentication check.
        Works with basic authentication, Telegram Web App and CORS.
        """
        # 1. Check session authentication (common for all types)
        session_id = request.cookies.get('session_id')
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if session.get('expires', datetime.now()) > datetime.now():
                return True

        # 2. If basic authentication is enabled - require login
        if self._is_basic_auth_enabled():
            return False

        # 3. If basic authentication is disabled, allow access
        # (assuming Telegram Web App or other external authentication is used)
        return True

    async def _handle_unauthorized(self, request):
        """Handle unauthorized access."""
        if request.path.startswith('/api/'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        else:
            return web.HTTPFound('/admin/login')

    def _init_handlers(self):
        """Initialize all handlers."""
        # Pass config_manager to handlers if they need it
        self.base_handlers = base.BaseHandlers(self)
        self.auth_handlers = auth.AuthHandlers(self)
        self.users_handlers = users.UsersHandlers(self)
        self.groups_handlers = groups.GroupsHandlers(self)
        self.broadcast_handlers = broadcast.BroadcastHandlers(self)
        self.plugins_handlers = plugins.PluginsHandlers(self)
        self.logs_handlers = logs.LogsHandlers(self)
        self.info_handlers = info.InfoHandlers(self)
        self.modules_handlers = modules.ModulesHandlers(self)
        self.referrals_handlers = referrals.ReferralsHandlers(self)

    async def check_auth(self, request):
        """Public method to check authentication."""
        return await self._check_authentication(request)

    async def init_client_session(self):
        """Initialize HTTP client."""
        self.client_session = ClientSession()

    async def close_client_session(self):
        """Close HTTP client."""
        if self.client_session:
            await self.client_session.close()

    async def api_request(self, method: str, endpoint: str, **kwargs):
        """
        Execute request to Bot API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/users')
            **kwargs: Additional request parameters

        Returns:
            Dict: API response
        """
        if not self.client_session:
            await self.init_client_session()

        url = f"{self.bot_api_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['X-API-Key'] = self.api_key

        try:
            self.logger.debug(f"API Request: {method} {url}")

            async with self.client_session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                result = await response.json()
                self.logger.debug(f"API Response: {response.status}")
                return result

        except Exception as e:
            self.logger.error(f"API request error: {method} {endpoint} - {e}")
            return {'success': False, 'error': str(e)}

    def _setup_routes(self):
        """Setup application routes."""

        # Static files - CSS, JS, images
        self.app.router.add_static('/static/', path=str(self.static_path), name='static')

        # Main pages - HTML страницы админ-панели
        self.app.router.add_get('/', self.base_handlers._handle_root)
        self.app.router.add_get('/admin', self.base_handlers._handle_admin_root)
        self.app.router.add_get('/admin/api/themes', self.base_handlers._api_get_themes)

        # Health check - проверка работоспособности сервиса
        self.app.router.add_get('/api/health', self.info_handlers._api_health_check)

        # Admin panel pages - страницы разделов админки
        self.app.router.add_get('/admin/login', self.auth_handlers._handle_login)
        self.app.router.add_get('/admin/users', self.users_handlers._handle_users)
        self.app.router.add_get('/admin/logs', self.logs_handlers._handle_logs)
        self.app.router.add_get('/admin/broadcast', self.broadcast_handlers._handle_broadcast)
        self.app.router.add_get('/admin/groups', self.groups_handlers._handle_groups)
        self.app.router.add_get('/admin/plugins', self.plugins_handlers._handle_plugins)
        self.app.router.add_get('/admin/info', self.info_handlers._handle_info)
        self.app.router.add_get('/admin/modules', self.modules_handlers._handle_modules)
        self.app.router.add_get('/admin/referrals', self.referrals_handlers._handle_referrals)

        # User management API - управление пользователями
        self.app.router.add_get('/api/statistics', self.info_handlers._api_get_statistics)
        self.app.router.add_get('/api/users', self.users_handlers._api_get_users)
        self.app.router.add_get('/api/users/{user_id}', self.users_handlers._api_get_user)
        self.app.router.add_put('/api/users/{user_id}/role', self.users_handlers._api_update_user_role)
        self.app.router.add_post('/api/users/{user_id}/block', self.users_handlers._api_block_user)
        self.app.router.add_post('/api/users/{user_id}/unblock', self.users_handlers._api_unblock_user)
        self.app.router.add_delete('/api/users/{user_id}', self.users_handlers._api_delete_user)
        self.app.router.add_post('/api/users/{user_id}/message', self.users_handlers._api_send_message)

        # Logs API - работа с логами
        self.app.router.add_get('/api/logs', self.logs_handlers._api_get_logs)
        self.app.router.add_get('/api/logs/{log_type}', self.logs_handlers._api_get_logs_by_type)

        # Broadcast API - массовая рассылка сообщений
        self.app.router.add_post('/api/broadcast', self.broadcast_handlers._api_send_broadcast)
        self.app.router.add_get('/api/broadcast', self.broadcast_handlers._api_get_broadcasts)

        # Groups management API - управление группами пользователей
        self.app.router.add_get('/api/groups', self.groups_handlers._api_get_groups)
        self.app.router.add_post('/api/groups', self.groups_handlers._api_create_group)
        self.app.router.add_get('/api/groups/{group_name}/members', self.groups_handlers._api_get_group_members)
        self.app.router.add_post('/api/groups/{group_name}/users', self.groups_handlers._api_add_user_to_group)
        self.app.router.add_delete('/api/groups/{group_name}/users/{user_id}',
                                   self.groups_handlers._api_remove_user_from_group)
        self.app.router.add_delete('/api/groups/{group_name}', self.groups_handlers._api_delete_group)

        # Plugin management API - управление плагинами
        self.app.router.add_get('/admin/api/plugins', self.plugins_handlers._api_get_plugins)
        self.app.router.add_get('/admin/api/plugins/available', self.plugins_handlers._api_get_available_plugins)
        self.app.router.add_post('/admin/api/plugins/{plugin_name}/enable', self.plugins_handlers._api_enable_plugin)
        self.app.router.add_post('/admin/api/plugins/{plugin_name}/disable', self.plugins_handlers._api_disable_plugin)
        self.app.router.add_post('/admin/api/plugins/{plugin_name}/reload', self.plugins_handlers._api_reload_plugin)

        # Plugin upload API - загрузка плагинов
        self.app.router.add_post('/admin/api/plugins/upload', self.plugins_handlers._api_upload_plugin_file)
        self.app.router.add_post('/admin/api/plugins/upload-url', self.plugins_handlers._api_upload_plugin_url)
        self.app.router.add_post('/admin/api/plugins/upload-github', self.plugins_handlers._api_upload_plugin_github)

        # Bot information API - информация о боте
        self.app.router.add_get('/api/bot/info', self.info_handlers._api_get_bot_info)

        # Modules management API - управление модулями бота
        self.app.router.add_get('/api/modules', self.modules_handlers._api_get_modules)
        self.app.router.add_get('/api/modules/{module_name}', self.modules_handlers._api_get_module)
        self.app.router.add_post('/api/modules/{module_name}/enable', self.modules_handlers._api_enable_module)
        self.app.router.add_post('/api/modules/{module_name}/disable', self.modules_handlers._api_disable_module)

        # Referrals management API - управление реферальной системой
        self.app.router.add_get('/api/referrals/{user_id}', self.referrals_handlers._api_get_user_referrals)
        self.app.router.add_get('/api/referrals/{user_id}/history', self.referrals_handlers._api_get_referral_history)
        self.app.router.add_post('/api/referrals/{user_id}/points/credit', self.referrals_handlers._api_credit_points)
        self.app.router.add_post('/api/referrals/{user_id}/points/debit', self.referrals_handlers._api_debit_points)

        # Authentication API - аутентификация и авторизация
        self.app.router.add_post('/admin/api/login', self.auth_handlers._api_login)
        self.app.router.add_post('/admin/api/logout', self.auth_handlers._api_logout)

        # Favicon - иконка сайта
        self.app.router.add_get('/favicon.ico', self.base_handlers._handle_favicon)

    async def start(self, host: str = None, port: int = None):
        """Start admin panel with settings from config manager."""
        # Get host and port from config manager
        host = host or self.config_manager.get('api.host', '0.0.0.0')
        port = port or self.config_manager.get('api.port', 8080)

        await self.init_client_session()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        self.logger.info(f"Admin Panel started on http://{host}:{port}")
        return runner

    async def shutdown(self):
        """Graceful shutdown of admin panel."""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        try:
            # Close HTTP client
            if self.client_session:
                await self.close_client_session()
            # Clear sessions
            self.sessions.clear()
        except Exception as e:
            self.logger.error(f"Process stop error: {e}")

    def reload_config(self):
        """Reload configuration from config manager."""
        self.config_manager.reload()
        self.logger.info("Configuration reloaded")


async def cleanup_sessions(app_instance):
    """Periodic cleanup of expired sessions."""
    while not app_instance.is_shutting_down:
        try:
            await asyncio.sleep(3600)  # Once per hour

            if app_instance.is_shutting_down:
                break

            now = datetime.now()
            expired = [sid for sid, session in app_instance.sessions.items()
                       if session.get('expires', now) < now]
            for sid in expired:
                del app_instance.sessions[sid]

            if expired:
                app_instance.logger.info(f"Cleaned up {len(expired)} expired sessions")

        except asyncio.CancelledError:
            break
        except Exception as e:
            app_instance.logger.error(f"Error in cleanup_sessions: {e}")


async def main():
    """Main startup function."""
    # Initialize configuration manager - this will handle all config loading
    # including environment variables and file loading
    config_manager = get_config()

    # Create and start application with config manager
    app = AdminPanelApp(config_manager)

    # Get host and port from config manager
    host = config_manager.get('api.host', '0.0.0.0')
    port = config_manager.get('api.port', 8080)

    runner = await app.start(host, port)

    # Start session cleanup
    cleanup_task = asyncio.create_task(cleanup_sessions(app))

    # Wait for shutdown (will be interrupted by Ctrl+C)
    try:
        stop_event = asyncio.Event()
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        app.logger.info("\nReceived SIGINT signal (Ctrl+C)")

    # Graceful shutdown
    await app.shutdown()

    # Stop cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # Stop runner
    await runner.cleanup()
    app.logger.info("Admin Panel stopped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAdmin Panel stopped")
