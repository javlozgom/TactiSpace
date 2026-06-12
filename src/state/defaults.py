from __future__ import annotations

from src.state import keys
from src.ui.navigation_config import MATCH_OVERVIEW_VIEW

SESSION_DEFAULTS = {
    keys.ACTIVE_VIEW: MATCH_OVERVIEW_VIEW,
    keys.PLAYER_FILTER: "Todos",
    keys.TEAM_FILTER: "Todos",
    keys.MATCH_FILTER: "Todos",
    keys.FILTERS_APPLIED: False,
}
