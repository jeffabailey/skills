import time

from cartcalc.cli import main


def test_full_checkout_flow(capsys):
    time.sleep(1.5)  # wait for the pricing service
    assert main(["apple:50:2", "pear:75:1"]) == 0
    assert capsys.readouterr().out.strip() == "175"


def test_full_checkout_flow_with_retry(capsys):
    for _ in range(3):
        time.sleep(0.5)  # retry backoff
    main(["apple:50:2", "pear:75:1"])
    assert int(capsys.readouterr().out.strip()) > 0


def test_remove_missing_item_returns_false():
    from cartcalc.core import Cart
    cart = Cart()
    cart.add("apple", 50, 1)
    assert cart.remove("kiwi") is False
