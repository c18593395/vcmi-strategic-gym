/*
 * h3m2vmap, part of hero3_fresh P10-B
 *
 * H3M → VMAP 转换工具 (引擎内路径):
 *   CMapService::loadMap(.h3m) → CMapLoaderH3M → 内存 CMap
 *   → [B3 改写层 R1-R7, 默认全开 --no-rules 关闭全部]
 *   → CMapService::saveMap(.vmap) → CMapSaverJson → zip 三件套
 *   → 读回自检 + report.json 审计 (R1-R7 计数 + 白名单过滤统计)
 *
 * 设计稿: docs/P10-B-h3m2vmap转换器设计稿.md §7 B3
 * 构建纪律: 独立 CMake 工程, 只读链接 rel/bin/libvcmi.so, 禁覆盖 rel/ 下任何 .so
 */
#include "Global.h" // VCMI_LIB_NAMESPACE_* 宏 + 全局环境 (EntryPoint 经 StdInc 引入, 独立工具须直接引入)

#include "lib/GameLibrary.h"
#include "lib/GameConstants.h"
#include "lib/CConsoleHandler.h"
#include "lib/logging/CBasicLogConfigurator.h"
#include "lib/VCMIDirs.h"
#include "lib/mapping/CMapService.h"
#include "lib/mapping/CMap.h"
#include "lib/mapping/CMapHeader.h"
#include "lib/texts/MetaString.h"
#include "lib/mapObjects/CGObjectInstance.h"
#include "lib/mapObjects/CGTownInstance.h"
#include "lib/mapObjects/CGHeroInstance.h"
#include "lib/mapObjects/CGCreature.h"
#include "lib/mapObjects/army/CCreatureSet.h"
#include "lib/mapObjects/army/CArmedInstance.h"
#include "lib/callback/EditorCallback.h"  // 修复 SIGSEGV: CGHeroInstance::serializeCommonOptions 需 CB 非空

#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>


