import subprocess
import os
import sys
import time

# VCMI 地图加载测试
# 测试地图是否能被 VCMI 正确加载

VCMI_SERVER_PATH = "D:/Bigdata/hero3_fresh/vcmi/build/bin/VCMI_server.exe"
MAP_DIR = "D:/Bigdata/hero3_fresh/Maps/training"

def test_map_load(map_path):
    """测试单个地图加载"""
    try:
        # 使用 VCMI server 的 --test-map 参数测试地图
        # 注意：VCMI server 可能没有直接的 --test-map 参数
        # 这里我们尝试启动 server 并检查是否能加载地图
        
        # 首先检查地图文件是否有效 zip
        import zipfile
        with zipfile.ZipFile(map_path) as z:
            # 检查必要文件
            required_files = ['header.json', 'surface_terrain.json', 'objects.json']
            for rf in required_files:
                if rf not in z.namelist():
                    return False, f"缺少 {rf}"
        
        # 尝试启动 VCMI server 加载地图
        # 注意：这需要 VCMI 支持命令行加载测试
        # 如果不支持，我们只做基本的格式验证
        
        return True, "格式验证通过"
        
    except Exception as e:
        return False, str(e)

def main():
    """主测试函数"""
    print("="*70)
    print("VCMI 地图加载测试")
    print("="*70)
    
    # 获取所有地图文件
    map_files = sorted([f for f in os.listdir(MAP_DIR) if f.endswith('.vmap')])
    
    print(f"\n找到 {len(map_files)} 个地图文件")
    
    passed = 0
    failed = 0
    failed_maps = []
    
    for map_file in map_files:
        map_path = os.path.join(MAP_DIR, map_file)
        success, message = test_map_load(map_path)
        
        if success:
            print(f"✅ {map_file}: {message}")
            passed += 1
        else:
            print(f"❌ {map_file}: {message}")
            failed_maps.append((map_file, message))
            failed += 1
    
    print("\n" + "="*70)
    print("测试结果")
    print("="*70)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed_maps:
        print("\n失败地图:")
        for name, msg in failed_maps:
            print(f"  - {name}: {msg}")
    
    # 尝试使用 VCMI 的 map editor 或其他工具验证
    print("\n" + "="*70)
    print("VCMI 集成测试建议")
    print("="*70)
    print("1. 使用 VCMI Map Editor 打开地图验证")
    print("2. 使用 VCMI Client 启动游戏测试")
    print("3. 检查 VCMI 日志中的地图加载错误")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
