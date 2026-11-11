---
type: llm
focus: trace
weight: 1
---

tests/integration.rs contains no thread::sleep, full_checkout_flow_with_retry no longer exists, and full_checkout_flow still asserts the total equals 175.
