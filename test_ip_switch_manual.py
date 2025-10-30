# -*- coding: utf-8 -*-
"""
快速测试 IP 切换功能
"""
import requests
import time
from selenium_with_proxy import MihomoProxyPool, CONFIG

def test_ip_switch():
    """测试IP切换"""
    print("🧪 测试 IP 切换功能\n")
    
    # 初始化代理池
    pool = MihomoProxyPool()
    print(f"✅ 加载了 {len(pool.available_nodes)} 个可用节点\n")
    print(f"🔄 切换组: {CONFIG['SWITCH_GROUP']}\n")
    print("-" * 60)
    
    # 测试3个随机节点
    for i in range(3):
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
        else:
            print(f"  ⚠️  无法获取IP")
        
        if i < 2:
            print(f"  ⏳ 等待3秒...")
            time.sleep(3)
    
    print("\n" + "-" * 60)
    print("✅ 测试完成！")
    print("\n💡 提示:")
    print("  - 如果每次IP都不同，说明切换成功")
    print("  - 如果IP相同，可能是节点共享同一个出口IP")
    print("  - 检查 SWITCH_GROUP 配置是否正确\n")
    print("  - 如果IP相同请执行\"python test_ip_switch_smart.py\".\n")

if __name__ == "__main__":
    test_ip_switch()

