"""Weapon definitions. Each weapon uses its own ammo type (same key).

The pistol is the starter weapon with effectively infinite ammo. Other
weapons are unlocked by picking up their ammo (dropped by enemies / found in
buildings).
"""

WEAPONS = {
    "pistol":  {"name": "\u041f\u0438\u0441\u0442\u043e\u043b\u0435\u0442", "ammo": "pistol",  "damage": 16, "fire_rate": 0.30, "pellets": 1, "spread": 2.0,  "bullet_speed": 720,  "infinite": True},
    "smg":     {"name": "\u0410\u0432\u0442\u043e\u043c\u0430\u0442",  "ammo": "smg",     "damage": 11, "fire_rate": 0.09, "pellets": 1, "spread": 7.0,  "bullet_speed": 800},
    "shotgun": {"name": "\u0414\u0440\u043e\u0431\u043e\u0432\u0438\u043a", "ammo": "shotgun", "damage": 9,  "fire_rate": 0.75, "pellets": 8, "spread": 24.0, "bullet_speed": 680},
    "rifle":   {"name": "\u0412\u0438\u043d\u0442\u043e\u0432\u043a\u0430", "ammo": "rifle",   "damage": 46, "fire_rate": 0.50, "pellets": 1, "spread": 1.0,  "bullet_speed": 1050},
}

# Display order / slot order
WEAPON_ORDER = ["pistol", "smg", "shotgun", "rifle"]

# Friendly ammo names for UI / pickups
AMMO_NAMES = {
    "pistol":  "\u041f\u0430\u0442\u0440\u043e\u043d\u044b 9\u043c\u043c",
    "smg":     "\u041f\u0430\u0442\u0440\u043e\u043d\u044b \u0410\u041a",
    "shotgun": "\u0414\u0440\u043e\u0431\u044c",
    "rifle":   "\u0412\u0438\u043d\u0442. \u043f\u0430\u0442\u0440\u043e\u043d\u044b",
}
