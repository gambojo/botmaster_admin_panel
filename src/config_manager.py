import os
import logging
import yaml
import sys
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env в окружение
load_dotenv('config/.env')


class AdminPanelConfigManager:
    ENV_MAPPINGS: List[Tuple[str, List[str], type]] = [
        # API settings
        ('API_URL', ['api', 'url'], str),
        ('API_KEY', ['api', 'key'], str),
        ('API_HOST', ['api', 'host'], str),
        ('API_PORT', ['api', 'port'], int),

        # Auth basic settings
        ('AUTH_BASIC_ENABLE', ['auth', 'basic', 'enable'], lambda x: x.lower() in ('true', '1', 'yes')),
        ('AUTH_BASIC_ADMIN_USERNAME', ['auth', 'basic', 'admin_username'], str),
        ('AUTH_BASIC_ADMIN_PASSWORD', ['auth', 'basic', 'admin_password'], str),

        # Auth CORS settings
        ('AUTH_CORS_ENABLE', ['auth', 'cors', 'enable'], lambda x: x.lower() in ('true', '1', 'yes')),
        ('AUTH_CORS_ALLOWED_ORIGINS', ['auth', 'cors', 'allowed_origins'], lambda x: [i.strip() for i in x.split(',')]),
        ('AUTH_CORS_ALLOWED_METHODS', ['auth', 'cors', 'allowed_methods'], lambda x: [i.strip() for i in x.split(',')]),
        ('AUTH_CORS_ALLOWED_HEADERS', ['auth', 'cors', 'allowed_headers'], lambda x: [i.strip() for i in x.split(',')]),

        # Standard log settings
        ('LOG_STANDARD_LEVEL', ['logging', 'standard_log', 'level'], str),
        ('LOG_STANDARD_CONSOLE', ['logging', 'standard_log', 'console'], lambda x: x.lower() in ('true', '1', 'yes')),
        ('LOG_STANDARD_FILE', ['logging', 'standard_log', 'file'], str),
        ('LOG_STANDARD_FORMAT', ['logging', 'standard_log', 'format'], str),
        ('LOG_STANDARD_MAX_SIZE', ['logging', 'standard_log', 'max_size'], int),

        # Audit log settings
        ('LOG_AUDIT_ENABLE', ['logging', 'audit_log', 'enable'], lambda x: x.lower() in ('true', '1', 'yes')),
        ('LOG_AUDIT_CONSOLE', ['logging', 'audit_log', 'console'], lambda x: x.lower() in ('true', '1', 'yes')),
        ('LOG_AUDIT_FILE', ['logging', 'audit_log', 'file'], str),
        ('LOG_AUDIT_FORMAT', ['logging', 'audit_log', 'format'], str),
        ('LOG_AUDIT_MAX_SIZE', ['logging', 'audit_log', 'max_size'], int),

        # AIOHTTP access log settings
        ('LOG_AIOHTTP_DISABLE', ['logging', 'aiohttp_access_log', 'disable'],
         lambda x: x.lower() in ('true', '1', 'yes')),
    ]

    def __init__(self, config_path: str = "config/config.yml"):
        self.config_path = config_path
        # self.logger = self._setup_config_logger()
        # Setup centralized logging BEFORE creating logger

        self.logger = logging.getLogger(self.__class__.__name__)
        self._config: Dict[str, Any] = self._get_default_config()
        self._load_yaml_config()
        self._override_from_env()

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    def _load_yaml_config(self):
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f) or {}
                    self._merge_config(self._config, yaml_config)
                    self.logger.info(f"Loaded config from {self.config_path}")
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error loading config YAML: {e}")

    def _merge_config(self, base: Dict, override: Dict):
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _override_from_env(self):
        overridden = 0
        for env_var, path, converter in self.ENV_MAPPINGS:
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted = converter(value)
                    self._set_nested_value(self._config, path, converted)
                    overridden += 1
                    self.logger.debug(f"ENV override: {env_var} → {'.'.join(path)} = {converted}")
                except Exception as e:
                    self.logger.error(f"ENV conversion error for {env_var}: {e}")
        if overridden:
            self.logger.info(f"Overridden {overridden} values from environment")

    def _set_nested_value(self, config: Dict, path: List[str], value: Any):
        current = config
        for key in path[:-1]:
            current = current.setdefault(key, {})
        current[path[-1]] = value

    def _get_default_config(self) -> Dict:
        return {
            'api': {
                'url': 'http://localhost:8081',
                'key': '',
                'host': '0.0.0.0',
                'port': 8080
            },
            'auth': {
                'basic': {
                    'enable': True,
                    'admin_username': 'admin',
                    'admin_password': 'admin'
                },
                'cors': {
                    'enable': True,
                    'allowed_origins': [],
                    'allowed_methods': [],
                    'allowed_headers': []
                }
            },
            'logging': {
                'standard_log': {
                    'level': 'INFO',
                    'console': True,
                    'file': 'logs/admin_panel.log',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'max_size': 10485760
                },
                'audit_log': {
                    'enable': True,
                    'console': False,
                    'file': 'logs/audit.log',
                    'format': '%(asctime)s - %(name)s - AUDIT - %(message)s',
                    'max_size': 10485760
                },
                'aiohttp_access_log': {
                    'disable': True
                }
            }
        }

    def get(self, key: str = None, default: Any = None) -> Any:
        if key is None:
            return self._config
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_nested(self, *keys, default: Any = None) -> Any:
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def reload(self):
        self._config = self._get_default_config()
        self._load_yaml_config()
        self._override_from_env()
        self.logger.info("Configuration reloaded")


_config_instance: Optional[AdminPanelConfigManager] = None


def get_config(config_path: str = "config/config.yml", reload: bool = False) -> AdminPanelConfigManager:
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = AdminPanelConfigManager(config_path)
    return _config_instance
