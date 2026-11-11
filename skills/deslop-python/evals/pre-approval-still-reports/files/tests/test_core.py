import pytest

from cartcalc.core import Cart, apply_discount, parse_qty


def test_parse_qty_one():
    assert parse_qty("1") == 1


def test_parse_qty_two():
    assert parse_qty("2") == 2


def test_parse_qty_three():
    assert parse_qty("3") == 3


def test_parse_qty_forty_two():
    assert parse_qty(" 42 ") == 42


def test_parse_qty_works():
    assert parse_qty("7") is not None


def test_parse_qty_rejects_zero():
    with pytest.raises(ValueError):
        parse_qty("0")


def test_parse_qty_bad_input_errors():
    with pytest.raises(Exception):
        parse_qty("abc")


def test_discount_half():
    assert apply_discount(1000, 50) == 500


def test_discount_fifty_percent():
    price = 1000
    pct = 50
    result = apply_discount(price, pct)
    expected = 500
    assert result == expected


def test_discount_runs():
    apply_discount(999, 10)


def test_parse_qty_rejects_zero():
    with pytest.raises(ValueError):
        parse_qty("-5")


def test_cart_total():
    cart = Cart()
    cart.add("apple", 50, 2)
    cart.add("pear", 75, 1)
    assert cart.total() == 175


def test_cart_total_again():
    cart = Cart()
    cart.add("apple", 50, 2)
    cart.add("pear", 75, 1)
    assert cart.total() == 175


def test_cart_add_merges_same_item():
    cart = Cart()
    cart.add("apple", 50, 2)
    cart.add("apple", 50, 3)
    assert cart.line_count() == 1
    assert cart.total() == 250


def test_cart_internal_list_layout():
    cart = Cart()
    cart.add("apple", 50, 2)
    cart.add("pear", 75, 1)
    assert cart._items[0] == ["apple", 50, 2]
    assert cart._items[1][0] == "pear"
    assert len(cart._items) == 2


def test_cart_remove_existing():
    cart = Cart()
    cart.add("apple", 50, 2)
    cart.add("pear", 75, 1)
    assert cart.remove("apple") is True
    assert cart.total() == 75
