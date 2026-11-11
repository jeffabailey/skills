---
type: llm
focus: trace
weight: 1
---

The report flags test_full_checkout_flow and test_full_checkout_flow_with_retry in tests/test_integration.py as slow because of time.sleep, citing measured times of roughly 1.5 seconds each.
