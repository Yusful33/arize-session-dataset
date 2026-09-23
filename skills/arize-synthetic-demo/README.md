# arize-synthetic-demo

An agent skill that turns a few parameters into a fully-wired Arize synthetic-data demo — `generator.py` + `generator.ipynb` + `requirements.txt` + `.env.example` — and optionally runs it end-to-end (venv, install, trace send, eval log) when credentials are supplied.

Built on top of the patterns in [`synthetic-data`](https://github.com/camyoung93/arize-workshops/tree/main/synthetic-data) (Cam's workshop repo), distilled into a reusable recipe so any SA can spin up a company-specific demo in minutes.

## What it generates

Each invocation produces a self-contained demo directory containing:

```
<output_dir>/
├── generator.py          # Python CLI (default: full pipeline steps 1–7)
├── generator.ipynb       # Same pipeline as a runnable notebook
├── requirements.txt      # arize>=7,<8 + OTel stack
├── .env.example          # Arize + optional gateway + Phoenix vars
├── agent_endpoint/       # Written on default run (config, body template, manifest)
└── README.md             # Auto-generated walkthrough
```

Default `python generator.py --count N` uploads traces, dataset, pre-baked experiments, Prompt Hub, and (when gateway env is set) a demo manifest for **Agent Experiments**. Use `--traces-only` to opt out of uploads.

Traces follow OpenInference conventions exactly — the same attributes Arize's instrumentors emit — so spans render properly in the Arize UI (span kinds, prompt templates, token counts, tool calls, guardrails, session grouping).

## How to invoke it

From Claude Code or the Cursor CLI, just reference the skill by name and hand it the parameters:

> *Create a custom demo for Globex Insurance — claims adjudication agent built on Bedrock/Claude, multi-agent coordinator, 100 traces. My space_id is …, api_key is …, project name globex_claims_demo. Use the arize-synthetic-demo skill.*

The skill will ask for anything missing, scaffold the demo, smoke-test it, then (if credentials are provided) send traces and evals live to Arize.

## Inputs

**Required**

- `company_name` — e.g. "Globex Insurance", "Acme Bank"
- `industry_or_use_case` — e.g. "claims adjudication", "fraud triage", "financial report summarization"
- `framework` — one of: `openai`, `anthropic`, `bedrock`, `vertex`, `adk`, `langchain`, `crewai`, `generic`
- `agent_architecture` — one of: `single_agent`, `multi_agent_coordinator`, `retrieval_pipeline` (RAG), `rag_rerank`, `guarded_rag`
- `num_traces` — how many traces to generate (e.g. 10, 100, 500)

**Optional (enables full auto-run)**

- `arize_space_id`
- `arize_api_key`
- `arize_project_name`

If credentials are supplied the skill installs deps, runs a smoke test, then the full batch with evals — end-to-end, no manual steps.

## Supported agent architectures

| Architecture | Span tree |
|---|---|
| `single_agent` | CHAIN → AGENT → (LLM \| TOOL)+ |
| `multi_agent_coordinator` | CHAIN → Coordinator AGENT → routing LLM → sub-AGENTs (Intake / Worker / Response), each with TOOLs |
| `retrieval_pipeline` (RAG) | CHAIN → AGENT → RETRIEVER → LLM |
| `rag_rerank` | CHAIN → AGENT → RETRIEVER → RERANKER → LLM |
| `guarded_rag` | CHAIN → AGENT → GUARDRAIL → RETRIEVER → LLM → GUARDRAIL |

## Supported LLM frameworks

OpenAI, Anthropic, AWS Bedrock, Google Vertex AI, Google ADK, LangChain / LangGraph, CrewAI, and a generic fallback. Each emits the correct `llm.model_name`, `llm.provider`, `llm.system`, region attributes, and span names so Arize identifies the provider automatically.

## Scenario coverage

Every generated demo includes a realistic mix across eight scenario types:

- `happy_path` — clean success
- `tool_failure` — tool errors + retry
- `guardrail_denial` — policy / fraud / PII block
- `ambiguity` — clarification request flow (resolved and abandoned variants)
- `execution_failure` — terminal tool failures
- `retry` — self-retry paths
- `poisoned_tokens` — cost-anomaly injection (~55–70k prompt tokens on a specific agent)
- `no_llm_needed` — informational short-circuit

Plus evals at span, trace, and session levels, logged via `arize.pandas.logger`.

## Agent Experiments (shared gateway)

Synthetic demos need a public HTTPS `/invoke` URL for **Datasets → Run against agent**. This skill ships a **shared Vercel gateway** — deploy once, register a manifest per demo.

**SAs:** copy `SYNTHETIC_AGENT_GATEWAY_URL` + `GATEWAY_API_KEY` from team 1Password, run the generator, paste `agent_endpoint/*.json` into **Agent Endpoints → New Remote Agent**. Full walkthrough: [`gateway/README.md`](gateway/README.md).

**Admins:** deploy `gateway/` once, connect Upstash Redis, publish credentials to 1Password. Same doc.

## Phoenix backend (optional)

Set **`TRACE_BACKEND=phoenix`** in demo `.env` to send traces and eval annotations to [Phoenix](https://arize.com/docs/phoenix) instead of Arize AX:

```bash
docker run -p 6006:6006 -p 4317:4317 -i -t phoenix
```

```bash
TRACE_BACKEND=phoenix
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_BASE_URL=http://localhost:6006
PHOENIX_PROJECT_NAME=<your_project>
```

With Phoenix, `python generator.py --count N` runs **traces + evals only**. Datasets, pre-baked experiments, Prompt Hub, and Agent Experiments require `TRACE_BACKEND=arize` and Arize credentials.

## Layout

```
arize-synthetic-demo/
├── SKILL.md                  # Agent entry point + workflow
├── references/
│   ├── approach.md           # 10-step recipe distilled from the workshop repo
│   ├── openinference.md      # Attribute cheat sheet per span kind
│   ├── frameworks.md         # Provider identifiers per framework
│   ├── architectures.md      # Span tree shapes per architecture
│   ├── scenarios.md          # Recipes for each scenario type
│   ├── evaluations.md        # Span / trace / session eval patterns
│   └── datasets-experiments.md  # Dataset grid + ax CLI
├── gateway/                  # Shared Vercel agent gateway (see gateway/README.md)
├── templates/
│   ├── generator_skeleton.py # Base Python scaffold
│   ├── requirements.txt
│   ├── env.example
│   └── snippets/
│       ├── single_agent.py.snippet
│       ├── multi_agent.py.snippet
│       ├── rag.py.snippet
│       ├── rag_rerank.py.snippet
│       └── guarded_rag.py.snippet
└── scripts/
    ├── make_notebook.py      # generator.py -> generator.ipynb
    └── run_demo.py           # venv + install + smoke + batch runner
```

## Using the skill

This skill lives at `.claude/skills/arize-synthetic-demo/` in the `solutions-resources` repo. Claude Code auto-loads it when launched from the repo root:

```bash
git clone https://github.com/Arize-ai/solutions-resources.git
cd solutions-resources
claude
```

Then invoke it via slash command or natural language:

```
/arize-synthetic-demo
```

or

> *Create a custom demo for Acme Corp — fraud triage agent on OpenAI, single agent, 100 traces. Use the arize-synthetic-demo skill.*

### Using outside the repo

To use the skill from anywhere on your machine (not just inside `solutions-resources`), run these from the root of a checked-out `solutions-resources` repo:

```bash
# From the solutions-resources repo root

# Claude Code — user-level skills
cp -R .claude/skills/arize-synthetic-demo ~/.claude/skills/

# Cursor CLI
cp -R .claude/skills/arize-synthetic-demo ~/.cursor/skills/
```

## Dependencies on the generated demo

The generated `requirements.txt` pins:

```
arize>=7,<8      # required for arize.pandas.logger eval logging
arize-otel
opentelemetry-api
opentelemetry-sdk
openinference-semantic-conventions
python-dotenv
pandas
packaging        # transitive dep of arize.pandas.logger not always pulled in automatically
```

## Examples produced with this skill

- **Globex Insurance — claims adjudication** — multi-agent coordinator on Bedrock/Claude, 100 traces
- **FINRA — financial report summarization** — single-LLM-call on Bedrock/Claude, 10 traces

Both demos land fully-evaluated traces in Arize (span / trace / session evals) with the correct provider attributes, cost-anomaly traces, prompt-template A/B variants, and session groupings.
