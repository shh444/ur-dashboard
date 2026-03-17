"""
UR Dashboard — Universal Robots Dashboard Server 제어 패키지.

    from ur_dashboard import SyncDashboard

    ur = SyncDashboard("192.168.1.101")
    ur.seq_full_boot("/programs/main.urp")
    ur.close()
"""

from .sync_dashboard import SyncDashboard
from .async_dashboard import AsyncDashboard
from .exceptions import (
    DashboardError,
    DashboardCommunicationError,
    DashboardCommandRejected,
    DashboardProtocolError,
)

__all__ = [
    "SyncDashboard",
    "AsyncDashboard",
    "DashboardError",
    "DashboardCommunicationError",
    "DashboardCommandRejected",
    "DashboardProtocolError",
]

__version__ = "1.0.0"
