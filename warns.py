# -*- coding: utf-8 -*-
# warns.py \u2014 Warn System
# Alle Warn-Verwaltung l\u00E4uft \u00FCber das Dashboard (dashboard.py)
# Diese Datei bleibt f\u00FCr zuk\u00FCnftige Erweiterungen erhalten

from config import *
from economy_helpers import (
    load_warns, save_warns, get_user_warns,
    load_team_warns, save_team_warns, get_user_team_warns
)
