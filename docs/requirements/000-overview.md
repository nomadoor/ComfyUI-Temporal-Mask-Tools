# 000 Overview — Temporal Mask Node Requirements

> This document defines global standards and coding rules for all temporal mask processing nodes.
> Each node specification is located in the same directory as a numbered Markdown file (e.g., `001-*.md`).


## 🔧 General Standards
- Comply with [Comfy-Org/docs](https://github.com/Comfy-Org/docs)  
- All nodes use **V3 schema** (`io.Schema`, `io.NodeOutput`)
- Output files to `nodes/`
- ≤ 300 LOC per node
- No unsafe imports (`os`, `subprocess`, `sys`)
- Deterministic, stateless operation
- Include `category`, `display_name`, and docstring

---

## 🧠 Common I/O Specifications
| Type | Shape | Description |
|------|--------|-------------|
| MASK | (N, H, W) or (H, W) | Boolean or 0–1 tensor |
| IMAGE | (N, H, W, C) | RGB float tensor |
| BOOL/INT/FLOAT | scalar | Parameters for configuration |

---

## 🧩 Coding Guidelines
- Use `torch` ops over NumPy
- GPU supported (`.to(device)`)
- Refrain from writing to disk
- Each node should have `execute()` only
- Avoid shared global states

---

## 🧪 Validation Checklist
- [ ] V3 schema compliant  
- [ ] Inputs / Outputs match docs  
- [ ] Unsafe imports absent  
- [ ] Proper docstring and category  
- [ ] Passes test cases under `tests/nodes/`  
- [ ] ADR entry updated on spec change  
