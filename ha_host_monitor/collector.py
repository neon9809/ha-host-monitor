"""
System metrics collector module.
Collects various Linux system metrics using psutil.
"""

import os
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects system metrics from the host."""

    def __init__(self, procfs_path: str = "/proc"):
        """Initialize metrics collector.

        Args:
            procfs_path: Path to /proc filesystem (for Docker containers)
        """
        self.procfs_path = procfs_path
        # Set psutil to use the provided procfs path
        if procfs_path != "/proc":
            psutil.PROCFS_PATH = procfs_path
            logger.info(f"Using custom procfs path: {procfs_path}")

    def get_cpu_percent(self) -> Optional[float]:
        """Get CPU usage percentage.

        Returns:
            CPU usage percentage (0-100) or None if failed
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Error getting CPU percent: {e}")
            return None

    def get_cpu_count(self) -> Optional[int]:
        """Get number of CPU cores.

        Returns:
            Number of logical CPU cores or None if failed
        """
        try:
            return psutil.cpu_count(logical=True)
        except Exception as e:
            logger.error(f"Error getting CPU count: {e}")
            return None

    def get_memory_percent(self) -> Optional[float]:
        """Get memory usage percentage.

        Returns:
            Memory usage percentage (0-100) or None if failed
        """
        try:
            return psutil.virtual_memory().percent
        except Exception as e:
            logger.error(f"Error getting memory percent: {e}")
            return None

    def get_memory_available(self) -> Optional[int]:
        """Get available memory in bytes.

        Returns:
            Available memory in bytes or None if failed
        """
        try:
            return psutil.virtual_memory().available
        except Exception as e:
            logger.error(f"Error getting available memory: {e}")
            return None

    def get_memory_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed memory information.

        Returns:
            Dictionary with memory info or None if failed
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.free,
                "percent": mem.percent,
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return None

    def get_disk_usage(self, path: str = "/") -> Optional[Dict[str, Any]]:
        """Get disk usage for specified path.

        Args:
            path: Path to check disk usage for

        Returns:
            Dictionary with disk usage info or None if failed
        """
        try:
            disk = psutil.disk_usage(path)
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            }
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return None

    def get_network_io(self) -> Optional[Dict[str, Any]]:
        """Get network I/O statistics.

        Returns:
            Dictionary with network I/O info or None if failed
        """
        try:
            net = psutil.net_io_counters()
            return {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
                "packets_sent": net.packets_sent,
                "packets_recv": net.packets_recv,
                "errin": net.errin,
                "errout": net.errout,
                "dropin": net.dropin,
                "dropout": net.dropout,
            }
        except Exception as e:
            logger.error(f"Error getting network I/O: {e}")
            return None

    def get_load_average(self) -> Optional[Dict[str, float]]:
        """Get system load average.

        Returns:
            Dictionary with load averages (1, 5, 15 min) or None if failed
        """
        try:
            load = os.getloadavg()
            return {
                "load_1min": load[0],
                "load_5min": load[1],
                "load_15min": load[2],
            }
        except Exception as e:
            logger.error(f"Error getting load average: {e}")
            return None

    def get_uptime(self) -> Optional[int]:
        """Get system uptime in seconds.

        Returns:
            System uptime in seconds or None if failed
        """
        try:
            boot_time = psutil.boot_time()
            uptime = datetime.now().timestamp() - boot_time
            return int(uptime)
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return None

    def get_boot_time(self) -> Optional[str]:
        """Get system boot time.

        Returns:
            System boot time as ISO format string or None if failed
        """
        try:
            boot_time = psutil.boot_time()
            return datetime.fromtimestamp(boot_time).isoformat()
        except Exception as e:
            logger.error(f"Error getting boot time: {e}")
            return None

    def get_process_count(self) -> Optional[int]:
        """Get number of running processes.

        Returns:
            Number of running processes or None if failed
        """
        try:
            return len(psutil.pids())
        except Exception as e:
            logger.error(f"Error getting process count: {e}")
            return None

    def get_cpu_temp(self) -> Optional[Dict[str, Any]]:
        """Get CPU temperature.

        Returns:
            Dictionary with CPU temperature info or None if failed
        """
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                logger.warning("No temperature sensors found")
                return None

            result = {}
            for name, entries in temps.items():
                result[name] = []
                for entry in entries:
                    result[name].append(
                        {
                            "label": entry.label or "unknown",
                            "current": entry.current,
                            "high": entry.high,
                            "critical": entry.critical,
                        }
                    )
            return result if result else None
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
            return None

    def test_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Test all available metrics and report which ones work.

        Returns:
            Dictionary with test results for each metric
        """
        results = {}

        metrics = {
            "cpu_percent": self.get_cpu_percent,
            "cpu_count": self.get_cpu_count,
            "memory_percent": self.get_memory_percent,
            "memory_available": self.get_memory_available,
            "memory_info": self.get_memory_info,
            "disk_usage": lambda: self.get_disk_usage("/"),
            "network_io": self.get_network_io,
            "load_average": self.get_load_average,
            "uptime": self.get_uptime,
            "boot_time": self.get_boot_time,
            "process_count": self.get_process_count,
            "cpu_temp": self.get_cpu_temp,
        }

        for metric_name, metric_func in metrics.items():
            try:
                result = metric_func()
                results[metric_name] = {
                    "status": "success" if result is not None else "no_data",
                    "value": result,
                    "error": None,
                }
                logger.info(f"Metric {metric_name}: OK")
            except Exception as e:
                results[metric_name] = {
                    "status": "error",
                    "value": None,
                    "error": str(e),
                }
                logger.error(f"Metric {metric_name}: FAILED - {e}")

        return results

    def collect_metric(self, metric_name: str) -> Optional[Any]:
        """Collect a specific metric by name.

        Args:
            metric_name: Name of the metric to collect

        Returns:
            Metric value or None if failed
        """
        metrics = {
            "cpu_percent": self.get_cpu_percent,
            "cpu_count": self.get_cpu_count,
            "memory_percent": self.get_memory_percent,
            "memory_available": self.get_memory_available,
            "memory_info": self.get_memory_info,
            "disk_usage": lambda: self.get_disk_usage("/"),
            "network_io": self.get_network_io,
            "load_average": self.get_load_average,
            "uptime": self.get_uptime,
            "boot_time": self.get_boot_time,
            "process_count": self.get_process_count,
            "cpu_temp": self.get_cpu_temp,
        }

        if metric_name not in metrics:
            logger.warning(f"Unknown metric: {metric_name}")
            return None

        try:
            return metrics[metric_name]()
        except Exception as e:
            logger.error(f"Error collecting metric {metric_name}: {e}")
            return None
