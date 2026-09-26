#!/usr/bin/env python3
"""T14.3b patcher — capability upgrade on top of T14.3 (WSL repo 4a1675c6a2).

Three items, all ENABLE_T14_BLUE-gated or zero-default hooks (NK2 zero behavior change):
  (1) Nullkiller.h/.cpp : onCommitPursuit empty hook (post-selection hard-goal injection
                          call site) + buildPlanAndFilter gated pinned band (>=1e7 keeps
                          its priority; NK2 organic cap DEFENSIVE_EMERGENCY_PRIORITY=1e6)
  (2) Nullkiller.h/.cpp + Settings.h/.cpp : onAfterInit empty hook + gated
                          Settings::setT14Weights (NK2 never compiled/calls it)
  (3) MMAI CMakeLists.txt : cross-arch python3 dev discovery (find_path/find_library)
                          replacing the hardcoded /usr/lib/x86_64-linux-gnu/libpython3.12.so
                          (c80796a17) that broke the ARM build (symlink-bridged on 172.16.2.40)

T14BlueMod files are overwritten from ./.t14_staging/T14b/ (T14Nullkiller.h/.cpp v2).

Usage (run inside WSL against /home/administrator/vcmi-native):
  python3 patch_t14blue_b.py --check      # verify all anchors present
  python3 patch_t14blue_b.py             # apply (+ .bak_t14blue_b backups, idempotent)
  python3 patch_t14blue_b.py --rollback  # restore .bak_t14blue_b
"""
import sys, os, shutil

ROOT = os.environ.get("VCMI_ROOT", "/home/administrator/vcmi-native")
STAGE = os.path.join(os.environ.get("HERMES3FRESH", "/mnt/d/Bigdata/hero3_fresh"), ".t14_staging", "T14b")
BAK = ".bak_t14blue_b"

EDITS = []  # (relpath, old, new, done_marker)

# ---- (1a) Nullkiller.h: two zero-default hooks after onPursueTurn
EDITS.append(("AI/Nullkiller2/Engine/Nullkiller.h",
"""	/// T14 (09-26): per-turn pursuit hook, called from makeTurn after defender reservation.
	/// NK2 default = empty (zero behavior change); T14Blue::T14Nullkiller overrides it (R13 harvest nudge).
	virtual void onPursueTurn() {}
""",
"""	/// T14 (09-26): per-turn pursuit hook, called from makeTurn after defender reservation.
	/// NK2 default = empty (zero behavior change); T14Blue::T14Nullkiller overrides it (R13 harvest nudge).
	virtual void onPursueTurn() {}
	/// T14.3b (09-27): post-selection hard-goal-injection hook, called from makeTurn after
	/// the selected task vector is sorted; NK2 default = empty (zero behavior change);
	/// T14Blue::T14Nullkiller overrides it (committed march task spliced into the stream).
	virtual void onCommitPursuit(Goals::TTaskVec & selectedTasks) {}
	/// T14.3b (09-27): post-init hook, called at the tail of init(); NK2 default = empty;
	/// T14Blue::T14Nullkiller overrides it (one-shot archetype Settings weight axis).
	virtual void onAfterInit() {}
""",
"virtual void onCommitPursuit"))

# ---- (1b) Nullkiller.cpp: init tail -> onAfterInit call
EDITS.append(("AI/Nullkiller2/Engine/Nullkiller.cpp",
"""	decomposer.reset(new DeepDecomposer(this));
	armyFormation.reset(new ArmyFormation(cc, this));
}
""",
"""	decomposer.reset(new DeepDecomposer(this));
	armyFormation.reset(new ArmyFormation(cc, this));

	// T14.3b (09-27): post-init hook — NK2 empty default (zero behavior change).
	onAfterInit();
}
""",
"onAfterInit();"))

