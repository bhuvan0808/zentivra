"use client";

import { useState, useEffect, useCallback, Fragment } from "react";
import { getRuns, triggerRun } from "@/lib/api";

const STATUS_BADGES = {
  completed: "badge-success",
  running: "badge-primary",
  failed: "badge-error",
  partial: "badge-warning",
  pending: "badge-muted",
};

export default function RunsPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [error, setError] = useState(null);

  const loadRuns = useCallback(async () => {
    try {
      const data = await getRuns(50);
      setRuns(data);
    } catch (e) {
      setError("Failed to load runs. Is the backend running?");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadRuns(); // eslint-disable-line react-hooks/set-state-in-effect -- async fetch on mount is intentional
  }, [loadRuns]);

  async function handleTrigger() {
    setTriggering(true);
    try {
      const result = await triggerRun();
      setError(null);
      setTimeout(() => {
        loadRuns();
        setTriggering(false);
      }, 3000);
    } catch (e) {
      setError(e.message);
      setTriggering(false);
    }
  }

  function formatDate(dt) {
    if (!dt) return "—";
    return new Date(dt).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function duration(start, end) {
    if (!start || !end) return "—";
    const ms = new Date(end) - new Date(start);
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  }

  if (loading)
    return (
      <div className="loading">
        <div className="spinner" /> Loading runs...
      </div>
    );

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Pipeline Runs</h2>
          <p>{runs.length} total runs</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleTrigger}
          disabled={triggering}
        >
          {triggering ? "⏳ Triggering..." : "▶ Trigger New Run"}
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(239,68,68,0.1)",
            border: "1px solid rgba(239,68,68,0.3)",
            borderRadius: "var(--radius-sm)",
            color: "var(--error-500)",
            fontSize: "13px",
            marginBottom: "20px",
          }}
        >
          {error}
        </div>
      )}

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Status</th>
              <th>Findings</th>
              <th>Triggered By</th>
              <th>Started</th>
              <th>Duration</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <Fragment key={run.id}>
                <tr>
                  <td>
                    <code
                      style={{
                        fontSize: "12px",
                        color: "var(--primary-400)",
                        fontFamily: "monospace",
                      }}
                    >
                      {run.id?.slice(0, 12)}
                    </code>
                  </td>
                  <td>
                    <span
                      className={`badge ${STATUS_BADGES[run.status] || "badge-muted"}`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: "600" }}>
                    {run.total_findings || 0}
                  </td>
                  <td>
                    <span className="badge badge-muted">
                      {run.triggered_by || "manual"}
                    </span>
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>
                    {formatDate(run.started_at)}
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>
                    {duration(run.started_at, run.completed_at)}
                  </td>
                  <td>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() =>
                        setExpanded(expanded === run.id ? null : run.id)
                      }
                    >
                      {expanded === run.id ? "▲ Hide" : "▼ Show"}
                    </button>
                  </td>
                </tr>
                {expanded === run.id && (
                  <tr key={`${run.id}-detail`}>
                    <td
                      colSpan={7}
                      style={{
                        background: "var(--bg-surface-raised)",
                        padding: "16px",
                      }}
                    >
                      <h4
                        style={{
                          fontSize: "13px",
                          fontWeight: "600",
                          marginBottom: "12px",
                        }}
                      >
                        Agent Statuses
                      </h4>
                      {run.agent_statuses ? (
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(4, 1fr)",
                            gap: "12px",
                          }}
                        >
                          {Object.entries(run.agent_statuses).map(
                            ([agent, status]) => (
                              <div
                                key={agent}
                                style={{
                                  padding: "10px",
                                  background: "var(--bg-surface)",
                                  borderRadius: "var(--radius-sm)",
                                  border: "1px solid var(--border-default)",
                                }}
                              >
                                <div
                                  style={{
                                    fontSize: "12px",
                                    fontWeight: "600",
                                    marginBottom: "4px",
                                  }}
                                >
                                  {agent.replace("_", " ")}
                                </div>
                                <span
                                  className={`badge ${typeof status === "string" && status.includes("completed") ? "badge-success" : typeof status === "string" && status.includes("failed") ? "badge-error" : "badge-muted"}`}
                                >
                                  {status}
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      ) : (
                        <span
                          style={{
                            color: "var(--text-muted)",
                            fontSize: "13px",
                          }}
                        >
                          No agent details available
                        </span>
                      )}

                      {run.error_log && (
                        <div
                          style={{
                            marginTop: "12px",
                            padding: "10px",
                            background: "rgba(239,68,68,0.1)",
                            borderRadius: "var(--radius-sm)",
                            fontSize: "12px",
                            color: "var(--error-500)",
                            fontFamily: "monospace",
                          }}
                        >
                          {run.error_log}
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {runs.length === 0 && (
        <div className="empty-state">
          <div className="icon">🚀</div>
          <h3>No runs yet</h3>
          <p>
            Trigger your first pipeline run to start discovering AI
            developments.
          </p>
        </div>
      )}
    </>
  );
}
