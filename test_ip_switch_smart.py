# -*- coding: utf-8 -*-
"""
智能 IP 切换测试 - 自动检查和修复配置
"""
import requests
import time
from selenium_with_proxy import MihomoProxyPool, CONFIG

def check_and_fix_mihomo():
    """检查并修复 Mihomo 配置"""
    print("🔍 检查 Mihomo 配置...")
    print("-" * 60)
    
    api_url = CONFIG["MIHOMO_API"]
    
    try:
        # 1. 检查 Mihomo 是否运行
        response = requests.get(f"{api_url}/configs", timeout=3)
        if response.status_code != 200:
            print("❌ Mihomo 未运行或 API 不可用")
            print("   请先启动 Mihomo 客户端")
            return False
        
        config = response.json()
        print("✅ Mihomo 运行正常")
        
        # 2. 检查运行模式
        current_mode = config.get("mode", "unknown")
        print(f"\n📋 当前模式: {current_mode}")
        
        if current_mode != "global":
            print(f"⚠️  模式不正确（需要 global 模式）")
            print(f"🔧 正在切换到 global 模式...")
            
            fix_response = requests.patch(
                f"{api_url}/configs",
                json={"mode": "global"},
                timeout=3
            )
            
            if fix_response.status_code == 204:
                print("✅ 已切换到 global 模式")
            else:
                print(f"❌ 切换失败 (HTTP {fix_response.status_code})")
                return False
        else:
            print("✅ 模式正确（global）")
        
        # 3. 检查端口配置
        http_port = config.get("port")
        socks_port = config.get("socks-port")
        mixed_port = config.get("mixed-port")
        
        print(f"\n🔌 端口配置:")
        print(f"   HTTP 端口: {http_port}")
        print(f"   SOCKS 端口: {socks_port}")
        print(f"   混合端口: {mixed_port}")
        
        # 提示正确的代理地址
        if http_port:
            print(f"\n💡 建议使用的代理地址: http://127.0.0.1:{http_port}")
            if CONFIG["MIHOMO_PROXY"] != f"http://127.0.0.1:{http_port}":
                print(f"⚠️  当前配置: {CONFIG['MIHOMO_PROXY']}")
                print(f"   建议修改 selenium_with_proxy.py 中的 MIHOMO_PROXY")
        
        # 4. 检查代理组配置
        print(f"\n🔄 代理组配置:")
        print(f"   切换组: {CONFIG['SWITCH_GROUP']}")
        
        group_response = requests.get(f"{api_url}/proxies/{CONFIG['SWITCH_GROUP']}", timeout=3)
        if group_response.status_code == 200:
            group_data = group_response.json()
            current_node = group_data.get("now", "unknown")
            print(f"   当前节点: {current_node}")
            print(f"✅ 代理组可用")
        else:
            print(f"❌ 代理组 {CONFIG['SWITCH_GROUP']} 不存在")
            return False
        
        print("\n" + "=" * 60)
        print("✅ Mihomo 配置检查完成，一切正常！")
        print("=" * 60 + "\n")
        return True
        
    except requests.RequestException as e:
        print(f"❌ 连接 Mihomo 失败: {e}")
        print("   请确认:")
        print("   1. Mihomo 已启动")
        print("   2. API 地址正确 (默认: http://127.0.0.1:9090)")
        print("   3. 如果设置了 secret，请在配置中添加")
        return False

def test_ip_switch(num_tests=3):
    """测试IP切换"""
    print("🧪 测试 IP 切换功能\n")
    
    # 初始化代理池
    pool = MihomoProxyPool()
    print(f"✅ 加载了 {len(pool.available_nodes)} 个可用节点\n")
    print("-" * 60)
    
    ip_list = []
    
    # 测试多个随机节点
    for i in range(num_tests):
        node = pool.get_random_node()
        if not node:
            print("❌ 没有可用节点")
            break
        
        node_name = node["name"]
        latency = node.get("latency_ms", "N/A")
        
        print(f"\n[测试 #{i+1}]")
        print(f"  🔄 切换到: {node_name} ({latency}ms)")
        
        # 切换节点
        success, msg = pool.switch_node(node_name)
        if not success:
            print(f"  ❌ 切换失败: {msg}")
            continue
        
        print(f"  ✅ 切换成功")
        
        # 查询IP
        print(f"  🔍 查询IP...")
        exit_ip = pool.get_current_ip()
        
        if exit_ip:
            print(f"  🌍 当前IP: {exit_ip}")
            ip_list.append(exit_ip)
        else:
            print(f"  ⚠️  无法获取IP")
        
        if i < num_tests - 1:
            print(f"  ⏳ 等待3秒...")
            time.sleep(3)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果统计")
    print("=" * 60)
    print(f"总测试次数: {num_tests}")
    print(f"成功获取IP: {len(ip_list)} 次")
    print(f"不同IP数量: {len(set(ip_list))} 个")
    
    if len(ip_list) > 0:
        print(f"\n获取到的IP列表:")
        for idx, ip in enumerate(ip_list, 1):
            print(f"  {idx}. {ip}")
    
    if len(set(ip_list)) == len(ip_list) and len(ip_list) == num_tests:
        print(f"\n✅ 完美！每次IP都不同，代理切换功能正常！")
    elif len(set(ip_list)) > 1:
        print(f"\n⚠️  部分IP重复，可能是某些节点共享出口IP")
    else:
        print(f"\n❌ 所有IP相同，代理切换可能未生效")
        print(f"   建议检查 Mihomo 模式是否为 global")
    
    print("=" * 60 + "\n")

def main():
    """主函数"""
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Mihomo 智能 IP 切换测试工具" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 步骤1: 检查并修复配置
    if not check_and_fix_mihomo():
        print("\n❌ 配置检查失败，无法继续测试")
        print("请按照上述提示修复问题后重试\n")
        return
    
    # 步骤2: 执行IP切换测试
    test_ip_switch(num_tests=3)
    
    # 步骤3: 提供使用提示
    print("💡 使用提示:")
    print("  1. Mihomo 必须运行在 global 模式")
    print("  2. 使用正确的代理端口（HTTP 或 SOCKS）")
    print("  3. 切换组配置要正确（默认: GLOBAL）")
    print("  4. 某些节点可能共享出口IP，这是正常的")
    print()

if __name__ == "__main__":
    main()

