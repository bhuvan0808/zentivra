"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Radar,
  Globe,
  Layers,
  Cpu,
  Brain,
  FileText,
  Mail,
  ArrowRight,
  Settings,
  Zap,
  Search,
  BarChart3,
  Send,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { LiquidBlob } from "@/components/liquid-blob";

const FEATURES = [
  {
    icon: Globe,
    title: "Configure Sources",
    description:
      "Set up crawlers for AI providers, research outlets, Hugging Face benchmarks, and more.",
  },
  {
    icon: Layers,
    title: "Multi-Step Run Builder",
    description:
      "3-step wizard to name your run, select sources, and set parameters via UI or code editor.",
  },
  {
    icon: Cpu,
    title: "Parallel Agent Execution",
    description:
      "All configured agents crawl their sources simultaneously for maximum throughput.",
  },
  {
    icon: Brain,
    title: "Intelligent Findings",
    description:
      "AI extracts insights, categorizes them, and assigns confidence scores automatically.",
  },
  {
    icon: FileText,
    title: "Automated Digests",
    description:
      "LLM-generated PDF and HTML reports compiled from aggregated findings and snapshots.",
  },
  {
    icon: Mail,
    title: "Email Alerts",
    description:
      "Automatic digest delivery to your configured recipients after every run.",
  },
];

const STEPS = [
  {
    icon: Settings,
    label: "Configure",
    detail: "Define run with sources and keywords",
  },
  { icon: Zap, label: "Trigger", detail: "Manual or scheduled execution" },
  {
    icon: Search,
    label: "Crawl",
    detail: "Agents process sources in parallel",
  },
  {
    icon: BarChart3,
    label: "Analyze",
    detail: "Findings extracted, snapshots created",
  },
  {
    icon: Send,
    label: "Report",
    detail: "Digest generated, optionally emailed",
  },
];

const fadeBlur = {
  initial: { opacity: 0, filter: "blur(4px)" },
  animate: { opacity: 1, filter: "blur(0px)" },
};

import { PublicGuard } from "@/components/public-guard";

function LandingContent() {
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");
  const signinHref = redirect
    ? `/signin?redirect=${encodeURIComponent(redirect)}`
    : "/signin";
  const signupHref = redirect
    ? `/signup?redirect=${encodeURIComponent(redirect)}`
    : "/signup";

  return (
    <div className="relative min-h-screen overflow-clip bg-background text-foreground">
      <LiquidBlob />

      {/* ── Ambient glow (gives backdrop-blur something to frost) ── */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-1 overflow-hidden"
      >
        <div className="absolute -top-24 left-1/4 h-120 w-120 rounded-full bg-indigo-500/20 blur-[120px]" />
        <div className="absolute top-1/3 right-[10%] h-100 w-100 rounded-full bg-violet-500/15 blur-[100px]" />
        <div className="absolute bottom-[15%] left-[15%] h-88 w-88 rounded-full bg-purple-500/15 blur-[110px]" />
        <div className="absolute bottom-0 right-1/4 h-80 w-80 rounded-full bg-indigo-400/10 blur-[100px]" />
      </div>

      {/* ── Header ── */}
      <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-background/40 backdrop-blur-xl backdrop-saturate-150">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <Radar className="size-6 text-primary" />
            <span className="text-lg font-bold tracking-tight font-display">
              Zentivra
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href={signinHref}>Sign In</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href={signupHref}>
                Get Started
                <ArrowRight className="ml-1.5 size-3.5" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative z-10 mx-auto max-w-4xl px-4 pb-24 pt-20 text-center sm:px-6 sm:pt-28 lg:pt-36">
        <motion.h1
          {...fadeBlur}
          transition={{ duration: 0.5 }}
          className="text-4xl font-bold tracking-tight font-display sm:text-5xl lg:text-6xl"
        >
          Your AI Intelligence{" "}
          <span className="bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 bg-clip-text text-transparent">
            Radar
          </span>
        </motion.h1>

        <motion.p
          {...fadeBlur}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground"
        >
          A multi-agent intelligence system that monitors the AI landscape,
          extracts findings, and generates executive digests — so you never miss
          a beat.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Button size="lg" asChild>
            <Link href={signupHref}>
              Get Started Free
              <ArrowRight className="ml-1.5 size-4" />
            </Link>
          </Button>
          <Button
            variant="outline"
            size="lg"
            asChild
            className="border-white/15 bg-card/30 backdrop-blur-xl backdrop-saturate-150 hover:bg-card/50"
          >
            <a href="#features" style={{ filter: "blur(0px)" }}>
              Learn More
            </a>
          </Button>
        </motion.div>
      </section>

      {/* ── Features ── */}
      <section
        id="features"
        className="relative z-10 mx-auto max-w-6xl px-4 py-20 sm:px-6"
      >
        <motion.div
          variants={fadeBlur}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4 }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight font-display sm:text-4xl">
            Everything You Need
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
            From source configuration to automated report delivery, Zentivra
            handles the entire intelligence pipeline.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, filter: "blur(4px)" }}
              whileInView={{ opacity: 1, filter: "blur(0px)" }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.35, delay: i * 0.07, ease: "easeOut" }}
              className="group rounded-xl border border-white/10 bg-card/30 p-6 backdrop-blur-xl backdrop-saturate-150 shadow-sm transition-shadow hover:shadow-lg"
            >
              <div className="mb-4 flex size-10 items-center justify-center rounded-lg bg-primary/10">
                <f.icon className="size-5 text-primary" />
              </div>
              <h3 className="text-sm font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {f.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="relative z-10 mx-auto max-w-5xl px-4 py-20 sm:px-6">
        <motion.div
          variants={fadeBlur}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4 }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight font-display sm:text-4xl">
            How It Works
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
            Five steps from configuration to a polished executive digest.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-6 sm:grid-cols-5">
          {STEPS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.35, delay: i * 0.1, ease: "easeOut" }}
              className="relative flex flex-col items-center text-center"
            >
              <div
                style={{ filter: "blur(0px)" }}
                className="flex size-14 items-center justify-center rounded-full border-2 border-white/15 bg-card/30 shadow-sm backdrop-blur-xl backdrop-saturate-150"
              >
                <s.icon className="size-6 text-primary" />
              </div>
              <div className="mt-4 text-xs font-bold uppercase tracking-wider text-primary">
                Step {i + 1}
              </div>
              <h3 className="mt-1 text-sm font-semibold">{s.label}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{s.detail}</p>

              {i < STEPS.length - 1 && (
                <ArrowRight className="absolute -right-3 top-5 hidden size-4 text-muted-foreground/40 sm:block" />
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="relative z-10 mx-auto max-w-3xl px-4 py-20 text-center sm:px-6">
        <motion.div
          initial={{ opacity: 0, filter: "blur(4px)" }}
          whileInView={{ opacity: 1, filter: "blur(0px)" }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4 }}
        >
          <h2 className="text-3xl font-bold tracking-tight font-display sm:text-4xl">
            Ready to Get Started?
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
            Create your account and configure your first intelligence run in
            minutes.
          </p>
          <div className="mt-8">
            <Button size="lg" asChild>
              <Link href={signupHref}>
                Create Free Account
                <ArrowRight className="ml-1.5 size-4" />
              </Link>
            </Button>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t border-white/10 bg-background/30 backdrop-blur-xl backdrop-saturate-150">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6 sm:px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Radar className="size-4" />
            <span>Zentivra</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Frontier AI Radar v1.0
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function LandingPage() {
  return (
    <PublicGuard>
      <LandingContent />
    </PublicGuard>
  );
}
