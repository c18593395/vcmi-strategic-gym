$script = @'
echo "=== which python3 ==="
which python3
echo "=== read state ==="
python3 - <<'PYEOF'
import torch
sd=torch.load('/DATA/hero3/train_server/assets/wsl2_model_state.pt', map_location='cpu', weights_only=False)
print('step=', sd.get('step'))
print('keys=', list(sd.keys()))
PYEOF
echo "=== tail step ==="
tail -30 /DATA/hero3/train_server/train_full.log | grep -oE 'step=[0-9]+' | tail -5
echo "=== latest step in log ==="
grep -oE 'step=[0-9]+' /DATA/hero3/train_server/train_full.log | tail -1
echo "=== service status ==="
systemctl show homm3-train-server -p MainPID -p ExecMainStartTimestamp -p NRestarts
echo "=== latest ckpt ==="
ls -lt /DATA/hero3/train_server/checkpoints/*.pt 2>/dev/null | head -3
'@
ssh -o BatchMode=yes root@172.16.2.40 $script
