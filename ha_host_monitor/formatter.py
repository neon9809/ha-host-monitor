"""
Data formatting utilities for HA Host Monitor.
"""

from typing import Any, Dict, Optional


class DataFormatter:
    """Format metric values according to configuration."""

    # Unit conversion factors (to bytes)
    UNIT_FACTORS = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialize formatter with configuration.

        Args:
            config: Configuration dictionary containing formatting options
        """
        formatting = config.get("formatting", {})
        self.disk_unit = formatting.get("disk_unit", "GB")
        self.memory_unit = formatting.get("memory_unit", "GB")
        self.network_unit = formatting.get("network_unit", "MB")
        self.decimal_places = formatting.get("decimal_places", 2)

    def convert_bytes(self, value: float, target_unit: str) -> float:
        """Convert bytes to target unit.

        Args:
            value: Value in bytes
            target_unit: Target unit (B, KB, MB, GB, TB)

        Returns:
            Converted value
        """
        if target_unit not in self.UNIT_FACTORS:
            raise ValueError(f"Invalid unit: {target_unit}")

        factor = self.UNIT_FACTORS[target_unit]
        return value / factor

    def format_value(self, value: Any, decimal_places: Optional[int] = None) -> Any:
        """Format a value with specified decimal places.

        Args:
            value: Value to format
            decimal_places: Number of decimal places (uses config default if None)

        Returns:
            Formatted value
        """
        if decimal_places is None:
            decimal_places = self.decimal_places

        if isinstance(value, float):
            return round(value, decimal_places)
        return value

    def format_disk_usage(self, disk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format disk usage data.

        Args:
            disk_data: Dictionary with total, used, free, percent keys

        Returns:
            Formatted disk usage dictionary
        """
        result = {}
        for key, value in disk_data.items():
            if key == "percent":
                result[key] = self.format_value(value)
            else:  # total, used, free (in bytes)
                converted = self.convert_bytes(value, self.disk_unit)
                result[key] = self.format_value(converted)
        return result

    def format_memory(self, value: float) -> float:
        """Format memory value from bytes to configured unit.

        Args:
            value: Memory value in bytes

        Returns:
            Formatted memory value
        """
        converted = self.convert_bytes(value, self.memory_unit)
        return self.format_value(converted)

    def format_network_io(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format network I/O data.

        Args:
            network_data: Dictionary with network statistics

        Returns:
            Formatted network I/O dictionary
        """
        result = {}
        for key, value in network_data.items():
            if key.startswith("bytes_"):
                # Convert bytes to configured unit
                converted = self.convert_bytes(value, self.network_unit)
                result[key] = self.format_value(converted)
            else:
                # Keep other values as-is (packets, errors)
                result[key] = value
        return result

    def format_load_average(self, load_data: Dict[str, float]) -> Dict[str, float]:
        """Format load average data.

        Args:
            load_data: Dictionary with load_1min, load_5min, load_15min

        Returns:
            Formatted load average dictionary
        """
        return {key: self.format_value(value) for key, value in load_data.items()}

    def get_unit_for_metric(self, metric_name: str, sub_key: Optional[str] = None) -> Optional[str]:
        """Get the unit for a metric.

        Args:
            metric_name: Name of the metric
            sub_key: Sub-key for dict metrics (e.g., "total" for disk_usage)

        Returns:
            Unit string or None
        """
        if metric_name == "disk_usage":
            if sub_key == "percent":
                return "%"
            return self.disk_unit
        elif metric_name == "memory_available":
            return self.memory_unit
        elif metric_name == "network_io":
            if sub_key and sub_key.startswith("bytes_"):
                return self.network_unit
            elif sub_key and sub_key.startswith("packets_"):
                return "packets"
            elif sub_key:
                return "errors"
        elif metric_name == "memory_percent":
            return "%"
        elif metric_name == "cpu_percent":
            return "%"
        elif metric_name == "uptime":
            return "s"
        elif metric_name == "process_count":
            return "processes"
        elif metric_name == "cpu_count":
            return "cores"
        elif metric_name == "cpu_temp":
            return "°C"

        return None
