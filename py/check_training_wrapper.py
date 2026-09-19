import subprocess, sys

result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "bash", "/mnt/d/Bigdata/hero3_fresh/check_training.sh"],
    capture_output=True, text=True, timeout=30
)
sys.stdout.write(result.stdout)
if result.stderr:
    sys.stderr.write(result.stderr)
sys.exit(result.returncode)
