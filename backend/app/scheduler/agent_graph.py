"""
LangGraph-based parallel agent execution graph.

Replaces asyncio.as_completed with a structured LangGraph StateGraph that:
1. Fans out to all agent nodes in parallel (one node per agent type)
2. Each agent node runs its full pipeline (discover -> fetch -> extract -> summarize)
3. Results are collected and merged into a single aggregate

This provides better observability, structured state, and deterministic execution.
"""

from __future__ import annotations

import asyncio
import operator
from typing import Annotated, Any, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.competitor_watcher import CompetitorWatcher
from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
from app.agents.model_provider_watcher import ModelProviderWatcher
from app.agents.research_scout import ResearchScout
from app.config import settings
from app.models.run import Run
from app.models.source import AgentType, Source
from app.utils.logger import logger

AGENT_MAP = {
    AgentType.COMPETITOR: CompetitorWatcher,
    AgentType.MODEL_PROVIDER: ModelProviderWatcher,
    AgentType.RESEARCH: ResearchScout,
    AgentType.HF_BENCHMARK: HFBenchmarkTracker,
}

# Sentinel empty result for failed / timed-out agents
_EMPTY_RESULT: dict = {
    "findings": [],
    "errors": [],
    "urls_attempted": 0,
    "urls_succeeded": 0,
}


# ── State definition using TypedDict with Annotated reducer ───────────────

from typing import TypedDict


class AgentGraphState(TypedDict):
    """State schema for the LangGraph agent execution graph.

    agent_results uses operator.add as reducer so parallel run_agent
    nodes can each append their results independently.
    """
    sources_by_type: dict[str, list]
    run_config: Any
    run_log: Any
    agent_results: Annotated[list, operator.add]


# ── Routing function (returns Send objects for parallel dispatch) ─────────

def route_to_agents(state: AgentGraphState) -> list[Send]:
    """Conditional edge from START: dispatch one Send per agent type.

    Each Send targets the 'run_agent' node with agent-specific payload.
    LangGraph executes all Send targets in parallel.
    """
    sources_by_type = state["sources_by_type"]
    sends = []

    for agent_type_str, sources in sources_by_type.items():
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            logger.warning("unknown_agent_type type=%s", agent_type_str)
            continue

        if agent_type not in AGENT_MAP:
            continue

        sends.append(
            Send(
                "run_agent",
                {
                    "agent_type_str": agent_type_str,
                    "sources": sources,
                    "run_config": state["run_config"],
                    "run_log": state.get("run_log"),
                    "agent_results": [],
                },
            )
        )

    if not sends:
        logger.warning("no_agents_to_dispatch")

    return sends


# ── Agent execution node ──────────────────────────────────────────────────

async def run_agent_node(state: dict) -> dict:
    """Execute a single agent with timeout, returning its results.

    Invoked once per agent type via Send(). Returns a dict with
    agent_results list (length 1) to be merged by the reducer.
    """
    agent_type_str = state["agent_type_str"]
    sources = state["sources"]
    run_config = state["run_config"]
    run_log = state.get("run_log")

    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        return {
            "agent_results": [(agent_type_str, _EMPTY_RESULT.copy(), RuntimeError(f"unknown type: {agent_type_str}"))]
        }

    agent_class = AGENT_MAP.get(agent_type)
    if not agent_class:
        return {
            "agent_results": [(agent_type_str, _EMPTY_RESULT.copy(), RuntimeError(f"no agent for: {agent_type_str}"))]
        }

    # Use per-run LLM provider if set on the Run config
    llm_provider = getattr(run_config, "llm_provider", None) if run_config else None
    agent = agent_class(llm_provider=llm_provider)
    agent_logger = run_log.for_agent(agent_type_str) if run_log else None
    timeout = max(0, int(settings.agent_timeout_seconds))

    logger.info("agent_start agent=%s sources=%d", agent_type_str, len(sources))
    if agent_logger:
        agent_logger.info("agent_start", step="pipeline", sources=len(sources))

    try:
        if timeout > 0:
            result = await asyncio.wait_for(
                agent.run(
                    sources=sources,
                    run_config=run_config,
                    run_logger=agent_logger,
                ),
                timeout=timeout,
            )
        else:
            result = await agent.run(
                sources=sources,
                run_config=run_config,
                run_logger=agent_logger,
            )

        logger.info(
            "agent_complete agent=%s findings=%d errors=%d",
            agent_type_str,
            len(result["findings"]),
            len(result["errors"]),
        )
        if agent_logger:
            agent_logger.info(
                "agent_complete",
                step="pipeline",
                findings=len(result["findings"]),
                errors=len(result["errors"]),
            )
        return {"agent_results": [(agent_type_str, result, None)]}

    except asyncio.TimeoutError:
        logger.error("agent_timeout agent=%s timeout=%ds", agent_type_str, timeout)
        if agent_logger:
            agent_logger.error("agent_timeout", step="pipeline", timeout_seconds=timeout)
        return {
            "agent_results": [
                (
                    agent_type_str,
                    {**_EMPTY_RESULT, "errors": [f"agent timeout after {timeout}s"]},
                    RuntimeError(f"timed out after {timeout}s"),
                )
            ]
        }
    except Exception as exc:
        logger.error("agent_error agent=%s err=%s", agent_type_str, str(exc)[:300])
        if agent_logger:
            agent_logger.error("agent_error", step="pipeline", error=str(exc)[:300])
        return {
            "agent_results": [
                (agent_type_str, {**_EMPTY_RESULT, "errors": [str(exc)[:300]]}, exc)
            ]
        }
    finally:
        try:
            await agent.close()
        except Exception:
            pass


# ── Graph builder ─────────────────────────────────────────────────────────

def build_agent_graph():
    """Build and compile the LangGraph agent execution graph.

    Graph structure:
        START --[conditional: route_to_agents]--> run_agent (parallel) --> END

    The conditional edge from START dispatches Send objects, one per agent
    type. Each Send invokes run_agent with that agent's sources. Results
    are accumulated via the operator.add reducer on agent_results.

    Returns a compiled graph ready for ainvoke().
    """
    graph = StateGraph(AgentGraphState)

    # Single node: run_agent (invoked in parallel via Send)
    graph.add_node("run_agent", run_agent_node)

    # Conditional edge from START fans out to run_agent via Send objects
    graph.add_conditional_edges(START, route_to_agents)

    # Each run_agent instance goes to END after completion
    graph.add_edge("run_agent", END)

    return graph.compile()


# ── High-level runner ─────────────────────────────────────────────────────

async def run_agents_with_langgraph(
    sources_by_type: dict[str, list[Source]],
    run_config: Run,
    run_log=None,
) -> list[tuple[str, dict, Optional[Exception]]]:
    """Run all agents in parallel using LangGraph.

    Drop-in replacement for the old Orchestrator._run_agents_parallel().

    Args:
        sources_by_type: mapping agent_type_str -> list[Source]
        run_config: the Run configuration
        run_log: optional RunLogger

    Returns:
        list of (agent_name, result_dict, error_or_None) tuples
    """
    if not sources_by_type:
        return []

    graph = build_agent_graph()

    initial_state: AgentGraphState = {
        "sources_by_type": sources_by_type,
        "run_config": run_config,
        "run_log": run_log,
        "agent_results": [],
    }

    final_state = await graph.ainvoke(initial_state)

    results = final_state.get("agent_results", [])

    logger.info(
        "langgraph_agents_complete total_agents=%d",
        len(results),
    )

    return results
