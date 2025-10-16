# AGENTS.md — Codex Node Development (ComfyUI)

**Motto:**

> “Small, clear, safe steps — always grounded in real data and reproducible code.”

---

## 🧭 Principles

* Prefer **clarity over cleverness**; explicit schemas over implicit behaviors.
* Each node = **one clear purpose**; no shared mutable state.
* Keep changes **minimal, reviewable, and reversible**.
* Avoid new dependencies unless explicitly declared under `docs/requirements/`.
* Follow ComfyUI’s **V3 schema** (`io.Schema`, `io.NodeOutput`) for all new nodes.
* Always align with the official **Comfy-Org/docs**.

---

## 🧩 Agent Overview

| Agent             | Role/Backend          | Description                                                                                                                              |
| :---------------- | :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `codex-nodegen`   | MCP context7 / serena | Generates and maintains ComfyUI nodes via Codex. Reads feature specs under `docs/requirements/`, outputs V3-schema node files under `nodes/`. |
| `codex-docsync`   | same                  | Keeps documentation (README, schema tables) synchronized with node code. Parses schema metadata and updates Markdown automatically.          |
| `codex-validator` | same                  | Lints & validates node files for schema compliance and API safety. Runs pre-commit validation via `codex validate nodes`.                  |

---

## 📚 Knowledge & Libraries

* Use `context7` MCP server to fetch and verify the latest docs before generation.
* **Primary reference:**
    * → **Comfy-Org/docs (GitHub)** — Official source for ComfyUI architecture, custom-node guides, and V3 schema specifications.
* Key directories to consult within that repo:
    * `development/overview` – Core development model & update cadence
    * `custom-nodes/overview` – Node design & registration
    * `core-concepts/dependencies` – Dependency and environment isolation
* Import API stably:

    ```python
    from comfy_api.latest import ComfyExtension, io
    ```

* Before emitting code, resolve dependencies:
    * `resolve-library-id` → `get-library-docs`
* For uncertain behavior or ambiguous specs, **pause and request human confirmation**.

---

## ⚙️ Workflow

1.  **Plan**
    * Write each node specification under `docs/requirements/feature-*.md`.
    * Define: purpose, inputs/outputs, constraints, and category (e.g., `ImpactPack/Operation`).
2.  **Generate**
    * Command:

        ```bash
        codex generate node --from docs/requirements/feature-example.md
        ```

    * Codex outputs:
        * `nodes/<NodeName>_v3.py`
        * (optional) `docs/generated/<NodeName>.md`
3.  **Verify**
    * Ensure:
        * `define_schema()` exists
        * Input/Output types match docs
        * No unsafe imports (`os`, `subprocess`, etc.)
        * Category and description align with requirement file
4.  **Implement & Test**
    * Load node in ComfyUI (portable build).
    * Validate UI, input ports, runtime behavior, and caching logic.
    * If mismatched, adjust `requirements/*.md` and regenerate.
5.  **Reflect**
    * After testing, Codex appends an ADR entry (`docs/adr/YYYY-MM-DD-node-change.md`) summarizing the decision and schema version.

---

## 🧱 Code Style & Limits

* **≤ 300 LOC** per node. One class = one logical unit.
* Always include a **docstring** summarizing:
    * What it does
    * Inputs/outputs
    * Key assumptions
* Use consistent `CATEGORY` taxonomy (e.g., `ImpactPack/Operation`).
* Keep nodes **deterministic**; avoid external side effects.
* If multiple constants are reused, move them to `config.py`.
* Prefer **pure, functional style**; avoid shared state or mutation.

---

## 🤝 Collaboration & Accountability

* **Escalate** before committing if:
    * Requirements are ambiguous.
    * Node impacts shared runtime or backend APIs.
    * UX / schema contracts could break compatibility.
* Communicate when confidence **< 80%**—**honesty > speed**.
* Follow “fail-safe” principle: unverified behavior must default to **no-op**.

---

## ✅ Quick Checklist

**Plan → Generate → Verify → Test → Docs → Reflect**

Before merging:

* Feature spec exists (`docs/requirements/*.md`)
* Code passes V3 schema validation
* Inputs/outputs match spec
* Category consistent
* ADR auto-generated
* No side-effects or unsafe imports

---

## 🧩 Environment Setup (Note)

MCP / Codex servers (e.g., `context7`, `serena`) are configured **locally** via TOML.
This repository does **not** include any machine-specific configuration or trusted path.
Refer to your local `~/.codex/config.toml` for environment setup.


## 💬 Note
- If multiple Codex agents are used (generation, validation, documentation sync), each must read AGENTS.md as its behavioral contract — no hidden logic.
- Docs define behavior; Codex enforces it.