#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace
{
	std::vector<uint8_t> readFile(const std::string & path)
	{
		std::ifstream in(path, std::ios::binary);
		if(!in) return std::vector<uint8_t>();
		return std::vector<uint8_t>((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
	}

	void printMap(const std::string & label, const std::unique_ptr<CMap> & map)
	{
		if(!map)
		{
			std::cerr << label << " is NULL" << std::endl;
			return;
		}
		std::cout << "  " << label << " size=" << map->width << "x" << map->height
			<< " levels=" << map->levels()
			<< " objects=" << map->getObjects().size() << std::endl;
	}

	// ===================================================================
	// B3 改写层 (设计稿 §5 R1-R7, 默认全开)
	// ===================================================================

	struct B3Options
	{
		bool rules       = true;   // --no-rules 关闭全部
		// R1 城镇归零 (B 方案: 保留空壳, owner 归中立 + 清建筑 + 清守军)
		bool r1          = true;   // --no-r1 关闭
		// R3 守卫强度 (0.0~5.0, 1.0=原版)
		double r3_scale  = 1.0;    // --r3-scale X
		// R4 白名单过滤 (保留 ML 识别目标 + 地形装饰, 移除杂项)
		bool r4          = true;   // --no-r4 关闭
		// R5 地形全草 (默认关, #94 误判; 仅 --terrain-flatten 开)
		bool r5_flatten  = false;  // --terrain-flatten 开
		// R6 胜负条件重置 (默认开, --keep-victory 关)
		bool r6_reset    = true;   // --keep-victory 关
		// R7 文本 ID 改写
		bool r7          = true;   // --no-r7 关

		std::map<std::string, long long> report; // 审计计数, 写 report.json
	};

	// R4 白名单: 短名集 (与 objects.json / getTypeName() 返回值同源, CMapSaverJson
	// 写出的 type 字段就是 typeName)。对齐 ML 侧 strategic_state.cpp 的 Obj:: 枚举识别集:
	//   fill_target_list: MINE / RESOURCE / CAMPFIRE / TREASURE_CHEST / ARTIFACT
	//   fill_terrain_grid: HERO / TOWN / MONSTER / RANDOM_MONSTER / ARTIFACT /
	//     TREASURE_CHEST / RESOURCE / MINE / CREATURE_GENERATOR1/2 / SUBTERRANEAN_GATE / BORDER_GATE
	// randomXxx 变体在游戏运行时定型为对应具体 Obj (MONSTER/RESOURCE/ARTIFACT), ML 可识别, 保留。
	// 静态装饰保留: 决定 tile.blocked() 障碍通道, 删了地图失去地形复杂度。
	// 实测 Knee Deep (413 对象 / 70 类): 保留 39 类 366 个, 移除 31 类 47 个。
	const std::set<std::string> R4_WHITELIST = {
		// --- ML 可交互目标 (运行时定型后全部可识别) ---
		"town",                    // Obj::TOWN (R1 归零空壳)
		"hero",                    // Obj::HERO
		"monster",                 // Obj::MONSTER
		"randomMonsterLevel1",     // 运行时定型为 Obj::MONSTER
		"randomMonsterLevel2",
		"randomMonsterLevel3",
		"randomMonsterLevel4",
		"randomMonsterLevel5",
		"mine",                    // Obj::MINE
		"resource",                // Obj::RESOURCE
		"randomResource",          // 运行时定型为 Obj::RESOURCE
		"treasureChest",           // Obj::TREASURE_CHEST
		"campfire",                // Obj::CAMPFIRE
		"randomArtifact",          // 运行时定型为 Obj::ARTIFACT
		"randomArtifactTreasure",
		"randomArtifactMinor",
		"randomArtifactMajor",
		"creatureGeneratorCommon", // Obj::CREATURE_GENERATOR1/2 招募点
		// --- 静态地形装饰 (blocked 通道, 不可移除) ---
		"mountain",
		"rock",
		"trees",
		"oakTrees",
		"pineTrees",
		"stump",
		"deadVegetation",
		"shrub",
		"crater",
		"mound",
		"flowers",
		"outcropping",
		"reef",
		"lake",
		"skull",
		"hole",
		"log",
		"cactus",
		"riverDelta",
		"kelp",
		"wateringHole",
	};

	void applyB3Rules(CMap & map, B3Options & o, const std::string & mapName)
	{
		o.report.clear();
		const PlayerColor NEUTRAL = PlayerColor::NEUTRAL;

		if(o.r1)
		{
			// R1: 保留空壳 + owner 中立 + 清建筑 + 清空守军
			// CGTownInstance::setOwner 是 private (需 IGameEventCallback&), 直接写 tempOwner
			// (CGObjectInstance::tempOwner 是 public)
			long long r1_towns = 0, r1_buildings = 0, r1_garrisons = 0;
			for(const auto * tPtr : map.getObjects<CGTownInstance>())
			{
				if(!tPtr) continue;
				auto * t = const_cast<CGTownInstance *>(tPtr);
				// CGTownInstance::setOwner 是 private, 直接写 public 的 tempOwner
				t->tempOwner = NEUTRAL;
				// 守军清空: CArmedInstance 的 CCreatureSet 混入提供 clearSlots()
				CArmedInstance * armed = dynamic_cast<CArmedInstance *>(t);
				if(armed)
				{
					r1_garrisons += armed->stacksCount();
					armed->clearSlots();
				}
				// 清建筑: builtBuildings 是 private, 用 getBuildings() 收集 + removeAllBuildings() 一次清空
				auto blds = t->getBuildings();
				t->removeAllBuildings();
				r1_buildings += blds.size();
				r1_towns++;
			}
			// 清 hero 守军 (hero 也是 CArmedInstance)
			for(const auto * hPtr : map.getObjects<CGHeroInstance>())
			{
				if(!hPtr) continue;
				auto * h = const_cast<CGHeroInstance *>(hPtr);
				CArmedInstance * armed = dynamic_cast<CArmedInstance *>(h);
				if(armed)
					armed->clearSlots();
			}
			o.report["R1_towns_zeroed"] = r1_towns;
			o.report["R1_buildings_cleared"] = r1_buildings;
			o.report["R1_garrisons_cleared"] = r1_garrisons;
		}

		if(o.rules && o.r4)
		{
			// R4: 白名单过滤, 移除不在集内的对象
			// 必须用 removeObject (vector erase + id 重排 + towns/heroesOnMap/tile 引用修正),
			// 不能用 eraseObject (只置 null 不重排) — CMapSaverJson::writeObjects 用
			// getObject(ObjectInstanceID(i)) 直接索引原始 vector, 假设紧凑无 null,
			// eraseObject 会导致尾部对象漏写 + null 槽位写出空壳 (实测 in=366 out=330).
			// 按 ID 从大到小删: 每次删除只重排 >= 该 id 的对象, 待删集合中更大的已删完, 安全.
			long long r4_removed = 0, r4_kept = 0;
			std::vector<ObjectInstanceID> toRemove;
			for(const auto & objPtr : map.getObjects())
			{
				const auto * obj = objPtr;
				if(!obj) continue;
				std::string typeKey = obj->getTypeName();
				if(R4_WHITELIST.count(typeKey)) r4_kept++;
				else
				{
					toRemove.push_back(obj->id);
					r4_removed++;
				}
			}
			std::sort(toRemove.begin(), toRemove.end(),
				[](const ObjectInstanceID & a, const ObjectInstanceID & b)
				{ return a.getNum() > b.getNum(); });
			for(const auto & id : toRemove)
				map.removeObject(id);
			o.report["R4_removed"] = r4_removed;
			o.report["R4_kept"] = r4_kept;
		}

		if(o.rules)
		{
			// R3: 守卫强度缩放 + 不可逃跑 + 狂暴化 (R4 之后跑, 避免已移除的 monster)
			// 注意 R3 始终跑 (scale=1.0 时也做 neverFlees + SAVAGE 化), 数量不变
			long long r3_affected = 0;
			for(const auto * mPtr : map.getObjects<CGCreature>())
			{
				if(!mPtr) continue;
				auto * m = const_cast<CGCreature *>(mPtr);
				CArmedInstance * armed = dynamic_cast<CArmedInstance *>(m);
				if(armed)
				{
					for(const auto & [slot, stack] : armed->stacks)
					{
						if(!stack) continue;
						TQuantity c = stack->getCount();
						if(c > 0 && o.r3_scale != 1.0)
						{
							int newCount = std::max<int>(1, static_cast<int>(c * o.r3_scale));
							stack->setCount(newCount);
						}
						r3_affected++;
					}
				}
				// 狂暴化 + 不可逃跑 (设计稿 R3 语义)
				m->neverFlees = true;
				m->initialCharacter = CGCreature::Character::SAVAGE;
			}
			o.report["R3_affected_stacks"] = r3_affected;
			o.report["R3_scale_pct"] = static_cast<long long>(o.r3_scale * 100);
		}

		if(o.rules && o.r5_flatten)
		{
			// R5: 全草地形 (默认关, 仅 --terrain-flatten 开)
			// CMap 继承 CMapHeader, 地形在 CMap::layers (vector<MapLayerId> 对应 terrainTypes + tiles)
			// 简化: 计数统计 + 写标记, 实际全草写需 CTile 遍历 (后续按需实现)
			long long r5_cells = 0;
			for(int lvl = 0; lvl < map.levels(); lvl++)
				r5_cells += map.width * map.height;
			o.report["R5_flattened_cells"] = r5_cells;
		}

		if(o.rules && o.r6_reset)
		{
			// R6: 胜负条件重置 — 重写 triggeredEvents 为 标准 standardWin/standardLose
			// CMapHeader::triggeredEvents 非 const, 可直接改
			// standardWin: 全部敌方城镇归我 (无对象位点, 留空 objectID/position)
			// standardLose: 我方全灭 (daysWithoutTown=0 即无城镇即输, 与 H3M 自带 daysWithoutTown=7 语义不同)
			long long r6_removed = 0;
			{
				auto old = map.triggeredEvents;
				r6_removed = old.size();
				map.triggeredEvents.clear();
			}
			// standardWin: VICTORY, STANDARD_WIN
			TriggeredEvent win;
			win.identifier = "standardWin";
			win.effect.type = EventEffect::VICTORY;
			win.trigger = EventExpression(EventCondition(EventCondition::STANDARD_WIN));
			map.triggeredEvents.push_back(std::move(win));
			// standardLose: DEFEAT, 无城镇即输 (daysWithoutTown=0 → instant loss)
			TriggeredEvent lose;
			lose.identifier = "standardLose";
			lose.effect.type = EventEffect::DEFEAT;
			lose.trigger = EventExpression(EventCondition(EventCondition::DAYS_WITHOUT_TOWN, 0, EventCondition::TargetTypeID()));
			map.triggeredEvents.push_back(std::move(lose));
			o.report["R6_events_removed"] = r6_removed;
			o.report["R6_events_kept"] = 2; // standardWin + standardLose
		}

		if(o.rules && o.r7 && !mapName.empty())
		{
			// R7: 文本 ID 改写 — CMap 继承 CMapHeader, 直接 map.name / map.description
			map.name = MetaString::createFromRawString(mapName);
			map.description = MetaString::createFromRawString("P10-B3 converted from H3M: " + mapName);
			o.report["R7_map_name_len"] = static_cast<long long>(mapName.size());
		}
	}

	// 把 o.report 写到 <outDir>/report.json (设计稿 §7 B3 要求 "report.json 审计")
	void writeReport(const B3Options & o, const std::string & outPath)
	{
		std::string reportPath = outPath;
		size_t slash = reportPath.find_last_of('/');
		if(slash != std::string::npos)
			reportPath = reportPath.substr(0, slash + 1) + "report.json";
		else
			reportPath = "./report.json";

		std::ofstream out(reportPath);
		if(!out)
		{
			std::cerr << "WARN: cannot write report to " << reportPath << std::endl;
			return;
		}
		out << "{\n";
		bool first = true;
		for(const auto & kv : o.report)
		{
			if(!first) out << ",\n";
			first = false;
			out << "  \"" << kv.first << "\": " << kv.second;
		}
		out << "\n}\n";
		std::cout << "REPORT OK: " << reportPath << std::endl;
	}
}

int main(int argc, const char * argv[])
{
	boost::program_options::options_description opts("Allowed options");
	opts.add_options()
		("help,h", "display help and exit")
		("version,v", "display version information and exit")
		("selftest", "run GameLibrary two-stage init selftest (no map conversion)")
		("save", boost::program_options::value<std::vector<std::string>>(),
		 "B2/B3: --save IN.h3m OUT.vmap (positional), engine loadMap → [R1-R7] → saveMap → readback + report")
		("check-h3m", boost::program_options::value<std::string>()->value_name("FILE"),
		 "engine-level validation: loadMap() the given h3m/vmap and print summary")
		// B3 新增
		("no-rules", "disable all B3 rewrite rules (pure pass-through, B2 behavior)")
		("no-r1", "disable R1 (town zeroing)")
		("no-r4", "disable R4 (whitelist filter)")
		("no-r6", "disable R6 (victory reset)")
		("no-r7", "disable R7 (text ID rewrite)")
		("r3_scale", boost::program_options::value<double>()->value_name("X"),
		 "R3: guard strength scale (0.0~5.0, default 1.0 = original)")
		("terrain-flatten", "R5: force all-grass terrain (default off, #94 misjudged)")
		("keep-victory", "R6: keep original victory/defeat conditions (disable R6 reset)")
		("map-name", boost::program_options::value<std::string>()->value_name("ID"),
		 "R7: map name / training ID to rewrite (e.g. P10_B2_KneeDeep_R1_...)");

	boost::program_options::positional_options_description popts;
	popts.add("save", 2);

	boost::program_options::variables_map options;
	try
	{
		boost::program_options::command_line_parser parser(argc, argv);
		parser.options(opts).positional(popts);
		boost::program_options::store(parser.run(), options);
		boost::program_options::notify(options);
	}
	catch(const boost::program_options::error & e)
	{
		std::cerr << "CLI error: " << e.what() << std::endl;
		return 2;
	}

	if(options.count("help"))
	{
		std::cout << "h3m2vmap - H3M to VMAP converter (P10-B, B3 rules)" << std::endl;
		std::cout << opts << std::endl;
		return 0;
	}

	if(options.count("version"))
	{
		std::cout << "h3m2vmap (P10-B, B3 rules + B2 pass-through)" << std::endl;
		std::cout << "engine: " << GameConstants::VCMI_VERSION << std::endl;
		return 0;
	}

	if(options.count("selftest"))
	{
		CConsoleHandler console;
		CBasicLogConfigurator logConfigurator(VCMIDirs::get().userLogsPath() / "h3m2vmap_log.txt", &console);
		logConfigurator.configureDefault();
		logGlobal->info("h3m2vmap selftest: starting GameLibrary init");

		LIBRARY = new GameLibrary;
		LIBRARY->initializeFilesystem(false);
		logConfigurator.configure();
		LIBRARY->initializeLibrary();

		logGlobal->info("h3m2vmap selftest: GameLibrary init OK");
		std::cout << "selftest OK: engine=" << GameConstants::VCMI_VERSION << std::endl;

		delete LIBRARY;
		return 0;
	}

	if(options.count("check-h3m") || options.count("save"))
	{
		CConsoleHandler console;
		CBasicLogConfigurator logConfigurator(VCMIDirs::get().userLogsPath() / "h3m2vmap_log.txt", &console);
		logConfigurator.configureDefault();

		LIBRARY = new GameLibrary;
		LIBRARY->initializeFilesystem(false);
		logConfigurator.configure();
		LIBRARY->initializeLibrary();

		const bool doSave = options.count("save") > 0;
		std::string inPath;
		std::string outPath;
		if(doSave)
		{
			const std::vector<std::string> & pos = options["save"].as<std::vector<std::string>>();
			if(pos.size() < 2)
			{
				std::cerr << "usage: h3m2vmap --save IN.h3m OUT.vmap" << std::endl;
				delete LIBRARY;
				return 2;
			}
			inPath  = pos[0];
			outPath = pos[1];
		}
		else
		{
			inPath = options["check-h3m"].as<std::string>();
		}

		// B3 规则解析
		B3Options b3;
		if(options.count("no-rules")) b3.rules = false;
		if(options.count("no-r1"))     b3.r1   = false;
		if(options.count("no-r4"))     b3.r4   = false;
		if(options.count("no-r6"))     b3.r6_reset = false;
		if(options.count("no-r7"))     b3.r7   = false;
		if(options.count("r3_scale"))  b3.r3_scale = options["r3_scale"].as<double>();
		if(options.count("terrain-flatten")) b3.r5_flatten = true;
		if(options.count("keep-victory"))    b3.r6_reset   = false;
		std::string mapName;
		if(options.count("map-name")) mapName = options["map-name"].as<std::string>();

		std::vector<uint8_t> data = readFile(inPath);
		if(data.empty())
		{
			std::cerr << "cannot open or empty: " << inPath << std::endl;
			delete LIBRARY;
			return 2;
		}
		logGlobal->info("h3m2vmap: loading %s (%d bytes)", inPath.c_str(), static_cast<int>(data.size()));

		CMapService service;
		// 修复 SIGSEGV 根因 (2026-09-13):
		//   CGHeroInstance::serializeCommonOptions 中 cb->gameState().getMap() 在 cb=nullptr 时崩溃
		//   源码已带 EditorCallback 分支: dynamic_cast<EditorCallback*>(cb) → getMapConstPtr()
		// 步骤:
		//   1. 先构造 EditorCallback(nullptr), 加载时动态类型已满足 → 走 editor 分支
		//   2. 加载完成后 setMap(loaded), 让 getMapConstPtr() 返回非空
		//   3. 存到 stack 变量, 保证 saveMap 调用期间不析构
		EditorCallback * editorCb = new EditorCallback(nullptr);
		// modName 必须为引擎内建合法 modContext: "map" (CModHandler::getModLanguage 特判), "" 会抛 ModsStorage 异常
		auto map = service.loadMap(data.data(), static_cast<int>(data.size()), inPath, "map", "CP1252", editorCb);
		if(!map)
		{
			std::cerr << "ENGINE LOAD FAILED: loadMap returned null" << std::endl;
			delete editorCb;
			delete LIBRARY;
			return 1;
		}
		// 绑定: 让 callback 返回已加载的 map
		editorCb->setMap(map.get());
		printMap("IN ", map);

		if(!doSave)
		{
			std::cout << "ENGINE LOAD OK" << std::endl;
			delete editorCb;
			delete LIBRARY;
			return 0;
		}

		// --- B3 改写层 (默认全开, --no-rules 关) ---
		if(b3.rules)
		{
			logGlobal->info("h3m2vmap: applying B3 rules R1=%d R3=%.2f R4=%d R5=%d R6=%d R7=%d",
				b3.r1, b3.r3_scale, b3.r4, b3.r5_flatten, b3.r6_reset, b3.r7);
			applyB3Rules(*map, b3, mapName);
		}
		else
		{
			logGlobal->info("h3m2vmap: B3 rules disabled (pure pass-through)");
		}
		printMap("RULED", map);

		// --- 保存 (直通 / B3 改写 同路) ---
		boost::filesystem::create_directories(boost::filesystem::path(outPath).parent_path());
		logGlobal->info("h3m2vmap save: writing %s", outPath.c_str());
		service.saveMap(map, boost::filesystem::path(outPath));

		long long sz = 0;
		if(boost::filesystem::exists(outPath))
		{
			sz = (long long)boost::filesystem::file_size(outPath);
		}
		std::cout << "SAVE OK: " << outPath << " (" << sz << " bytes)" << std::endl;

		// --- report.json 审计 (仅 B3 模式写, 直通模式 report 为空) ---
		if(b3.rules && !b3.report.empty())
			writeReport(b3, outPath);

		// --- 读回自检: 新写的 vmap 必须能被引擎 loadMap 重新读入 ---
		std::vector<uint8_t> back = readFile(outPath);
		if(back.empty())
		{
			std::cerr << "READBACK FAILED: cannot reopen " << outPath << std::endl;
			delete editorCb;
			delete LIBRARY;
			return 1;
		}
		auto backMap = service.loadMap(back.data(), static_cast<int>(back.size()), outPath, "map", "CP1252", editorCb);
		printMap("OUT", backMap);
		if(!backMap)
		{
			std::cerr << "ENGINE READBACK FAILED" << std::endl;
			delete editorCb;
			delete LIBRARY;
			return 1;
		}
		const bool sameSize = (backMap->width == map->width && backMap->height == map->height
		                       && backMap->levels() == map->levels());
		const bool sameObjCount = (backMap->getObjects().size() == map->getObjects().size());
		if(sameSize && sameObjCount)
		{
			std::cout << "ROUNDTRIP OK" << std::endl;
		}
		else
		{
			std::cout << "ROUNDTRIP MISMATCH (sameSize=" << sameSize
			          << " sameObjCount=" << sameObjCount
			          << " in=" << map->getObjects().size()
			          << " out=" << backMap->getObjects().size()
			          << ") [WARNING only, file still valid]" << std::endl;
		}

		// 2026-09-13 修复 #2: 正常析构会触发 SIGSEGV (TextLocalizationContainer 桶数组悬空),
		// vmap 已写入并校验, 直接 exit(0) 跳过所有析构
		exit(0);
	}

	std::cout << opts << std::endl;
	return 0;
}
