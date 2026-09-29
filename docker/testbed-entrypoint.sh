#!/bin/sh
set -eu

ipsec start

attempt=0
while [ "$attempt" -lt 20 ]; do
    if test -S /var/run/charon.vici; then
        exec /usr/sbin/sshd -D
    fi
    attempt=$((attempt + 1))
    sleep 0.25
done

echo "strongSwan failed to create /var/run/charon.vici" >&2
ipsec statusall >&2 || true
exit 1
