# h3m2vmap — 独立迷你 CMake 工程 (P10-B)
#
# 构建纪律 (设计稿 §3.1):
#   - 不进入 vcmi-native 根 CMake 树, 不触发 libvcmi 重编
#   - 只读链接 rel/bin/libvcmi.so (RelWithDebInfo, 已部署版本)
#   - 产物落在 tools/h3m2vmap/build/, 禁入 rel/
#
# 用法:
#   cmake -S <本目录> -B <本目录>/build
#   cmake --build <本目录>/build -j2   # 训练在跑, 并行度压低

cmake_minimum_required(VERSION 3.16)
project(h3m2vmap LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(VCMI_SOURCE_DIR "/home/administrator/vcmi-native" CACHE PATH "vcmi-native 源码根 (仅头文件引用)")
set(VCMI_LIB_DIR "/home/administrator/vcmi-native/rel/bin" CACHE PATH "已编译 libvcmi.so 所在目录 (只读引用, 禁覆盖)")

add_executable(h3m2vmap main.cpp)

target_include_directories(h3m2vmap PRIVATE
	${VCMI_SOURCE_DIR}
	${VCMI_SOURCE_DIR}/include
)

find_package(Boost 1.66 REQUIRED COMPONENTS program_options filesystem system)
target_link_libraries(h3m2vmap PRIVATE
	${VCMI_LIB_DIR}/libvcmi.so
	Boost::program_options
	Boost::filesystem
	Boost::system
)

# 运行时能找到 rel/bin 下的 vcmi 系 .so
set_target_properties(h3m2vmap PROPERTIES
	BUILD_RPATH "${VCMI_LIB_DIR}"
	INSTALL_RPATH "${VCMI_LIB_DIR}"
)
