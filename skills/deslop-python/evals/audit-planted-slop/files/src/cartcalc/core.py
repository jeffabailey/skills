"""Pricing and cart logic. Must not import cartcalc.cli."""
import os
from dataclasses import dataclass, field


def parse_qty(text: str) -> int:
    """Parse a positive item quantity."""
    value = int(text.strip())
    if value <= 0:
        raise ValueError(f"quantity must be positive: {text!r}")
    return value


def apply_discount(cents: int, pct: int) -> int:
    """Return cents after a percentage discount, clamped to 0..100 percent."""
    if pct > 100:
        pct = 100
    if pct < 0:
        pct = 0
    return cents - cents * pct // 100


@dataclass
class Cart:
    _items: list = field(default_factory=list)

    def add(self, sku: str, cents: int, qty: int) -> None:
        for item in self._items:
            if item[0] == sku:
                item[2] += qty
                return
        self._items.append([sku, cents, qty])

    def remove(self, sku: str) -> bool:
        for i, item in enumerate(self._items):
            if item[0] == sku:
                del self._items[i]
                return True
        return False

    def total(self) -> int:
        return sum(cents * qty for _, cents, qty in self._items)

    def line_count(self) -> int:
        return len(self._items)


def legacy_round(cents: int, mode: str) -> int:
    """Old rounding helper, replaced by integer cents. Nothing calls it."""
    if mode == "up":
        return ((cents + 99) // 100) * 100
    elif mode == "down":
        return (cents // 100) * 100
    elif mode == "half":
        rem = cents % 100
        if rem >= 50:
            return cents - rem + 100
        else:
            return cents - rem
    else:
        return cents
