"""
Configuration management module for HA Host Monitor.
Handles loading, validation, and default configuration generation.
"""

import os
import socket
import yaml
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation."""

    DEFAULT_CONFIG = {
        "home_assistant": {
            "url": "http://localhost:8123",
            "token": "",
            "verify_ssl": True,
        },
        "update_frequency": 60,  # seconds
        "host_identifier": "auto",  # "auto" to use hostname, or specify custom name
        "metrics": {
            "cpu_percent": {
                "enabled": True,
                "frequency": 60,
            },
            "cpu_count": {
                "enabled": True,
                "frequency": 300,
            },
            "memory_percent": {
                "enabled": True,
                "frequency": 60,
            },
            "memory_available": {
                "enabled": True,
                "frequency": 60,
            },
            "disk_usage": {
                "enabled": True,
                "frequency": 300,
                "path": "/",
            },
            "network_io": {
                "enabled": True,
                "frequency": 60,
            },
            "load_average": {
                "enabled": True,
                "frequency": 60,
            },
            "uptime": {
                "enabled": True,
                "frequency": 300,
            },
            "boot_time": {
                "enabled": True,
                "frequency": 3600,
            },
            "process_count": {
                "enabled": True,
                "frequency": 60,
            },
            "cpu_temp": {
                "enabled": False,
                "frequency": 60,
            },
        },
    }

    def __init__(self, config_dir: str = "/app/config"):
        """Initialize configuration manager.

        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yml"
        self.error_log = self.config_dir / "error.log"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.

        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            logger.info(f"Loading configuration from {self.config_file}")
            try:
                with open(self.config_file, "r") as f:
                    config = yaml.safe_load(f)
                    if config is None:
                        config = {}
                    # Merge with defaults to ensure all keys exist
                    config = self._merge_configs(self.DEFAULT_CONFIG, config)
                    # Resolve host identifier
                    config = self._resolve_host_identifier(config)
                    return config
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                self._write_error_log(f"Config loading error: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info(f"Config file not found at {self.config_file}, creating default")
            self._create_default_config()
            return self.DEFAULT_CONFIG.copy()

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False)
            logger.info(f"Default configuration created at {self.config_file}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
            self._write_error_log(f"Failed to create default config: {e}")

    def _get_hostname(self) -> str:
        """Get the hostname of the system.

        Returns:
            Sanitized hostname suitable for use in entity IDs
        """
        try:
            # Try to get hostname from environment variable first (Docker container name)
            hostname = os.environ.get('HOSTNAME', '')
            
            if not hostname:
                # Fall back to socket.gethostname()
                hostname = socket.gethostname()
            
            # Sanitize hostname for use in entity IDs
            # Replace invalid characters with underscores
            hostname = re.sub(r'[^a-z0-9_]', '_', hostname.lower())
            
            # Remove leading/trailing underscores
            hostname = hostname.strip('_')
            
            # If hostname is empty after sanitization, use default
            if not hostname:
                hostname = "host"
            
            logger.info(f"Detected hostname: {hostname}")
            return hostname
            
        except Exception as e:
            logger.warning(f"Failed to get hostname: {e}, using default 'host'")
            return "host"

    def _resolve_host_identifier(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve host identifier to actual hostname if set to 'auto'.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with resolved host_identifier
        """
        host_id = config.get("host_identifier", "auto")
        
        if host_id == "auto":
            # Auto-detect hostname
            hostname = self._get_hostname()
            config["entity_prefix"] = f"{hostname}_monitor"
            logger.info(f"Auto-detected entity prefix: {config['entity_prefix']}")
        else:
            # Use custom identifier
            # Sanitize custom identifier
            sanitized = re.sub(r'[^a-z0-9_]', '_', host_id.lower())
            sanitized = sanitized.strip('_')
            config["entity_prefix"] = f"{sanitized}_monitor"
            logger.info(f"Using custom entity prefix: {config['entity_prefix']}")
        
        return config

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not config.get("home_assistant", {}).get("url"):
            return False, "Missing home_assistant.url"

        if not config.get("home_assistant", {}).get("token"):
            return False, "Missing home_assistant.token"

        # Validate update frequency
        if not isinstance(config.get("update_frequency", 60), (int, float)):
            return False, "update_frequency must be a number"

        if config.get("update_frequency", 60) < 5:
            return False, "update_frequency must be at least 5 seconds"

        return True, None

    def _merge_configs(
        self, default: Dict[str, Any], custom: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge custom config with defaults.

        Args:
            default: Default configuration
            custom: Custom configuration

        Returns:
            Merged configuration
        """
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _write_error_log(self, message: str) -> None:
        """Write error message to error log file.

        Args:
            message: Error message to log
        """
        try:
            with open(self.error_log, "a") as f:
                from datetime import datetime

                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")

    def get_error_log_path(self) -> Path:
        """Get path to error log file.

        Returns:
            Path to error log file
        """
        return self.error_log
