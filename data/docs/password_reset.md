# Password Reset and Account Lockout Guide

## Purpose

This guide explains how to triage password reset requests, account lockouts, and common authentication issues.

## Common Symptoms

Users may report that they cannot sign in after changing their password, their account is locked, or they are repeatedly prompted for credentials.

## Initial Troubleshooting Steps

1. Verify the user's identity according to company policy.
2. Confirm whether the account is locked in the identity provider or directory service.
3. Check whether the user recently changed their password.
4. Ask the user to sign out of all active sessions and sign back in.
5. Confirm that cached credentials are not being used on laptops, mobile devices, VPN clients, or mapped drives.
6. If multi-factor authentication is enabled, confirm that the user's MFA method is active and accessible.

## Common Causes

Password reset issues are often caused by cached credentials, expired sessions, account lockout thresholds, disabled accounts, expired passwords, or MFA device problems.

## Escalation Criteria

Escalate to identity and access management if the account is disabled, the user cannot complete MFA, suspicious login attempts are detected, or privileged account access is involved.

## Security Notes

Repeated failed login attempts may indicate a brute-force attempt, password spraying, stale service credentials, or a compromised device. Review authentication logs before unlocking accounts with repeated failures.