# ---- (1c) Nullkiller.cpp: makeTurn post-selection -> onCommitPursuit call
EDITS.append(("AI/Nullkiller2/Engine/Nullkiller.cpp",
"""		std::ranges::sort(selectedTasks, [](const TTask& a, const TTask& b)
		{
			return a->priority > b->priority;
		});

		if(selectedTasks.empty())
""",
"""		std::ranges::sort(selectedTasks, [](const TTask& a, const TTask& b)
		{
			return a->priority > b->priority;
		});

		// T14.3b (09-27): post-selection hard-goal-injection hook — NK2 empty default
		// (zero behavior change); T14Nullkiller splices a committed march task in.
		onCommitPursuit(selectedTasks);

		if(selectedTasks.empty())
""",
"onCommitPursuit(selectedTasks);"))

# ---- (1d) Nullkiller.cpp: buildPlanAndFilter gated pinned band
EDITS.append(("AI/Nullkiller2/Engine/Nullkiller.cpp",
"""				const auto & task = tasks[i];
				if(task->asTask()->priority <= 0 || priorityTier != PriorityEvaluator::PriorityTier::BUILDINGS)
""",
"""				const auto & task = tasks[i];
#ifdef ENABLE_T14_BLUE
				// T14.3b (09-27) pinned band: committed T14 march tasks carry a priority
				// >= 1e7 — above NK2's organic cap (DEFENSIVE_EMERGENCY_PRIORITY = 1e6) —
				// so they keep it verbatim and always lead the tier pass.
				if(task->asTask()->priority >= 10000000.0f)
					continue;
#endif
				if(task->asTask()->priority <= 0 || priorityTier != PriorityEvaluator::PriorityTier::BUILDINGS)
""",
"pinned band"))

# ---- (2a) Settings.h: gated setter declaration
EDITS.append(("AI/Nullkiller2/Engine/Settings.h",
"""		bool isUpdateHitmapOnTileReveal() const { return updateHitmapOnTileReveal; }
		bool isOpenMap() const { return openMap; }
	};
""",
"""		bool isUpdateHitmapOnTileReveal() const { return updateHitmapOnTileReveal; }
		bool isOpenMap() const { return openMap; }
#ifdef ENABLE_T14_BLUE
		// T14.3b (09-27) weight axis: archetype-weighted overrides. Gated, and never
		// called by stock Nullkiller -> zero behavior change for the NK2 build.
		void setT14Weights(float maxGoldPressure, float retreatThresholdRelative, int mainHeroTurnDistanceLimit);
#endif
	};
""",
"setT14Weights"))

# ---- (2b) Settings.cpp: gated setter implementation
EDITS.append(("AI/Nullkiller2/Engine/Settings.cpp",
"""		openMap = node["openMap"].Bool();
		useTroopsFromGarrisons = node["useTroopsFromGarrisons"].Bool();
		useOneWayMonoliths = node["useOneWayMonoliths"].Bool();
	}
}
""",
"""		openMap = node["openMap"].Bool();
		useTroopsFromGarrisons = node["useTroopsFromGarrisons"].Bool();
		useOneWayMonoliths = node["useOneWayMonoliths"].Bool();
	}
#ifdef ENABLE_T14_BLUE
	void Settings::setT14Weights(float mGP, float rTRel, int mHeroDist)
	{
		maxGoldPressure = mGP;
		retreatThresholdRelative = rTRel;
		mainHeroTurnDistanceLimit = mHeroDist;
	}
#endif
}
""",
"void Settings::setT14Weights"))

