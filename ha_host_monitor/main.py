"""
Main application entry point.
Orchestrates the monitoring loop and Home Assistant integration.
"""

import time
import logging
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from .config import ConfigManager
from .collector import MetricsCollector
from .hass import HomeAssistantNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HostMonitor:
    """Main application class for host monitoring."""

    def __init__(self, config_dir: str = "/app/config"):
        """Initialize the host monitor.

        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = config_dir
        self.config_manager = ConfigManager(config_dir)
        self.running = True
        self.last_update_time: Dict[str, float] = {}

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def initialize(self) -> bool:
        """Initialize the monitor.

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("Initializing HA Host Monitor...")

        # Load configuration
        self.config = self.config_manager.load_config()

        # Validate configuration
        is_valid, error = self.config_manager.validate_config(self.config)
        if not is_valid:
            logger.error(f"Configuration validation failed: {error}")
            self.config_manager._write_error_log(f"Config validation error: {error}")
            return False

        # Initialize collector
        self.collector = MetricsCollector(procfs_path="/host/proc")

        # Initialize Home Assistant notifier
        ha_config = self.config.get("home_assistant", {})
        self.notifier = HomeAssistantNotifier(
            url=ha_config.get("url"),
            token=ha_config.get("token"),
            verify_ssl=ha_config.get("verify_ssl", True),
        )

        # Test Home Assistant connection
        success, error = self.notifier.test_connection()
        if not success:
            logger.error(f"Failed to connect to Home Assistant: {error}")
            self.config_manager._write_error_log(
                f"Home Assistant connection failed: {error}"
            )
            return False

        logger.info("HA Host Monitor initialized successfully")
        return True

    def run_startup_tests(self) -> None:
        """Run tests on all metrics during startup.

        This helps identify which metrics are available on the system.
        """
        logger.info("Running startup metric tests...")
        print("\n" + "=" * 60)
        print("STARTUP METRIC TEST RESULTS")
        print("=" * 60)

        test_results = self.collector.test_all_metrics()

        error_messages = []
        for metric_name, result in test_results.items():
            status = result["status"]
            if status == "success":
                print(f"✓ {metric_name}: OK")
            elif status == "no_data":
                print(f"⚠ {metric_name}: No data returned")
                error_messages.append(f"{metric_name}: No data returned")
            else:
                print(f"✗ {metric_name}: FAILED - {result['error']}")
                error_messages.append(f"{metric_name}: {result['error']}")

        print("=" * 60 + "\n")

        # Write error messages to error log
        if error_messages:
            logger.warning(f"Some metrics failed during startup test")
            for msg in error_messages:
                self.config_manager._write_error_log(f"Startup test - {msg}")

    def should_update_metric(self, metric_name: str) -> bool:
        """Check if a metric should be updated based on its frequency.

        Args:
            metric_name: Name of the metric

        Returns:
            True if metric should be updated, False otherwise
        """
        current_time = time.time()
        last_update = self.last_update_time.get(metric_name, 0)

        # Get metric frequency from config
        metric_config = self.config.get("metrics", {}).get(metric_name, {})
        frequency = metric_config.get("frequency", self.config.get("update_frequency", 60))

        if current_time - last_update >= frequency:
            self.last_update_time[metric_name] = current_time
            return True

        return False

    def run_monitoring_loop(self) -> None:
        """Run the main monitoring loop."""
        logger.info("Starting monitoring loop...")

        while self.running:
            try:
                # Get enabled metrics from config
                metrics_config = self.config.get("metrics", {})
                entity_prefix = self.config.get("entity_prefix", "host_monitor")

                updates = {}

                for metric_name, metric_config in metrics_config.items():
                    # Skip disabled metrics
                    if not metric_config.get("enabled", False):
                        continue

                    # Check if it's time to update this metric
                    if not self.should_update_metric(metric_name):
                        continue

                    # Collect the metric
                    value = self.collector.collect_metric(metric_name)

                    if value is None:
                        logger.warning(f"Failed to collect metric: {metric_name}")
                        self.config_manager._write_error_log(
                            f"Failed to collect metric: {metric_name}"
                        )
                        continue

                    # Prepare entity ID and attributes
                    entity_id = f"sensor.{entity_prefix}_{metric_name}"
                    attributes = {"last_updated": datetime.now().isoformat()}

                    # Add unit of measurement based on metric type
                    unit = self._get_unit_for_metric(metric_name)

                    # Handle different metric types
                    if isinstance(value, dict):
                        # For dict values, convert to JSON string and add details to attributes
                        state = str(value)
                        attributes.update(value)
                    else:
                        state = value

                    updates[entity_id] = {
                        "state": state,
                        "attributes": attributes,
                        "unit_of_measurement": unit,
                    }

                # Update all sensors in Home Assistant
                if updates:
                    results = self.notifier.update_multiple_sensors(updates)

                    # Log any failures
                    for entity_id, (success, error) in results.items():
                        if not success:
                            logger.error(f"Failed to update {entity_id}: {error}")
                            self.config_manager._write_error_log(
                                f"Failed to update {entity_id}: {error}"
                            )

                # Sleep before next iteration
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.config_manager._write_error_log(f"Monitoring loop error: {e}")
                time.sleep(5)  # Sleep longer on error

    def _get_unit_for_metric(self, metric_name: str) -> Optional[str]:
        """Get unit of measurement for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Unit of measurement or None
        """
        units = {
            "cpu_percent": "%",
            "cpu_count": "cores",
            "memory_percent": "%",
            "memory_available": "B",
            "disk_usage": "%",
            "network_io": "B",
            "load_average": "load",
            "uptime": "s",
            "process_count": "processes",
        }
        return units.get(metric_name)

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code
        """
        try:
            # Initialize
            if not self.initialize():
                return 1

            # Run startup tests
            self.run_startup_tests()

            # Run monitoring loop
            self.run_monitoring_loop()

            return 0

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.config_manager._write_error_log(f"Fatal error: {e}")
            return 1

        finally:
            # Cleanup
            if hasattr(self, "notifier"):
                self.notifier.close()


def main():
    """Entry point for the application."""
    monitor = HostMonitor()
    sys.exit(monitor.run())


if __name__ == "__main__":
    main()
