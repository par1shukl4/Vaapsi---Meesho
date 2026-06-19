# Vaapsi

Vaapsi is a production-oriented multi-agent backend for resolving Non-Delivery Reports (NDRs) and Return-to-Origin risk in Indian social commerce.

The platform coordinates three specialist agents:

- Buyer Contact Agent: WhatsApp-first and voice-first buyer outreach, language inference, address correction, redelivery scheduling, sentiment, and buyer-side fraud signals.
- Reseller Context Agent: reseller social-context activation, trust scoring, and reseller risk evaluation.
- Logistics Intel Agent: delivery-attempt authenticity checks using GPS, timestamps, address geocoding, and delivery-agent history.

A central orchestrator runs a ReAct-style planning loop over shared case state and writes every observation to episodic memory.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## API Surface

- `POST /ndr/create`
- `POST /agent/logistics`
- `POST /agent/buyer`
- `POST /agent/reseller`
- `POST /resolution`
- `GET /case/{id}`
- `GET /history/{id}`
- `POST /memory/update`

## Production Integration Points

Provider interfaces live under `backend/tools`. The default implementation is deterministic and safe for local demos. Real deployments should bind those interfaces to WhatsApp Business API, Sarvam AI, Twilio or Exotel, OpenStreetMap, Google Maps Distance Matrix, Redis, PostgreSQL, and queue-backed worker execution.
