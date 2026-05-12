# VPN Troubleshooting Guide

## Purpose

This guide explains how to troubleshoot VPN connectivity issues for remote users.

## Common Symptoms

Users may report that they can connect to the internet but cannot access internal systems, shared drives, remote desktops, or private applications.

## Initial Troubleshooting Steps

1. Confirm that the user's internet connection is working.
2. Confirm that the VPN client is installed and updated.
3. Verify that the user is signing in with the correct username format.
4. Check whether the user's password was recently changed.
5. Confirm that MFA approval is successful.
6. Ask the user to disconnect and reconnect the VPN.
7. Confirm that the VPN client received an internal IP address.
8. Test DNS resolution for internal resources.
9. Test access to a known internal hostname and IP address.

## Common Causes

VPN issues are often caused by expired passwords, failed MFA, DNS problems, stale cached credentials, firewall restrictions, split-tunnel routing issues, or disabled remote access permissions.

## Escalation Criteria

Escalate to the network team if multiple users are affected, the VPN gateway is unreachable, internal routing fails, DNS resolution fails for many users, or firewall logs show blocked VPN traffic.

## Security Notes

Repeated failed VPN login attempts from unfamiliar locations may indicate credential stuffing or attempted unauthorized access. Review source IPs, timestamps, and user account history.