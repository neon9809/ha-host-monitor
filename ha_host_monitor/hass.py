"""
Home Assistant API integration module.
Handles communication with Home Assistant REST API.
"""

import requests
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class HomeAssistantNotifier:
    """Handles communication with Home Assistant."""

    def __init__(
        self,
        url: str,
        token: str,
        verify_ssl: bool = True,
        timeout: int = 10,
    ):
        """Initialize Home Assistant notifier.

        Args:
            url: Home Assistant URL (e.g., http://localhost:8123)
            token: Long-lived access token
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to Home Assistant.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = self.session.get(
                urljoin(self.url, "/api/"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                logger.info("Successfully connected to Home Assistant")
                return True, None
            else:
                error = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to connect to Home Assistant: {error}")
                return False, error
        except requests.exceptions.RequestException as e:
            error = str(e)
            logger.error(f"Connection error: {error}")
            return False, error

    def update_sensor(
        self,
        entity_id: str,
        state: Any,
        attributes: Optional[Dict[str, Any]] = None,
        unit_of_measurement: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Update a sensor state in Home Assistant.

        Args:
            entity_id: Entity ID (e.g., sensor.host_monitor_cpu_percent)
            state: New state value
            attributes: Additional attributes
            unit_of_measurement: Unit of measurement

        Returns:
            Tuple of (success, error_message)
        """
        if attributes is None:
            attributes = {}

        # Add unit of measurement if provided
        if unit_of_measurement:
            attributes["unit_of_measurement"] = unit_of_measurement

        # Add friendly name
        if "friendly_name" not in attributes:
            friendly_name = entity_id.split(".")[-1].replace("_", " ").title()
            attributes["friendly_name"] = friendly_name

        payload = {
            "state": state,
            "attributes": attributes,
        }

        try:
            response = self.session.post(
                urljoin(self.url, f"/api/states/{entity_id}"),
                json=payload,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

            if response.status_code in [200, 201]:
                logger.debug(f"Successfully updated {entity_id} to {state}")
                return True, None
            else:
                error = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to update {entity_id}: {error}")
                return False, error

        except requests.exceptions.RequestException as e:
            error = str(e)
            logger.error(f"Error updating {entity_id}: {error}")
            return False, error

    def update_multiple_sensors(
        self, updates: Dict[str, Dict[str, Any]]
    ) -> Dict[str, tuple[bool, Optional[str]]]:
        """Update multiple sensors at once.

        Args:
            updates: Dictionary mapping entity_id to update data
                    Each update data should have 'state' and optionally 'attributes'

        Returns:
            Dictionary mapping entity_id to (success, error_message) tuples
        """
        results = {}
        for entity_id, data in updates.items():
            state = data.get("state")
            attributes = data.get("attributes", {})
            unit = data.get("unit_of_measurement")
            results[entity_id] = self.update_sensor(
                entity_id, state, attributes, unit
            )
        return results

    def get_sensor_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a sensor.

        Args:
            entity_id: Entity ID

        Returns:
            State dictionary or None if failed
        """
        try:
            response = self.session.get(
                urljoin(self.url, f"/api/states/{entity_id}"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get state for {entity_id}: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting state for {entity_id}: {e}")
            return None

    def close(self) -> None:
        """Close the session."""
        self.session.close()
