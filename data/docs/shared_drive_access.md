# Shared Drive Access Troubleshooting Guide

## Purpose

This guide explains how to troubleshoot shared drive access issues, mapped drive failures, and file permission problems.

## Common Symptoms

Users may report that they cannot access a shared drive, receive an access denied message, cannot map a network drive, or can access some folders but not others.

## Initial Troubleshooting Steps

1. Confirm that the user is connected to the corporate network or VPN.
2. Confirm that the shared drive path is correct.
3. Check whether the user has the required group membership.
4. Ask whether the user's password was recently changed.
5. Remove and recreate the mapped drive if cached credentials are suspected.
6. Test access using the full UNC path.
7. Confirm that the file server is online and reachable.
8. Check whether other users are affected.

## Common Causes

Shared drive issues are often caused by missing security group membership, stale cached credentials, disconnected VPN sessions, incorrect drive mappings, DNS issues, file server outages, or permission inheritance problems.

## Escalation Criteria

Escalate to systems administration if the file server is unreachable, multiple users are affected, permissions appear incorrect, group membership changes are not applying, or sensitive folder access is involved.

## Security Notes

Unexpected access denied errors for sensitive folders should be reviewed carefully. Do not grant access without confirming manager approval, business need, and least-privilege requirements.