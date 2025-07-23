"""Dashboard modules for virtuoso gem hunter."""

from .dashboard_utils import create_dashboard
from .dashboard_styled import create_futuristic_dashboard
from .web_dashboard import VirtuosoWebDashboard

__all__ = [
    'create_dashboard',
    'create_futuristic_dashboard',
    'VirtuosoWebDashboard'
]
# Enhanced features available
# - Real-time alerts
# - Raydium V3 tracking
# - Performance metrics
# - Rich token metadata
