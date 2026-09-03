#!/bin/bash
echo "=== dmesg 崩溃完整段:"
dmesg 2>/dev/null | grep -B2 -A25 'segfault\|general protection\|SIGSEGV' | tail -45
