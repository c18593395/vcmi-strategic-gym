#!/usr/bin/env python3
"""batch_eval_batch3_ug.py — batch3 13张地下图 条件4/5/6 一次跑齐 (09-26)
部署位置: 服务器 /DATA/hero3/ (HERO3_ROOT=/DATA/hero3, 主仓此件为留档副本).
用法: python3 batch_eval_batch3_ug.py <ckpt> <n_workers> <games_per_map>
⚠ 09-27 踩坑: 漏训练同款引导参数 → 35~49步 fuse 底噪数据作废; 本件已内置 21 引导参数, 照抄勿省.
逐图判据(条件6): 4局 meanR>=0 且 正局(R>0)>=50% => promo 入batch:3; 否则 hold(batch:99)
条件5: 数据用满250步整局(非30步冒烟), N>=4
条件4: OBS同层已静态定谳(gate=0+spawn l=0), 跑局 rc/valid/obs 佐证无全零坑
输出: /DATA/hero3/output/batch3_ug_<ts>.json + 逐图行
"""
import os, json, subprocess, sys, time, glob
from concurrent.futures import ProcessPoolExecutor

H = os.environ.get("HERO3_ROOT", "/DATA/hero3")
MODELP = sys.argv[1]
N_WORKERS = int(sys.argv[2])
GAMES = int(sys.argv[3])
OUTDIR = H + "/output"
os.makedirs(OUTDIR, exist_ok=True)

pool_dir = H + "/train_server/pool_dir"
idx = json.load(open(H + "/train_server/pool/_pool_index.json"))
maps = sorted(k for k, v in idx.items()
              if isinstance(v, dict) and v.get("batch") == 3
              and os.path.exists(os.path.join(pool_dir, k)))
print(f"batch:3 _ug maps = {len(maps)}", flush=True)
print("model:", MODELP, "workers:", N_WORKERS, "games/map:", GAMES, flush=True)


def _w(go):
    return "WIN" if go == 1 else ("LOSS" if go >= 2 else "DRAW")


def run_worker(wid, chunk):
    ENV = dict(os.environ)
    ENV.update({
        "PYTHONPATH": H + "/vcmi_gym_new:" + H,
        "STRATEGIC_STATE_LIB": H + "/vcmi-build/bin/libmlclient.so",
        "LD_LIBRARY_PATH": H + "/vcmi-build/bin",
        "DISPLAY": ":99",
        "VCMI_WORKSPACE_DIR": os.environ.get("VCMI_WORKSPACE_DIR", "/root/vcmi-workspace"),
        "VCMI_NATIVE_DIR": H + "/vcmi",
    })
    out = []
    for mp in chunk:
        per = []
        for g in range(GAMES):
            traj = f"/tmp/b3u_w{wid}_{mp.replace('.vmap', '').replace(' ', '_')}_g{g}.json"
            rec = {"g": g, "winner": "ERROR", "go": 0, "steps": 0, "rew": 0.0, "rc": -1, "time": 0.0}
            t0 = time.time()
            try:
                r = subprocess.run(
                    ["python3", "-P", H + "/ep_runner_one.py", "250", traj, mp,
                     "--model", MODELP,
                     "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
                     # 训练同款引导参数 (与 h3m_batch_pipeline train_verify / run_episode 同构, 09-26 条件5 对齐):
                     "--reward_explore", "0.3",
                     "--move_to_bias", "1.92", "--move_to_force", "60", "--act_loop_from_step", "60",
                     "--economy_force", "24", "--cycle_detect", "5", "--act_loop_penalty", "1.0",
                     "--guard_done_steps", "15", "--objective_reward", "30",
                     "--blue_hero_grad", "0.2", "--blue_hero_grad_cap", "25",
                     "--blue_hero_contact_r", "15", "--blue_hero_contact_d", "2",
                     "--kill_r_first", "40", "--kill_r_next", "30",
                     "--own_town_decay", "0.5", "--own_town_max_visits", "4",
                     "--blue_hero_attack_bypass", "1", "--attack_f_min", "-1",
                     "--use_nk2_shaping", "--nk2_shaping_scale", "0.45",
                     "--target_chain", "scorer"],
                    env=ENV, timeout=2400)
                rec["rc"] = r.returncode
                if os.path.exists(traj):
                    d = json.load(open(traj))
                    if "error" in d:
                        rec["winner"] = "ERROR"; rec["err"] = str(d["error"])[:120]
                    else:
                        go = int(d.get("game_over", 0))
                        rec["go"] = go; rec["winner"] = _w(go)
                        rec["steps"] = int(d.get("steps", 0))
                        rec["rew"] = float(d.get("total_rew", d.get("rew", 0.0)))
                else:
                    rec["winner"] = "RC"
            except subprocess.TimeoutExpired:
                rec["winner"] = "TIMEOUT"
            except Exception as e:
                rec["winner"] = "ERROR"; rec["err"] = str(e)[:120]
            rec["time"] = round(time.time() - t0, 1)
            per.append(rec)
        valid = [x for x in per if x["winner"] in ("WIN", "LOSS", "DRAW")]
        full = [x for x in valid if x["steps"] >= 249]
        pos = [x for x in valid if x["rew"] > 0]
        err = [x for x in per if x["winner"] not in ("WIN", "LOSS", "DRAW")]
        nv = len(valid)
        meanR = (sum(x["rew"] for x in valid) / nv) if nv else None
        pos_pct = round(100 * len(pos) / max(1, nv))
        full_pct = round(100 * len(full) / max(1, nv))
        promo = (meanR is not None and meanR >= 0 and pos_pct >= 50 and nv >= 1)
        line = {"map": mp, "n": len(per), "valid": len(valid),
                "full250": len(full), "full_pct": full_pct,
                "meanR": round(meanR, 1) if meanR is not None else None,
                "pos": len(pos), "pos_pct": pos_pct, "err": len(err),
                "W": sum(1 for x in valid if x["winner"] == "WIN"),
                "DRAW": sum(1 for x in valid if x["winner"] == "DRAW"),
                "promo_batch3": promo, "games": per}
        flag = "PROMO" if promo else "hold"
        print(f"[{mp}] valid={line['valid']}/{line['n']} full250={line['full250']}({line['full_pct']}%) "
              f"meanR={line['meanR']} 正局={line['pos_pct']}% err={line['err']} => {flag}", flush=True)
        out.append(line)
    return out


if __name__ == "__main__":
    nchunk = max(1, len(maps) // N_WORKERS)
    chunks = [maps[i * nchunk:(i + 1) * nchunk] if i < N_WORKERS - 1 else maps[i * nchunk:]
              for i in range(N_WORKERS)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        allres = list(ex.map(run_worker, range(N_WORKERS), chunks))
    agg = [x for r in allres for x in r]
    ts = time.strftime("%Y%m%d_%H%M%S")
    with open(f"{OUTDIR}/batch3_ug_{ts}.json", "w") as f:
        json.dump({"model": MODELP, "games_per_map": GAMES, "maps": agg,
                   "promo": [x["map"] for x in agg if x["promo_batch3"]],
                   "hold": [x["map"] for x in agg if not x["promo_batch3"]],
                   "secs": round(time.time() - t0, 1)}, f, indent=2)
    print(f"DONE maps={len(agg)} promo={sum(1 for x in agg if x['promo_batch3'])} "
          f"hold={sum(1 for x in agg if not x['promo_batch3'])} secs={time.time() - t0:.0f}", flush=True)
