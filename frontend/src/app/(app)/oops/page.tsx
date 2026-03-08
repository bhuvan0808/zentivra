"use client";

import { Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";

export default function OopsPage() {
  return (
    <div>
      <PageHeader
        title="Oops"
        description="Drop a disruptive article link, generate a PDF report, and email it."
      />

      {/* TODO: Re-enable when the disruptive article workflow API is implemented */}
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <Sparkles className="mb-4 size-10 text-muted-foreground/50" />
          <p className="text-lg font-medium">Coming Soon</p>
          <p className="mt-1 text-sm text-muted-foreground max-w-md">
            The disruptive article analysis workflow is being rebuilt. Check
            back once the new pipeline is fully operational.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
