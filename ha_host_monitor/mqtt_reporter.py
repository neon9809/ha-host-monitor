"""
MQTT Discovery reporter for Home Assistant.
Sends metrics via MQTT Discovery protocol with unique_id support.
"""

import json
import logging
import socket
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTReporter:
    """Handles MQTT Discovery reporting to Home Assistant."""

    def __init__(self, config: Dict[str, Any], entity_prefix: str):
        """
        Initialize MQTT reporter.

        Args:
            config: MQTT configuration dictionary
            entity_prefix: Prefix for entity IDs (e.g., "server1_monitor")
        """
        self.config = config
        self.entity_prefix = entity_prefix
        self.client = None
        self.connected = False
        self.discovery_prefix = config.get("discovery_prefix", "homeassistant")
        
        # Generate client ID if not provided
        client_id = config.get("client_id", "")
        if not client_id:
            hostname = socket.gethostname()
            client_id = f"ha_host_monitor_{hostname}"
        
        self.client_id = client_id
        self._discovered_sensors = set()  # Track which sensors have been discovered

    def connect(self) -> bool:
        """
        Connect to MQTT broker.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Set username and password if provided
            username = self.config.get("username", "")
            password = self.config.get("password", "")
            if username:
                self.client.username_pw_set(username, password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            broker = self.config.get("broker", "localhost")
            port = self.config.get("port", 1883)
            
            logger.info(f"Connecting to MQTT broker at {broker}:{port}...")
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker: {rc}")

    def send_discovery(self, metric_name: str, unit: str = None, device_class: str = None, state_class: str = None):
        """
        Send MQTT Discovery message for a sensor.

        Args:
            metric_name: Name of the metric (e.g., "cpu_percent")
            unit: Unit of measurement (e.g., "%", "B")
            device_class: Home Assistant device class
            state_class: State class for the sensor (e.g., "measurement")
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping discovery")
            return

        # Generate unique_id and object_id
        unique_id = f"{self.entity_prefix}_{metric_name}"
        object_id = unique_id
        
        # Discovery topic
        discovery_topic = f"{self.discovery_prefix}/sensor/{object_id}/config"
        
        # State topic (where actual data will be sent)
        state_topic = f"{self.discovery_prefix}/sensor/{object_id}/state"
        
        # Build discovery payload
        payload = {
            "name": metric_name.replace("_", " ").title(),
            "unique_id": unique_id,
            "object_id": object_id,
            "state_topic": state_topic,
            "device": {
                "identifiers": [self.entity_prefix],
                "name": f"Host Monitor ({self.entity_prefix})",
                "manufacturer": "Manus AI",
                "model": "Host Monitor",
            },
        }
        
        # Add unit if provided
        if unit:
            payload["unit_of_measurement"] = unit
        
        # Add device class if provided
        if device_class:
            payload["device_class"] = device_class
        
        # Add state class if provided
        if state_class:
            payload["state_class"] = state_class
        
        # Send discovery message (with retain flag)
        try:
            result = self.client.publish(
                discovery_topic,
                json.dumps(payload),
                qos=1,
                retain=True
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self._discovered_sensors.add(metric_name)
                logger.debug(f"Sent discovery for {metric_name}")
            else:
                logger.error(f"Failed to send discovery for {metric_name}: {result.rc}")
        except Exception as e:
            logger.error(f"Error sending discovery for {metric_name}: {e}")

    def send_state(self, metric_name: str, value: Any, unit: str = None, device_class: str = None, state_class: str = None):
        """
        Send sensor state update.

        Args:
            metric_name: Name of the metric
            value: Sensor value
            unit: Unit of measurement
            device_class: Home Assistant device class
            state_class: State class for the sensor
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, skipping state update")
            return

        # Send discovery if not already sent
        if metric_name not in self._discovered_sensors:
            self.send_discovery(metric_name, unit, device_class, state_class)

        # Generate object_id
        unique_id = f"{self.entity_prefix}_{metric_name}"
        object_id = unique_id
        
        # State topic
        state_topic = f"{self.discovery_prefix}/sensor/{object_id}/state"
        
        # Send state update
        try:
            result = self.client.publish(
                state_topic,
                str(value),
                qos=0,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Sent state for {metric_name}: {value}")
            else:
                logger.error(f"Failed to send state for {metric_name}: {result.rc}")
        except Exception as e:
            logger.error(f"Error sending state for {metric_name}: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")

    def test_connection(self) -> bool:
        """
        Test MQTT broker connection.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.connect():
            return False
        
        # Wait a bit for connection to establish
        import time
        time.sleep(1)
        
        success = self.connected
        self.disconnect()
        return success
