"""
Digest module — post-processing pipeline for findings.

This module compiles raw agent findings into structured intelligence digests
and renders them as HTML/PDF. It runs after the orchestrator has collected
findings from all agents (competitor, model provider, research, HF benchmark).

Components:
- DigestCompiler: Deduplicates, ranks, organizes, and summarizes findings.
- PDFRenderer: Converts digest data to HTML (Jinja2) and PDF (WeasyPrint/FPDF).
"""
