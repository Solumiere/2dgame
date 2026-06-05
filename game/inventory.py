"""Player inventory: weapons, ammo per type, and loot items."""
from .weapon import WEAPONS, WEAPON_ORDER

LOOT_KINDS = ["\u0410\u043f\u0442\u0435\u0447\u043a\u0430", "\u0415\u0434\u0430", "\u041c\u043e\u043d\u0435\u0442\u044b", "\u041a\u043b\u044e\u0447"]


class Inventory:
    def __init__(self):
        self.weapons = ["pistol"]
        self.ammo = {"pistol": -1, "smg": 0, "shotgun": 0, "rifle": 0}  # -1 = infinite
        self.loot = {k: 0 for k in LOOT_KINDS}
        self.current = 0

    def current_weapon(self):
        self.current = max(0, min(self.current, len(self.weapons) - 1))
        return self.weapons[self.current]

    def select(self, index):
        if 0 <= index < len(self.weapons):
            self.current = index

    def cycle(self, direction):
        if self.weapons:
            self.current = (self.current + direction) % len(self.weapons)

    def select_pistol(self):
        if "pistol" in self.weapons:
            self.current = self.weapons.index("pistol")

    def has_ammo(self, wkey):
        if WEAPONS[wkey].get("infinite"):
            return True
        return self.ammo.get(wkey, 0) > 0

    def consume(self, wkey):
        if not WEAPONS[wkey].get("infinite"):
            self.ammo[wkey] = max(0, self.ammo.get(wkey, 0) - 1)

    def add_ammo(self, atype, amount):
        if atype not in WEAPONS:
            return
        self.ammo[atype] = self.ammo.get(atype, 0) + amount
        if atype not in self.weapons:
            self.weapons.append(atype)
            # keep slots in canonical order
            self.weapons.sort(key=lambda w: WEAPON_ORDER.index(w))

    def add_loot(self, name, amount=1):
        self.loot[name] = self.loot.get(name, 0) + amount
