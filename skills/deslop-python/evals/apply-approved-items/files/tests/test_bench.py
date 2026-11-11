from cartcalc.core import Cart


def test_cart_total_speed(benchmark):
    cart = Cart()
    for i in range(500):
        cart.add(f"sku{i}", 10, 1)
    benchmark(cart.total)
