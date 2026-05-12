# Nginx Security and Rate Limiting Guide

## Purpose

This guide explains how to triage suspicious Nginx access logs, repeated authentication failures, and rate limiting events.

## Common Symptoms

Administrators may observe repeated HTTP 401, 403, 404, or 429 responses from the same source IP address. Users may report that a web service is unavailable or that login attempts are being blocked.

## Important Status Codes

- 401 Unauthorized usually indicates failed or missing authentication.
- 403 Forbidden usually indicates access was denied after authentication or authorization checks.
- 404 Not Found may indicate scanning for nonexistent paths.
- 429 Too Many Requests indicates rate limiting is active.

## Initial Troubleshooting Steps

1. Identify the source IP address and request pattern.
2. Check whether the requests target login pages, admin paths, API routes, or known vulnerable endpoints.
3. Review timestamps to determine request frequency.
4. Check whether multiple usernames or accounts were targeted.
5. Confirm whether rate limiting rules are working as expected.
6. Review firewall, WAF, or reverse proxy logs for related activity.

## Common Causes

Repeated 401 and 429 responses may indicate brute-force login attempts, password spraying, bot traffic, vulnerability scanning, misconfigured clients, or an overly aggressive health check.

## Escalation Criteria

Escalate to the security team if the source IP repeatedly targets authentication endpoints, attempts multiple usernames, triggers rate limits, accesses admin paths, or appears in threat intelligence sources.

## Recommended Mitigations

Consider blocking the IP address, tightening rate limits, enabling account lockout protections, requiring MFA, reviewing exposed admin endpoints, and confirming that access logs are retained for investigation.