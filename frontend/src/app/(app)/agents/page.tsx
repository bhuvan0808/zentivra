"use client";

import { Activity } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";

const AGENT_CARDS = [
  { key: "competitor", label: "Competitor Watcher", description: "Monitors competitor announcements, releases, and strategic moves." },
  { key: "model_provider", label: "Model Provider Watcher", description: "Tracks LLM provider updates, new model releases, and API changes." },
  { key: "research", label: "Research Scout", description: "Scans research publications, arXiv papers, and technical blogs." },
  { key: "hf_benchmark", label: "HF Benchmark Tracker", description: "Monitors Hugging Face leaderboards and benchmark results." },
];

export default function AgentsPage() {
  return (
    <div>
      <PageHeader
        title="Agents"
        description="Agent overview and monitoring."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {AGENT_CARDS.map((agent) => (
          <Card key={agent.key}>
            <CardContent className="space-y-3 py-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold">{agent.label}</h3>
                <Activity className="size-4 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground">{agent.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* TODO: Re-enable live agent monitoring when per-agent status tracking APIs are implemented */}
      <Card className="mt-6">
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          Live agent monitoring will be available once run execution tracking is implemented.
        </CardContent>
      </Card>
    </div>
  );
}
