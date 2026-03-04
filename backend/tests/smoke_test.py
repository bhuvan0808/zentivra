"""Quick smoke test for the Zentivra API."""
import httpx

base = "http://127.0.0.1:8000/api"

# Test health
r = httpx.get("http://127.0.0.1:8000/health")
print(f"GET /health: {r.status_code} -> {r.json()}")

# Test sources list (should have pre-seeded sources from agents.yaml)
r = httpx.get(f"{base}/sources/")
sources = r.json()
print(f"GET /sources: {r.status_code}, count={len(sources)}")
if sources:
    for s in sources[:3]:
        print(f"  - {s['name']} ({s['agent_type']})")

# Test findings (empty)
r = httpx.get(f"{base}/findings/")
print(f"GET /findings: {r.status_code}, count={len(r.json())}")

# Test runs (empty)
r = httpx.get(f"{base}/runs/")
print(f"GET /runs: {r.status_code}, count={len(r.json())}")

# Test digests (empty)
r = httpx.get(f"{base}/digests/")
print(f"GET /digests: {r.status_code}, count={len(r.json())}")

# Test stats
r = httpx.get(f"{base}/findings/stats")
print(f"GET /findings/stats: {r.status_code} -> {r.json()}")

# Test manual run trigger
r = httpx.post(f"{base}/runs/trigger")
print(f"POST /runs/trigger: {r.status_code} -> {r.json()}")

print("\n✅ All endpoints responding!")
