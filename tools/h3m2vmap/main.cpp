/*
 * h3m2vmap, part of hero3_fresh P10-B
 *
 * H3M → VMAP 转换工具 (引擎内路径):
 *   CMapService::loadMap(.h3m) → CMapLoaderH3M → 内存 CMap
 *   → [B3 改写层 R1-R7, 本文件暂未实现]
 *   → CMapService::saveMap(.vmap) → CMapSaverJson → zip 三件套
 *
 * 设计稿: docs/P10-B-h3m2vmap转换器设计稿.md
 * B1 骨架: 仅 --version / --selftest, 验证 GameLibrary 两段初始化可用
 * B2 直通: --save IN.h3m OUT.vmap  引擎内 loadMap→saveMap 零改写, 保存后读回自检
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

#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>

#include <fstream>
#include <iostream>
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
}

int main(int argc, const char * argv[])
{
	boost::program_options::options_description opts("Allowed options");
	opts.add_options()
		("help,h", "display help and exit")
		("version,v", "display version information and exit")
		("selftest", "run GameLibrary two-stage init selftest (no map conversion)")
		("save", boost::program_options::value<std::vector<std::string>>(),
		 "B2: --save IN.h3m OUT.vmap (positional), engine loadMap→saveMap zero-rewrite")
		("check-h3m", boost::program_options::value<std::string>()->value_name("FILE"),
		 "engine-level validation: loadMap() the given h3m/vmap and print summary");

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
		std::cout << "h3m2vmap - H3M to VMAP converter (P10-B)" << std::endl;
		std::cout << opts << std::endl;
		std::cout << "Usage:" << std::endl;
		std::cout << "  h3m2vmap --check-h3m FILE" << std::endl;
		std::cout << "  h3m2vmap --save IN.h3m OUT.vmap" << std::endl;
		return 0;
	}

	if(options.count("version"))
	{
		std::cout << "h3m2vmap (P10-B, B1 skeleton + B2 pass-through)" << std::endl;
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

		std::vector<uint8_t> data = readFile(inPath);
		if(data.empty())
		{
			std::cerr << "cannot open or empty: " << inPath << std::endl;
			delete LIBRARY;
			return 2;
		}
		logGlobal->info("h3m2vmap: loading %s (%d bytes)", inPath.c_str(), static_cast<int>(data.size()));

		CMapService service;
		// V1 实测: cb=nullptr 可用 (对象构造仅存指针, 未见解引用)
		// modName 必须为引擎内建合法 modContext: "map" (CModHandler::getModLanguage 特判), "" 会抛 ModsStorage 异常
		auto map = service.loadMap(data.data(), static_cast<int>(data.size()), inPath, "map", "CP1252", nullptr);
		if(!map)
		{
			std::cerr << "ENGINE LOAD FAILED: loadMap returned null" << std::endl;
			delete LIBRARY;
			return 1;
		}
		printMap("IN ", map);

		if(!doSave)
		{
			std::cout << "ENGINE LOAD OK" << std::endl;
			delete LIBRARY;
			return 0;
		}

		// --- B2 直通: 零改写 saveMap 到 OUT ---
		boost::filesystem::create_directories(boost::filesystem::path(outPath).parent_path());
		logGlobal->info("h3m2vmap save: writing %s", outPath.c_str());
		service.saveMap(map, boost::filesystem::path(outPath));

		long long sz = 0;
		if(boost::filesystem::exists(outPath))
		{
			sz = (long long)boost::filesystem::file_size(outPath);
		}
		std::cout << "SAVE OK: " << outPath << " (" << sz << " bytes)" << std::endl;

		// --- 读回自检: 新写的 vmap 必须能被引擎 loadMap 重新读入 ---
		std::vector<uint8_t> back = readFile(outPath);
		if(back.empty())
		{
			std::cerr << "READBACK FAILED: cannot reopen " << outPath << std::endl;
			delete LIBRARY;
			return 1;
		}
		auto backMap = service.loadMap(back.data(), static_cast<int>(back.size()), outPath, "map", "CP1252", nullptr);
		printMap("OUT", backMap);
		if(!backMap)
		{
			std::cerr << "ENGINE READBACK FAILED" << std::endl;
			delete LIBRARY;
			return 1;
		}
		const bool sameSize = (backMap->width == map->width && backMap->height == map->height
		                       && backMap->levels() == map->levels());
		const bool sameObjCount = (backMap->getObjects().size() == map->getObjects().size());
		std::cout << (sameSize && sameObjCount ? "ROUNDTRIP OK" : "ROUNDTRIP MISMATCH")
			<< " (sameSize=" << sameSize << " sameObjCount=" << sameObjCount << ")" << std::endl;

		delete LIBRARY;
		return (sameSize && sameObjCount) ? 0 : 1;
	}

	std::cout << opts << std::endl;
	return 0;
}
