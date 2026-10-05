# 🤖 RATISS LABS AGENT

A RATISS Labs agent **assembled** from existing open-source building blocks, MCP first. Nothing is built from scratch.

📄 Reference architecture: the `agentmd.txt` brief (control plane / execution plane, Tool / Skill / MCP Server kept separate, Policy ALLOW / DENY / REQUIRE_APPROVAL, hashed provenance).

> **Status: census completed (campaign of 02/10/2026).** No code. The assembly will be done with GLM following `MONTAGE.md`.

## 📂 Content
| File | Role |
|---|---|
| **`MONTAGE.md`** | ⭐ **The assembly workflow**: 12 steps, each with its building blocks, its assembly and its pass check |
| `CATALOGUE.md` | 84 verified repositories, classified by component, plus the list of discarded and renamed repositories |
| `COMPATIBILITE.md` | Technical sheet and matrix of the junctions, with the source of each claim (README / DOC / DEDUCED) |
| `VERSIONS.md` | Exact versions of the V1 stack (Python 3.12, Node ≥ 22.19) |
| `LICENCES.md` | Licenses read in the LICENSE files and their consequences |
| `SOURCES.md` | Method and web sources of the campaign |
| `LIENS.csv` | Data in machine format |

## 🧩 V1 stack retained

| Brief building block | Repository |
|---|---|
| UI | Open WebUI (test bench), then assistant-ui |
| Runtime (router, planner, executor, approvals) | LangGraph + deepagents + `langchain.mcp` |
| Model Gateway | LiteLLM (+ Ollama) |
| MCP Gateway + registry | IBM ContextForge (virtual server "ratiss-v1") |
| MCP Admission | Cisco mcp-scanner (offline) + MCP Inspector + hash in `tools.yaml` |
| Policy | OPA, called by the runtime before each tool |
| MCP tools | filesystem, git, github, playwright, jupyter, arxiv, postgres; cyber: mcp-security-hub |
| Sandboxes | llm-sandbox + gVisor, playwright-mcp, browser-use |
| Memory | PostgreSQL + pgvector + LangGraph checkpoints |
| Verification | **RATISS-Framework** (SHA-256, journal, run manifest) |
| Skills | SKILL.md format + K-Dense, Cybersecurity-Skills, diagram-design (10 to 20 skills in V1) |
| Object storage | RustFS |

## 🗺️ Roadmap (brief)
0. Contract: Tool / Skill / Task / Event / Run / Policy schemas.
1. Core.
2. Execution.
3. Memory.
4. RATISS verification.
5. Skills.
6. UI.
7. Industrialization.

## 🚫 Out of V1 (brief §46)
Multi-agent swarm, 1000 tools, Kubernetes, distributed inference, mobile application, voice.

---
RATISS Labs — Jonathan