# ---- (3) MMAI CMakeLists.txt: cross-arch python3 dev discovery
EDITS.append(("AI/MMAI/CMakeLists.txt",
"""# PyGILState_Ensure/Release used in AAI::yourTurn
target_link_libraries(MMAI PRIVATE /usr/lib/x86_64-linux-gnu/libpython3.12.so)

# Used in schema/base.h to determine if it is imported by MMAI or vcmi-gym
target_compile_definitions(MMAI PRIVATE MMAI_DLL=1)
target_include_directories(MMAI
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
  PRIVATE "/usr/include/python3.12"
)
""",
"""# PyGILState_Ensure/Release used in AAI::yourTurn
# T14.3b (09-27): cross-arch python3 dev discovery — replaces the hardcoded
# /usr/lib/x86_64-linux-gnu/libpython3.12.so (c80796a17) that broke the ARM build
# (had been papered over with /usr symlink bridges on 172.16.2.40).
find_path(T14_PYTHON3_INCLUDE_DIR NAMES Python.h
  HINTS /usr/include /usr/local/include
  PATH_SUFFIXES python3.12 python3.11 python3.10 python3
)
find_library(T14_PYTHON3_LIBRARY NAMES python3.12 python3.11 python3.10 python3
  HINTS /usr/lib /usr/lib64 /usr/lib/x86_64-linux-gnu /usr/local/lib
)
if(T14_PYTHON3_INCLUDE_DIR AND T14_PYTHON3_LIBRARY)
  message(STATUS "MMAI python3 dev: ${T14_PYTHON3_INCLUDE_DIR} + ${T14_PYTHON3_LIBRARY}")
  target_link_libraries(MMAI PRIVATE ${T14_PYTHON3_LIBRARY})
  target_include_directories(MMAI PRIVATE ${T14_PYTHON3_INCLUDE_DIR})
else()
  message(FATAL_ERROR "python3 development files not found (need Python.h + libpython3.x); install python3-devel")
endif()

# Used in schema/base.h to determine if it is imported by MMAI or vcmi-gym
target_compile_definitions(MMAI PRIVATE MMAI_DLL=1)
target_include_directories(MMAI
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
)
""",
"find_path(T14_PYTHON3_INCLUDE_DIR"))

# ---- T14BlueMod v2: overwrite-copy from staging
T14FILES = ("AI/T14BlueMod/T14Nullkiller.h", "AI/T14BlueMod/T14Nullkiller.cpp")

def apply_all():
    ok = True
    for rel, old, new, _marker in EDITS:
        p = os.path.join(ROOT, rel)
        s = open(p, encoding="utf-8").read()
        if _marker in s:
            print(f"ALREADY  {rel}")
            continue
        if s.count(old) != 1:
            print(f"FAIL     {rel} (anchor count={s.count(old)})")
            ok = False
            continue
        if not os.path.exists(p + BAK):
            shutil.copyfile(p, p + BAK)
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
        print(f"PATCHED  {rel}")
    for rel in T14FILES:
        src = os.path.join(STAGE, os.path.basename(rel))
        dst = os.path.join(ROOT, rel)
        shutil.copyfile(dst, dst + BAK)
        shutil.copyfile(src, dst)
        print(f"COPY     {rel} (from staging)")
    return ok

def check_all():
    ok = True
    for rel, old, new, marker in EDITS:
        p = os.path.join(ROOT, rel)
        s = open(p, encoding="utf-8").read()
        if marker in s:
            print(f"ALREADY  {rel}")
        elif s.count(old) == 1:
            print(f"READY    {rel}")
        else:
            print(f"MISSING  {rel} (anchor count={s.count(old)})")
            ok = False
    for rel in T14FILES:
        src = os.path.join(STAGE, os.path.basename(rel))
        print(("READY    " if os.path.exists(src) else "MISSING  ") + rel + f" (staging {os.path.exists(src)})")
        ok = ok and os.path.exists(src)
    return ok

def rollback_all():
    for rel, *_ in EDITS:
        p = os.path.join(ROOT, rel)
        bak = p + BAK
        if os.path.exists(bak):
            shutil.copyfile(bak, p)
            print(f"ROLLED   {rel}")
    for rel in T14FILES:
        p = os.path.join(ROOT, rel)
        bak = p + BAK
        if os.path.exists(bak):
            shutil.copyfile(bak, p)
            print(f"ROLLED   {rel}")

if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check_all() else 1)
    if "--rollback" in sys.argv:
        rollback_all()
    else:
        sys.exit(0 if apply_all() else 1)
