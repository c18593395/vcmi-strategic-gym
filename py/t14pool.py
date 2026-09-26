#!/usr/bin/env python3
"""T14.4 pool matrix: 4 maps x 4 games x blue-arms (Nullkiller2/T14Blue), red=PPO model.
Same red model as S-7 full-pool (wsl2_model.pt 09-25) -> only blue arm differs = clean A/B.
16 workers (CPU-collision window with N=16 training on 64 cores).

Deploy (server 172.16.2.40):
  nohup python3 /DATA/hero3/t14pool.py > /DATA/hero3/output/t14pool.log 2>&1 &
Recover (server was down mid-run): read /DATA/hero3/output/t14pool.log + t14pool_matrix_0926.json;
re-launch missing arms if rc!=0.
"""
import os, time, json, subprocess
from concurrent.futures import ThreadPoolExecutor
R = os.environ.get("HERO3_ROOT", "/DATA/hero3")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": R + "/vcmi_gym_new:" + R,
    "STRATEGIC_STATE_LIB": R + "/vcmi-build/bin/libmlclient.so",
    "LD_LIBRARY_PATH": R + "/DATA/hero3/vcmi-build/bin",
    "DISPLAY": ":99",
    "VCMI_WORKSPACE_DIR": "/root/vcmi-workspace",
    "VCMI_NATIVE_DIR": R + "/vcmi",
})
MODEL = R + "/wsl2_model.pt"          # stable 09-25 (1003121-era); NOT the live-rewritten train_server/assets
MAPS = ["Key to Victory.h3m", "good_to_go_h3m.vmap", "judgement_day_h3m.vmap", "King of Pain.h3m"]
ARMS = ["Nullkiller2", "T14Blue"]
G = 4
WORKERS = 16

def run(arm, mp, i):
    tag = mp.replace(".h3m","").replace(".vmap","").replace(" ","_").lower()
    traj = f"/tmp/t14pool_{arm}_{tag}_{i}.json"
    t0 = time.time()
    p = subprocess.run(["python3","-P",R+"/ep_runner_one.py","250",traj,mp,
        "--model",MODEL,"--blue_ai","MMAI_RANDOM","--blue_adventure_ai",arm,
        "--blue_hero_attack_bypass","1","--blue_hero_contact_d","2","--attack_f_min","0.0",
        "--reward_explore","0.3","--move_to_bias","1.0","--move_to_force","60",
        "--economy_force","24","--cycle_detect","5","--act_loop_penalty","1.0",
        "--guard_done_steps","15","--objective_reward","30","--act_loop_from_step","60",
        "--use_nk2_shaping","--nk2_shaping_scale","0.45","--target_chain","scorer"],
        env=ENV, capture_output=True, text=True, timeout=1800)
    rec = {"arm":arm,"map":mp,"i":i,"rc":p.returncode,"secs":round(time.time()-t0,1)}
    if p.returncode==0 and os.path.exists(traj):
        try:
            d = json.load(open(traj))
            rec.update({"R":round(float(d.get("total_rew",0)),2),"go":d.get("game_over")})
        except Exception as e:
            rec["traj_err"]=str(e)
    else:
        rec["err"] = ((p.stdout or "")+(p.stderr or ""))[-300:].replace("\n"," ")
    return rec

if __name__ == "__main__":
    jobs = [(a,m,i) for a in ARMS for m in MAPS for i in range(G)]
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for rec in ex.map(lambda j: run(*j), jobs):
            results.append(rec)
            print(json.dumps(rec), flush=True)
    json.dump(results, open(R+"/output/t14pool_matrix_0926.json","w"))
    import statistics
    bad = sum(1 for r in results if r.get("rc")!=0)
    for a in ARMS:
        rs=[r for r in results if r["arm"]==a and r.get("R") is not None]
        if rs:
            print(f"AGG {a}: n={len(rs)} meanR={statistics.mean(r['R'] for r in rs):.1f} go_nonzero={sum(1 for r in rs if r.get('go'))}")
    print(f"POOL_DONE maps={len(MAPS)} arms={len(ARMS)} games={G} bad={bad}")
