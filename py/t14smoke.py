#!/usr/bin/env python3
"""T14.4 smoke: KTV N=4, T14Blue vs Nullkiller2 baseline (#298 discipline).
Deployed on server 09-26 as /DATA/hero3/t14smoke.py (scp'd from local).
Result JSON: /DATA/hero3/output/t14smoke_ktv_0926.json
"""
import sys, os, time, json, subprocess
R = os.environ.get("HERO3_ROOT", "/DATA/hero3")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": R + "/vcmi_gym_new:" + R,
    "STRATEGIC_STATE_LIB": R + "/vcmi-build/bin/libmlclient.so",
    "LD_LIBRARY_PATH": R + "/vcmi-build/bin",
    "DISPLAY": ":99",
    "VCMI_WORKSPACE_DIR": "/root/vcmi-workspace",
    "VCMI_NATIVE_DIR": R + "/vcmi",
})
MP = "Key to Victory.h3m"   # in vcmi/data/Maps
MODEL = R + "/wsl2_model.pt"
N = 4
results = []
for arm in ["T14Blue", "Nullkiller2"]:
    for i in range(N):
        traj = f"/tmp/t14smoke_{arm}_{i}.json"
        t0 = time.time()
        p = subprocess.run(["python3","-P",R+"/ep_runner_one.py","250",traj,MP,
            "--model",MODEL,"--blue_ai","MMAI_RANDOM","--blue_adventure_ai",arm,
            "--blue_hero_attack_bypass","1","--blue_hero_contact_d","2","--attack_f_min","0.0",
            "--reward_explore","0.3","--move_to_bias","1.0","--move_to_force","60",
            "--economy_force","24","--cycle_detect","5","--act_loop_penalty","1.0",
            "--guard_done_steps","15","--objective_reward","30","--act_loop_from_step","60",
            "--use_nk2_shaping","--nk2_shaping_scale","0.45","--target_chain","scorer"],
            env=ENV, capture_output=True, text=True, timeout=900)
        dt = time.time()-t0
        rec = {"arm":arm,"i":i,"rc":p.returncode,"secs":round(dt,1)}
        if p.returncode==0 and os.path.exists(traj):
            d = json.load(open(traj))
            rec.update({"R":round(float(d.get("total_rew",0)),2),"nsteps":d.get("nsteps"),
                        "go":d.get("game_over")})
        out = (p.stdout or "") + (p.stderr or "")
        rec["T14_ACT"] = out.count("[T14-ACT]")
        rec["err"] = "no" if p.returncode==0 else out[-300:].replace("\n"," ")
        results.append(rec)
        print(json.dumps(rec), flush=True)
        # kill any leaked vcmini
        subprocess.run(["pkill","-f",f"vcmini.*{MP.split('.')[0]}"],capture_output=True)
json.dump(results, open(R+"/output/t14smoke_ktv_0926.json","w"))
bad = sum(1 for r in results if r["rc"]!=0)
print(f"SMOKE_DONE arm=T14Blue+Nullkiller2 N=4 bad={bad}")
