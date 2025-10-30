# -*- coding: utf-8 -*-
"""
使用 Mihomo 代理池的 Selenium 访问脚本
"""
import os
import time
import random
import csv
import json
from datetime import datetime, timezone

import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ========== 配置区 ==========
CONFIG = {
    # 基础配置
    "URL": "https://google.com",
    "MAX_VISITS": 5,  # 最大访问次数，0表示无限
    "WAIT_AFTER_LOAD": 2,  # 页面加载后等待秒数
    
    # 访问间隔模式（两种模式）
    "INTERVAL_MODE": "poisson",  # 间隔模式：'fixed'（固定间隔）或 'poisson'（泊松分布，推荐）
    "INTERVAL_MEAN": 10,  # 间隔均值（秒）
    #   - fixed 模式：每次等待固定的 INTERVAL_MEAN 秒
    #   - poisson 模式：平均等待 INTERVAL_MEAN 秒，但每次随机（更自然，模拟真实用户）
    
    # 代理配置
    "USE_PROXY": True,  # 是否使用代理
    "HEADLESS": True,  # 是否使用无头模式（不打开浏览器窗口）
    "MIHOMO_API": "http://127.0.0.1:9090",  # Mihomo REST API 地址
    "MIHOMO_PROXY": "http://127.0.0.1:7892",  # Mihomo HTTP 代理地址（修正端口）
    "PROXY_GROUP": "NODE_TEST",  # Mihomo 代理组名称（用于读取节点列表）
    "SWITCH_GROUP": "GLOBAL",  # Mihomo 切换组名称（实际切换的组，流量走这个组）
    "PROXY_RESULTS": "/Users/ronchy2000/Documents/Developer/Workshop/Python_Study/爬虫学习/动态ip池/proxies/proxy_test_results.json",  # 测试结果文件
    "CSV_FILE": "visit_log.csv",  # 日志文件名
}

# ========== Mihomo 代理池类 ==========
class MihomoProxyPool:
    """Mihomo 代理池管理"""
    def __init__(self, results_file=None, api_url=None, group_name=None, switch_group=None):
        self.available_nodes = []
        self.failed_nodes = []
        if results_file is None:
            results_file = CONFIG["PROXY_RESULTS"]
        if api_url is None:
            api_url = CONFIG["MIHOMO_API"]
        if group_name is None:
            group_name = CONFIG["PROXY_GROUP"]
        if switch_group is None:
            switch_group = CONFIG["SWITCH_GROUP"]
        
        self.api_url = api_url
        self.group_name = group_name
        self.switch_group = switch_group
        self.load_test_results(results_file)
    
    def load_test_results(self, filepath):
        """从测试结果文件加载可用节点"""
        # 如果是相对路径，转换为相对于脚本目录的绝对路径
        if not os.path.isabs(filepath):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, filepath)
        
        if not os.path.exists(filepath):
            print(f"⚠️  测试结果文件不存在: {filepath}")
            return
        
        with open(filepath, "r", encoding="utf-8") as f:
            results = json.load(f)
        
        # 兼容 check_proxies.py 多种格式
        if "meta" in results:
            # 新格式: {"meta": {...}, "ok": [...], "failed": [...]}
            self.available_nodes = results.get("ok", [])
            self.failed_nodes = results.get("failed", [])
        elif "ok" in results:
            # 中间格式: {"ok": [...], "failed": [...]} (没有 meta)
            self.available_nodes = results.get("ok", [])
            self.failed_nodes = results.get("failed", [])
        else:
            # 旧格式: {"available": [...], "failed": [...]}
            self.available_nodes = results.get("available", [])
            self.failed_nodes = results.get("failed", [])
        
        print(f"✅ 加载 {len(self.available_nodes)} 个可用节点")
        if len(self.failed_nodes) > 0:
            print(f"ℹ️  {len(self.failed_nodes)} 个节点不可用")
    
    def get_random_node(self):
        """随机获取可用节点"""
        if not self.available_nodes:
            return None
        return random.choice(self.available_nodes)
    
    def switch_node(self, node_name):
        """切换 Mihomo 代理节点"""
        url = f"{self.api_url}/proxies/{self.switch_group}"
        payload = {"name": node_name}
        
        try:
            response = requests.put(url, json=payload, timeout=5)
            if response.status_code == 204:
                # 添加短暂延迟，等待节点切换生效
                time.sleep(0.3)
                return True, "切换成功"
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def get_current_ip(self):
        """获取当前出口 IP"""
        try:
            response = requests.get(
                "https://api.ipify.org?format=json",
                proxies={
                    "http": CONFIG["MIHOMO_PROXY"],
                    "https": CONFIG["MIHOMO_PROXY"]
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("ip")
        except:
            pass
        return None
    
    def __len__(self):
        return len(self.available_nodes)

# User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]

SCREEN_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 414, "height": 896},
    {"width": 390, "height": 844},
]

