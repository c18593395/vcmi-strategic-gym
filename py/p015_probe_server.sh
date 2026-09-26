#!/bin/bash
echo "unit=$(systemctl is-active homm3-train-server)"
echo "NRestarts=$(systemctl show homm3-train-server -p NRestarts --value)"
echo "start=$(systemctl show homm3-train-server -p ExecMainStartTimestamp --value)"
echo "runners=$(pgrep -f ep_runner_one.py | wc -l)"
tail -2 /DATA/hero3/train_server/train_full.log
