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

#include <fstream>
#include <iostream>
#include <vector>

int main(int argc, const char * argv[])
{
	boost::program_options::options_description opts("Allowed options");
	opts.add_options()
		("help,h", "display help and exit")
		("version,v", "display version information and exit")
		("selftest", "run GameLibrary two-stage init selftest (no map conversion)")
		("check-h3m", boost::program_options::value<std::string>()->value_name("FILE"),
		 "engine-level validation: loadMap() the given h3m/vmap and print summary");

	boost::program_options::variables_map options;
	try
	{
		boost::program_options::store(boost::program_options::parse_command_line(argc, argv, opts), options);
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
		return 0;
	}

	if(options.count("version"))
	{
		std::cout << "h3m2vmap (P10-B converter skeleton, B1)" << std::endl;
		std::cout << "engine: " << GameConstants::VCMI_VERSION << std::endl;
		return 0;
	}

	if(options.count("selftest"))
	{
		// 初始化序列 = serverapp/EntryPoint.cpp:72-92 同款 (设计稿 3.2)
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

	if(options.count("check-h3m"))
	{
		const std::string path = options["check-h3m"].as<std::string>();

		CConsoleHandler console;
		CBasicLogConfigurator logConfigurator(VCMIDirs::get().userLogsPath() / "h3m2vmap_log.txt", &console);
		logConfigurator.configureDefault();

		LIBRARY = new GameLibrary;
		LIBRARY->initializeFilesystem(false);
		logConfigurator.configure();
		LIBRARY->initializeLibrary();

		std::ifstream in(path, std::ios::binary);
		if(!in)
		{
			std::cerr << "cannot open " << path << std::endl;
			delete LIBRARY;
			return 2;
		}
		std::vector<uint8_t> data((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
		logGlobal->info("h3m2vmap check: loading %s (%d bytes)", path.c_str(), static_cast<int>(data.size()));

		CMapService service;
		// V1 实测: cb=nullptr 可用 (对象构造仅存指针, 未见解引用)
		// modName 必须为引擎内建合法 modContext: "map" (CModHandler::getModLanguage 特判), "" 会抛 ModsStorage 异常
		auto map = service.loadMap(data.data(), static_cast<int>(data.size()), path, "map", "CP1252", nullptr);
		if(!map)
		{
			std::cerr << "ENGINE LOAD FAILED: loadMap returned null" << std::endl;
			delete LIBRARY;
			return 1;
		}
		std::cout << "ENGINE LOAD OK: " << path << std::endl;
		std::cout << "  size=" << map->width << "x" << map->height
			<< " levels=" << map->levels()
			<< " objects=" << map->getObjects().size() << std::endl;

		delete LIBRARY;
		return 0;
	}

	std::cout << opts << std::endl;
	return 0;
}
