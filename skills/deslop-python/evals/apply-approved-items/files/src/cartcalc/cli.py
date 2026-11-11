"""Command-line front end."""
import sys

from cartcalc.core import Cart, parse_qty


def main(argv: list[str]) -> int:
    cart = Cart()
    for arg in argv:
        sku, cents, qty = arg.split(":")
        cart.add(sku, int(cents), parse_qty(qty))
    print(cart.total())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