def get_log_file_path():
    """获取日志文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    return os.path.join(logs_dir, CONFIG["CSV_FILE"])

def now_iso():
    """返回当前时间（UTC）"""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def get_interval(mode="poisson", mean=10):
    """
    获取访问间隔时间
    
    Args:
        mode: 间隔模式
            - 'fixed': 固定间隔，每次返回 mean
            - 'poisson': 泊松分布（指数间隔），平均为 mean，但每次随机
        mean: 间隔均值（秒）
    
    Returns:
        float: 间隔时间（秒）
    
    数学原理：
        泊松过程描述的是事件随机发生的过程（如网站访问、排队到达等）
        在泊松过程中，两次事件之间的时间间隔服从指数分布
        参数 λ = 1/mean，即平均间隔时间的倒数
        
        为什么用泊松分布？
        1. 真实用户访问不是机械地每隔固定时间点击
        2. 泊松分布更自然，不易被检测为机器人
        3. 符合实际的网络流量规律
    """
    if mode == "fixed":
        # 固定间隔模式
        return mean
    elif mode == "poisson":
        # 泊松分布模式（指数间隔）
        # np.random.exponential(mean) 生成服从指数分布的随机数
        # 平均值为 mean，但每次都不同
        interval = np.random.exponential(mean)
        # 设置最小间隔为2秒，避免请求过于频繁
        return max(2.0, interval)
    else:
        # 未知模式，默认使用泊松分布
        print(f"⚠️  未知间隔模式 '{mode}'，使用默认泊松分布")
        interval = np.random.exponential(mean)
        return max(2.0, interval)

def get_random_device():
    """随机设备配置"""
    ua = random.choice(USER_AGENTS)
    screen = random.choice(SCREEN_SIZES)
    return ua, screen

def create_driver(user_agent, screen_size, use_proxy=False, headless=False):
    """创建Chrome驱动"""
    options = webdriver.ChromeOptions()
    
    # 无头模式设置
    if headless:
        options.add_argument('--headless=new')  # 使用新版无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        print(f"  👻 模式: 无头模式（后台运行）")
    else:
        print(f"  🖥️  模式: 显示浏览器窗口")
    
    # 设置User-Agent
    options.add_argument(f'user-agent={user_agent}')
    
    # 设置窗口大小
    options.add_argument(f'--window-size={screen_size["width"]},{screen_size["height"]}')
    
    # Mihomo 代理设置
    if use_proxy:
        proxy_address = CONFIG["MIHOMO_PROXY"]
        print(f"  🌐 代理: {proxy_address}")
        options.add_argument(f'--proxy-server={proxy_address}')
    else:
        print(f"  🌐 代理: 无")
    
    # 反检测设置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 创建driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def write_csv_header(csvfile):
    """写入CSV头"""
    with open(csvfile, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow([
                "timestamp_utc", "visit_number", "url", "proxy_node",
                "exit_ip", "user_agent", "screen_width", "screen_height",
                "status", "note"
            ])

def log_visit(visit_num, url, proxy_node, exit_ip, user_agent, screen_size, status, note=""):
    """记录访问日志"""
    log_file = get_log_file_path()
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            now_iso(), visit_num, url, proxy_node or "DIRECT",
            exit_ip or "N/A", user_agent, screen_size["width"], screen_size["height"],
            status, note
        ])

def visit_page(driver, url):
    """访问页面"""
    try:
        driver.get(url)
        time.sleep(CONFIG["WAIT_AFTER_LOAD"])
        
        # 获取页面标题
        page_title = driver.title[:50] if driver.title else "无标题"
        
        # 随机滚动
        scroll_times = random.randint(1, 3)
        for _ in range(scroll_times):
            scroll_amount = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
        
        if random.random() < 0.3:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))
        
        return "SUCCESS", page_title
    except Exception as e:
        return "ERROR", str(e)

def main():
    """主函数"""
    url = CONFIG["URL"]
    max_visits = CONFIG["MAX_VISITS"]
    use_proxy = CONFIG["USE_PROXY"]
    log_file = get_log_file_path()
    
    # 初始化 Mihomo 代理池
    proxy_pool = None
    if use_proxy:
        proxy_pool = MihomoProxyPool()
        if len(proxy_pool) == 0:
            print("⚠️  代理池为空，将不使用代理")
            use_proxy = False
    
    print(f"🚀 开始访问任务")
    print(f"📍 目标 URL: {url}")
    print(f"🔢 最大访问次数: {max_visits if max_visits > 0 else '无限'}")
    print(f"⏱️  间隔模式: {CONFIG['INTERVAL_MODE']} (均值: {CONFIG['INTERVAL_MEAN']}秒)")
    if CONFIG['INTERVAL_MODE'] == 'fixed':
        print(f"   → 固定间隔，每次等待 {CONFIG['INTERVAL_MEAN']} 秒")
    else:
        print(f"   → 泊松分布（指数间隔），平均 {CONFIG['INTERVAL_MEAN']} 秒，更自然")
    print(f"👻 无头模式: {'开启（后台运行）' if CONFIG['HEADLESS'] else '关闭（显示窗口）'}")
    print(f"🌐 使用代理: {'是' if use_proxy else '否'}")
    if use_proxy:
        print(f"📊 代理池大小: {len(proxy_pool)}")
        print(f"🔗 Mihomo API: {CONFIG['MIHOMO_API']}")
        print(f"🔌 Mihomo 代理: {CONFIG['MIHOMO_PROXY']}")
        print(f"🔄 切换代理组: {CONFIG['SWITCH_GROUP']}")
    print(f"💾 日志文件: {log_file}")
    print("-" * 60)
    
    write_csv_header(log_file)
    
    visit_count = 0
    driver = None
    
    try:
        while True:
            if max_visits > 0 and visit_count >= max_visits:
                print(f"\n✅ 已完成 {visit_count} 次访问")
                break
            
            visit_count += 1
            user_agent, screen_size = get_random_device()
            
            # 切换代理节点
            proxy_node = None
            exit_ip = None
            if use_proxy and proxy_pool:
                node = proxy_pool.get_random_node()
                if node:
                    node_name = node.get("name")
                    latency = node.get("latency_ms", node.get("latency", "N/A"))
                    
                    print(f"\n[访问 #{visit_count}]")
                    print(f"  🔄 切换节点: {node_name} (延迟: {latency}ms)")
                    
                    success, msg = proxy_pool.switch_node(node_name)
                    if success:
                        print(f"  ✅ 节点切换成功")
                        proxy_node = node_name
                        
                        # 验证 IP 地址
                        print(f"  🔍 查询出口 IP...")
                        exit_ip = proxy_pool.get_current_ip()
                        if exit_ip:
                            print(f"  🌍 当前 IP: {exit_ip}")
                        else:
                            print(f"  ⚠️  无法获取 IP")
                    else:
                        print(f"  ❌ 节点切换失败: {msg}")
            else:
                print(f"\n[访问 #{visit_count}]")
            
            # 关闭旧driver
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            print(f"  🖥️  设备: {screen_size['width']}x{screen_size['height']}")
            
            try:
                driver = create_driver(user_agent, screen_size, use_proxy, CONFIG["HEADLESS"])
                status, note = visit_page(driver, url)
                
                if status == "SUCCESS":
                    print(f"  ✅ 访问成功 - 页面: {note}")
                else:
                    print(f"  ❌ 访问失败: {note}")
                
                log_visit(visit_count, url, proxy_node, exit_ip, user_agent, screen_size, status, note)
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ 发生异常: {error_msg}")
                log_visit(visit_count, url, proxy_node, exit_ip, user_agent, screen_size, "EXCEPTION", error_msg)
            
            if max_visits == 0 or visit_count < max_visits:
                interval = get_interval(CONFIG["INTERVAL_MODE"], CONFIG["INTERVAL_MEAN"])
                mode_desc = "固定" if CONFIG["INTERVAL_MODE"] == "fixed" else "泊松分布"
                print(f"  ⏳ 等待 {interval:.1f} 秒（{mode_desc}）...")
                time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    
    finally:
        if driver:
            try:
                driver.quit()
                print("🔒 已关闭浏览器")
            except:
                pass
        
        print(f"\n📊 总访问次数: {visit_count}")
        print(f"💾 日志: {log_file}")

if __name__ == "__main__":
    main()