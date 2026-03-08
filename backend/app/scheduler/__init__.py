"""
Scheduler & Orchestration module.

Provides APScheduler-based job scheduling for pipeline runs and the central
Orchestrator that coordinates the full pipeline execution (source resolution,
parallel agents, finding persistence, snapshots, digest generation, and email).
"""

# Scheduler & Orchestration
