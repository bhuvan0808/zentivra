"""
Notifications module — delivery of digest reports to users.

This module runs after the digest pipeline has produced HTML/PDF outputs.
It sends email notifications containing the executive summary, PDF attachment,
and a link to the web dashboard.

Components:
- EmailService: Sends digest emails via SendGrid (primary) or SMTP (fallback).
"""
