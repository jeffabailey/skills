use cartcalc::{parse_qty, Cart};
use std::thread;
use std::time::Duration;

fn checkout(lines: &[(&str, u64, &str)]) -> u64 {
    let mut cart = Cart::new();
    for (name, price, qty) in lines {
        cart.add(name, *price, parse_qty(qty).unwrap());
    }
    cart.total()
}

#[test]
fn full_checkout_flow() {
    // Simulates network latency to the pricing service (there is no pricing service).
    thread::sleep(Duration::from_millis(1500));
    let total = checkout(&[("apple", 50, "2"), ("pear", 75, "1")]);
    assert_eq!(total, 175);
}

#[test]
fn full_checkout_flow_with_retry() {
    for _ in 0..3 {
        thread::sleep(Duration::from_millis(500));
    }
    let total = checkout(&[("apple", 50, "2"), ("pear", 75, "1")]);
    assert!(total > 0);
}

#[test]
fn remove_missing_item_returns_false() {
    let mut cart = Cart::new();
    cart.add("apple", 50, 1);
    assert!(!cart.remove("banana"));
    assert_eq!(cart.total(), 50);
}
