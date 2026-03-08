"""
API Routes Package
==================
Exports the central API router and all sub-routers for the Zentivra backend.

All routes are mounted under the /api prefix. Sub-routers include:
- /api/auth - Authentication (signup, login, logout, me)
- /api/sources - Data source CRUD
- /api/runs - Run configuration CRUD and trigger execution
- /api/run-triggers - Trigger details, findings, snapshots, execution logs
- /api/findings - Intelligence findings list and stats
- /api/digests - Digest list, latest, HTML/PDF download
- /api/dashboard - KPI, charts, triggers, sources (progressive tile loading)
- /api/config - Orchestrator configuration
- /api/workflows - One-off analysis workflows (e.g. disruptive article report)
"""
