#!/bin/bash
# R7 新打点验证脚本 (2026-09-03)
F=$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -1)
echo "FILE=$F"
echo "--- popIfTop OK count:"
grep -c 'popIfTop OK' "$F"
echo "--- notifyObjectAboutRemoval ENTER (last 3):"
grep 'notifyObjectAboutRemoval ENTER' "$F" | tail -3
echo "--- CHeroMovementQuery onExposure (last 3):"
grep 'CHeroMovementQuery::onExposure ENTER' "$F" | tail -3
echo "--- MapObjectVisitQuery onExposure (last 2):"
grep 'MapObjectVisitQuery::onExposure ENTER' "$F" | tail -2
echo "--- battleFinished RETURN (last 2):"
grep 'battleFinished RETURN' "$F" | tail -2
