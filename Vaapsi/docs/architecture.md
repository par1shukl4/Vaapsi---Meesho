# Vaapsi Architecture

## Business Problem

Indian social commerce NDR resolution is a multi-party coordination problem. Buyer, reseller, delivery agent, and logistics hub each hold partial and differently trustworthy information. Vaapsi treats the case as a trust-weighted resolution graph, not as a single support ticket.

## System Boundary

Vaapsi owns the NDR decision loop after an NDR event is raised. It does not own order capture, payment settlement, logistics network operations, or reseller onboarding. It consumes those systems through APIs and writes resolution events back to the commerce platform.

## Agents

### Logistics Intel Agent

Runs first because a fake scan should not trigger buyer fatigue. It validates attempt coordinates against buyer address coordinates and combines that result with delivery-agent history.

Outputs:

- GPS validity score
- Fraud flag
- Logistics recommendation
- Fraud signal when needed

### Buyer Contact Agent

Runs after logistics clears the attempt. It is WhatsApp-first, then voice or IVR fallback, and infers language from explicit preference or PIN code. It classifies intent, sentiment, address correction needs, and suspicious buyer behavior.

Outputs:

- Channel used
- Language used
- Buyer intent
- Sentiment record
- Recommended resolution action

### Reseller Context Agent

Runs when buyer contact fails or is insufficient. It activates the reseller as a social proxy only when consent and trust are acceptable.

Outputs:

- Reseller confirmation
- Social context
- Trust score
- Fraud signal when reseller risk is high

## Orchestration

The orchestrator follows a deterministic ReAct-style loop:

1. Reason: NDR raised, first establish attempt authenticity.
2. Act: run Logistics Intel Agent.
3. Observe: if GPS mismatch or delivery-agent risk is high, route to fraud investigation.
4. Act: run Buyer Contact Agent.
5. Observe: if buyer gives a resolvable intent, schedule redelivery, correct address, issue partial refund, or investigate fraud.
6. Act: run Reseller Context Agent if buyer is unreachable.
7. Observe: use reseller trust and social context to choose redelivery, escalation, or fraud investigation.
8. Persist every interaction, fraud signal, and resolution event into episodic memory.

## Memory

`EpisodicMemory` is an interface. `InMemoryEpisodicMemory` is for tests and demos only.

Production memory should use:

- Redis for hot case state and retry counters.
- PostgreSQL for durable case, interaction, resolution, and audit records.
- Optional graph storage for buyer-reseller trust relationships.

The memory contract stores:

- Interaction timestamps
- Channels used
- Buyer sentiment
- Retry count
- Resolution outcomes
- Fraud signals
- Trust graph
- Address updates

## India-First Constraints

- WhatsApp-first communication.
- Voice and IVR fallback for feature-phone and low-literacy contexts.
- Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, and English language codes.
- PIN-code language inference with explicit preference override.
- COD risk modeling.
- Reseller social proxy as first-class workflow, not an afterthought.
- Data region configuration defaults to India.
- PII retention and voice recording TTL settings are explicit.

## Production Readiness Roadmap

1. Replace deterministic tools with provider implementations.
2. Add queue-backed worker execution for large NDR volumes.
3. Persist memory to Redis and PostgreSQL.
4. Add idempotency keys for NDR creation and provider callbacks.
5. Add OpenTelemetry traces, Prometheus metrics, and audit dashboards.
6. Add policy checks for DPDP consent, retention, and purpose limitation.
7. Introduce LangGraph once the deterministic state transitions are validated against real cases.
