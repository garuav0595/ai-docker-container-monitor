# AI Agent for Docker Container Monitoring

A practical AI agent that monitors and manages Docker containers using **natural language** — no CLI, no manual `docker ps`/`docker stats`. Ask it to check a container's health or analyze its logs, and it gives you a plain-English verdict instead of raw output.

> 📖 Full write-up: [Built an AI Agent for Docker Container Monitoring](https://www.linkedin.com/pulse/built-ai-agent-docker-container-monitoring-gaurav-khatri-cqzac/) by **Gaurav Khatri**

## What it does

- Checks container health & resource usage
- Analyzes logs automatically
- Detects anomalies — memory spikes, DB failures, and more
- Restarts unhealthy containers on demand
- Works entirely through conversational queries

**Health check example:**

```
> check health demo-nginx
demo-nginx: running | Memory: 8MB
```

**Log analysis example** — raw logs in:

```
[WARN]  High memory usage: 84%
[ERROR] Connection timeout to database
[WARN]  High memory usage: 94%
[ERROR] Connection timeout to database
[WARN]  High memory usage: 98%
```

What the agent gives back:

```
✅ Multiple high memory spikes detected (80%+)
✅ Repeated database connection timeouts
⚠️  Memory pressure likely causing DB instability
🔁 Recommendation: Restart container & check DB connection pool
```

## Two implementations

| Version | Execution model | Best for |
|---|---|---|
| **Simple** | Direct execution | Lightweight, fast, perfect for prototyping |
| **Temporal** | Durable workflows with automatic retries | Fault-tolerant, production-ready reliability |

The core AI agent logic is identical in both — only the execution layer changes: `Simple → Validate → Swap orchestration → Scale`, with zero rewrites.

## `monitor.py` — the foundation

[`monitor.py`](./monitor.py) in this repo is the clean, minimal Docker monitor everything else is built on — pure Python, no AI, no AWS, just Docker commands via the `docker-py` SDK: list/health/logs/restart/stop/start/inspect/stats/images/prune/exec.

```bash
pip install docker
python3 monitor.py
```

Get this working first, understand the foundation, then layer in AI (AWS Bedrock) and durable orchestration (Temporal) on top.

## Tech stack

- Python
- Docker SDK (`docker-py`)
- Temporal (durable workflow orchestration)
- AWS Bedrock (the AI layer)

## Takeaway

AI agents don't have to be chatbots — they can be real operational tools embedded inside DevOps workflows, replacing manual commands and turning raw system noise into actionable decisions. Build simple, validate fast, then scale smart.

---

**Author:** [Gaurav Khatri](https://www.linkedin.com/in/gaurav-khatri-devops/) — DevOps Engineer @ Sarv.com | Kubernetes (EKS), Docker, GitOps & CI/CD
