---
type: llm
focus: trace
weight: 1
---

The five test_parse_qty_one/two/three/forty_two/works tests are replaced by fewer tests (for example one pytest.mark.parametrize test) that still assert the exact return value for each of the inputs "1", "2", "3", " 42 " and "7".
