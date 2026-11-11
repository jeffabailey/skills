//! A tiny shopping-cart calculator.

#[derive(Debug, PartialEq)]
pub enum QtyError {
    Empty,
    NotANumber,
    Zero,
}

/// Parses a quantity string. Quantities must be positive integers.
pub fn parse_qty(s: &str) -> Result<u32, QtyError> {
    let s = s.trim();
    if s.is_empty() {
        return Err(QtyError::Empty);
    }
    let n: u32 = s.parse().map_err(|_| QtyError::NotANumber)?;
    if n == 0 {
        return Err(QtyError::Zero);
    }
    Ok(n)
}

/// Applies a percentage discount. Percentages above 100 are clamped to 100.
pub fn apply_discount(price_cents: u64, pct: u8) -> u64 {
    let pct = if pct > 100 { 100 } else { pct as u64 };
    price_cents - price_cents * pct / 100
}

#[derive(Debug, Default)]
pub struct Cart {
    items: Vec<(String, u64, u32)>,
}

impl Cart {
    pub fn new() -> Self {
        Cart { items: Vec::new() }
    }

    pub fn add(&mut self, name: &str, price_cents: u64, qty: u32) {
        if let Some(item) = self.items.iter_mut().find(|i| i.0 == name) {
            item.2 += qty;
        } else {
            self.items.push((name.to_string(), price_cents, qty));
        }
    }

    pub fn remove(&mut self, name: &str) -> bool {
        let before = self.items.len();
        self.items.retain(|i| i.0 != name);
        self.items.len() != before
    }

    pub fn total(&self) -> u64 {
        self.items.iter().map(|i| i.1 * i.2 as u64).sum()
    }

    pub fn line_count(&self) -> usize {
        self.items.len()
    }

    #[doc(hidden)]
    pub fn raw_items(&self) -> &Vec<(String, u64, u32)> {
        &self.items
    }
}

/// Old rounding helper from the v0 pricing engine. Nothing calls it.
#[allow(dead_code)]
fn legacy_round(cents: u64) -> u64 {
    if cents % 100 >= 50 {
        cents + (100 - cents % 100)
    } else {
        cents - cents % 100
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_qty_one() {
        assert_eq!(parse_qty("1"), Ok(1));
    }

    #[test]
    fn parse_qty_two() {
        assert_eq!(parse_qty("2"), Ok(2));
    }

    #[test]
    fn parse_qty_three() {
        assert_eq!(parse_qty("3"), Ok(3));
    }

    #[test]
    fn parse_qty_forty_two() {
        assert_eq!(parse_qty("42"), Ok(42));
    }

    #[test]
    fn parse_qty_works() {
        assert!(parse_qty("7").is_ok());
    }

    #[test]
    fn parse_qty_rejects_zero() {
        assert_eq!(parse_qty("0"), Err(QtyError::Zero));
    }

    #[test]
    fn parse_qty_rejects_empty() {
        assert_eq!(parse_qty("   "), Err(QtyError::Empty));
    }

    #[test]
    fn parse_qty_bad_input_errors() {
        assert!(parse_qty("abc").is_err());
    }

    #[test]
    fn discount_half() {
        assert_eq!(apply_discount(1000, 50), 500);
    }

    #[test]
    fn discount_fifty_percent() {
        let price = 1000;
        let pct = 50;
        let result = apply_discount(price, pct);
        assert_eq!(result, 500);
    }

    #[test]
    fn discount_runs() {
        let _ = apply_discount(999, 10);
    }

    #[test]
    fn cart_total() {
        let mut cart = Cart::new();
        cart.add("apple", 50, 2);
        cart.add("pear", 75, 1);
        assert_eq!(cart.total(), 175);
    }

    #[test]
    fn cart_total_again() {
        let mut cart = Cart::new();
        cart.add("apple", 50, 2);
        cart.add("pear", 75, 1);
        assert_eq!(cart.total(), 175);
    }

    #[test]
    fn cart_add_merges_same_item() {
        let mut cart = Cart::new();
        cart.add("apple", 50, 2);
        cart.add("pear", 75, 1);
        cart.add("apple", 50, 3);
        assert_eq!(cart.line_count(), 2);
        assert_eq!(cart.total(), 325);
    }

    #[test]
    fn cart_internal_vec_layout() {
        let mut cart = Cart::new();
        cart.add("apple", 50, 2);
        cart.add("pear", 75, 1);
        let raw = cart.raw_items();
        assert_eq!(raw[0], ("apple".to_string(), 50, 2));
        assert_eq!(raw[1], ("pear".to_string(), 75, 1));
        assert_eq!(raw.capacity() >= 2, true);
    }

    #[test]
    fn cart_remove_existing() {
        let mut cart = Cart::new();
        cart.add("apple", 50, 2);
        cart.add("pear", 75, 1);
        assert!(cart.remove("apple"));
        assert_eq!(cart.total(), 75);
    }
}
