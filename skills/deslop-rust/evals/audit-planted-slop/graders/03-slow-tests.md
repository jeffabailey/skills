---
type: llm
focus: trace
weight: 1
---

The report flags full_checkout_flow and full_checkout_flow_with_retry in tests/integration.rs as slow because of thread::sleep, citing measured times of roughly 1.5 seconds each.
