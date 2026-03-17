class DashboardError(Exception):
    """Base exception for all UR Dashboard client errors."""


class DashboardCommunicationError(DashboardError):
    """Raised when connection or communication with the robot fails."""


class DashboardProtocolError(DashboardError):
    """Raised when the dashboard server behaves unexpectedly."""


class DashboardCommandRejected(DashboardError):
    """Raised when the robot rejects an action command."""

    def __init__(self, command: str, raw_response: str):
        self.command = command
        self.raw_response = raw_response
        super().__init__(
            f"Command rejected: {command!r} -> {raw_response!r}"
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"command={self.command!r}, "
            f"raw_response={self.raw_response!r})"
        )
