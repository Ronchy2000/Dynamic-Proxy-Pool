# 🌐 Mihomo IP Rotator

基于 Mihomo 的动态 IP 切换系统，适用于网页爬虫、流量提升（CSDN/GitHub/博客）、数据采集等场景。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 📖 项目简介

### 为什么需要动态 IP？

在网络爬虫开发或提升网站流量时，经常遇到这些问题：

- **IP 被封禁**：频繁访问同一网站容易被检测
- **流量统计**：需要不同 IP 访问来增加真实浏览量
- **地理限制**：某些内容仅对特定地区开放
- **反爬机制**：网站会识别并限制机器人访问

### 解决方案

本项目提供完整的动态 IP 解决方案：

- ✅ 使用机场订阅，自动获取上百个代理节点
- ✅ 每次访问自动切换不同的出口 IP
- ✅ 泊松分布间隔，模拟真实用户行为
- ✅ 无头浏览器运行，节省资源
- ✅ 完整的访问日志记录

---

## ✨ 功能特性

- **动态 IP 切换**：每次访问使用不同的代理节点
- **智能间隔**：支持固定间隔和泊松分布两种模式
- **无头模式**：后台运行，不显示浏览器窗口
- **反检测**：随机 User-Agent、窗口大小、滚动行为
- **并发检测**：快速测试所有节点可用性（异步并发）
- **自动配置**：从机场订阅自动生成配置文件

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Chrome 浏览器
- Mihomo (Clash Meta) 客户端
- 机场订阅链接

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用流程

#### 步骤 1：获取代理节点

编辑 `fetch_proxies.py`，填入你的机场订阅链接：

```python
subscriptions = [
    'https://your-airport.com/api/v1/client/subscribe?token=YOUR_TOKEN',
    # 可以添加多个订阅
]
```

运行获取脚本：

```bash
python fetch_proxies.py
```

生成的文件：
- `proxies/raw_nodes.json` - JSON 格式节点数据
- `proxies/raw_nodes.yaml` - YAML 格式节点配置
- `proxies/all_proxies.txt` - 节点列表

#### 步骤 2：生成 Mihomo 配置

```bash
python generate_clash_profile.py
```

生成文件：`proxies/clash_profile.yaml`

#### 步骤 3：安装和配置 Mihomo

**下载 Mihomo：**

- macOS: [Clash Verge](https://github.com/clash-verge-rev/clash-verge-rev/releases) 或 [ClashX Meta](https://github.com/MetaCubeX/ClashX.Meta/releases)
- Windows: [Clash Verge](https://github.com/clash-verge-rev/clash-verge-rev/releases)
- Linux: [Mihomo Core](https://github.com/MetaCubeX/mihomo/releases)

**配置步骤：**

1. 打开 Mihomo 客户端
2. 导入配置文件 `proxies/clash_profile.yaml`
3. 启动 Mihomo
4. ⚠️ **重要**：切换到全局模式（Global）

**命令行验证：**

```bash
# 检查 Mihomo 状态
curl http://127.0.0.1:9090/configs

# 切换到全局模式
curl -X PATCH -H "Content-Type: application/json" -d '{"mode":"global"}' http://127.0.0.1:9090/configs
```

#### 步骤 4：检测可用节点

```bash
python check_proxies.py
```

这个脚本会并发测试所有节点，生成可用节点列表。

示例输出：
```
🚀 准备并发测试 246 个节点
   并发数: 20，超时: 8s

测试完成：
  ✅ 可用 159，失败 87，总计 246

💾 结果已写入: proxies/proxy_test_results.json
```

#### 步骤 5：测试 IP 切换

先运行基础测试：

```bash
python test_ip_switch_manual.py
```

期望输出（IP 应该不同）：
```
[测试 #1]
  🔄 切换到: 日本节点 (599ms)
  🌍 当前IP: 156.246.92.93

[测试 #2]
  🔄 切换到: 菲律宾节点 (995ms)
  🌍 当前IP: 61.245.11.176  ← IP 变了

[测试 #3]
  🔄 切换到: 新加坡节点 (397ms)
  🌍 当前IP: 185.234.56.78  ← 又变了
```

**如果 IP 没有变化**，运行智能诊断：

```bash
python test_ip_switch_smart.py
```

这个脚本会自动检查并修复 Mihomo 配置问题。

#### 步骤 6：开始使用

✅ 确认 IP 切换成功后：

```bash
python selenium_with_proxy.py
```

---

## ⚙️ 配置说明

编辑 `selenium_with_proxy.py` 的 `CONFIG` 部分：

```python
CONFIG = {
    # 基础配置
    "URL": "https://blog.csdn.net/your_article",  # 目标网址
    "MAX_VISITS": 100,                             # 访问次数
    "WAIT_AFTER_LOAD": 2,                          # 页面加载等待时间
    
    # 间隔模式
    "INTERVAL_MODE": "poisson",  # fixed 或 poisson
    "INTERVAL_MEAN": 15,          # 平均间隔（秒）
    
    # 代理设置
    "USE_PROXY": True,
    "HEADLESS": True,
    "MIHOMO_API": "http://127.0.0.1:9090",
    "MIHOMO_PROXY": "http://127.0.0.1:7892",
    "SWITCH_GROUP": "GLOBAL",
}
```

### 间隔模式说明

**固定间隔模式**（适合测试）：
```python
"INTERVAL_MODE": "fixed",
"INTERVAL_MEAN": 10,  # 每次等待 10 秒
```

**泊松分布模式**（推荐，更自然）：
```python
"INTERVAL_MODE": "poisson",
"INTERVAL_MEAN": 15,  # 平均 15 秒，但每次随机
```

泊松分布模拟真实用户访问行为。真实用户不会机械地每隔固定时间点击，而是有快有慢。泊松过程正好描述了这种随机事件的发生规律（比如网站访问、排队到达等），两次访问之间的时间间隔服从指数分布。

---

## 📁 文件说明

| 文件 | 功能 |
|------|------|
| `fetch_proxies.py` | 从机场订阅获取节点 |
| `generate_clash_profile.py` | 生成 Mihomo 配置文件 |
| `check_proxies.py` | 并发检测节点可用性 |
| `test_ip_switch_manual.py` | 快速测试 IP 切换 |
| `test_ip_switch_smart.py` | 智能诊断和自动修复 |
| `selenium_with_proxy.py` | 主程序：动态 IP 访问 |

---

## 📊 运行示例

```bash
$ python selenium_with_proxy.py

✅ 加载 159 个可用节点
🚀 开始访问任务
📍 目标 URL: https://blog.csdn.net/xxx
🔢 最大访问次数: 100
⏱️  间隔模式: poisson (均值: 15秒)
👻 无头模式: 开启
🌐 使用代理: 是
📊 代理池大小: 159
------------------------------------------------------------

[访问 #1]
  🔄 切换节点: 日本全解锁 (延迟: 599ms)
  ✅ 节点切换成功
  🔍 查询出口 IP...
  🌍 当前 IP: 156.246.92.93
  🖥️  设备: 1366x768
  👻 模式: 无头模式（后台运行）
  ✅ 访问成功 - 页面: CSDN博客
  ⏳ 等待 12.3 秒（泊松分布）...

[访问 #2]
  🔄 切换节点: 菲律宾家宽 (延迟: 995ms)
  ✅ 节点切换成功
  🌍 当前 IP: 61.245.11.176
  ...
```

---

## 🔍 查看日志

访问日志保存在 `logs/visit_log.csv`：

```bash
# 查看所有记录
cat logs/visit_log.csv

# 查看最近 10 条
tail -n 10 logs/visit_log.csv

# 统计不同 IP 数量
awk -F',' '{print $5}' logs/visit_log.csv | sort -u | wc -l
```

日志格式：
```csv
timestamp_utc,visit_number,url,proxy_node,exit_ip,user_agent,screen_width,screen_height,status,note
2025-10-30T14:20:00Z,1,https://blog.csdn.net/xxx,日本节点,156.246.92.93,Mozilla/5.0...,1366,768,SUCCESS,CSDN博客
```

---

## 🛠️ 常见问题

### ❓ IP 地址不切换？

**原因**：Mihomo 可能运行在 rule 模式

**解决方法**：
```bash
# 方法 1：运行智能诊断
python test_ip_switch_smart.py

# 方法 2：手动切换模式
curl -X PATCH -H "Content-Type: application/json" -d '{"mode":"global"}' http://127.0.0.1:9090/configs
```

### ❓ 无法连接 Mihomo API？

检查：
1. Mihomo 是否正在运行
2. API 端口是否正确（默认 9090）
3. 防火墙是否阻止

验证：
```bash
curl http://127.0.0.1:9090/configs
```

### ❓ 所有节点检测都失败？

可能原因：
- Mihomo 未启动或配置错误
- 机场订阅已过期
- 网络环境问题

解决步骤：
```bash
# 重新获取节点
python fetch_proxies.py

# 重新生成配置
python generate_clash_profile.py

# 重新导入 Mihomo
```

### ❓ Chrome 驱动下载失败？

```bash
# 使用国内镜像
export WDM_CHROME_DRIVER_MIRROR=https://npm.taobao.org/mirrors/chromedriver
python selenium_with_proxy.py
```

---

## 💡 高级用法

### 筛选低延迟节点

在 `selenium_with_proxy.py` 中添加：

```python
def get_fast_node(self, max_latency=500):
    """只使用延迟低于 max_latency ms 的节点"""
    fast_nodes = [n for n in self.available_nodes 
                  if n.get('latency_ms', 9999) < max_latency]
    return random.choice(fast_nodes) if fast_nodes else self.get_random_node()
```

### 按国家筛选节点

```python
def get_node_by_country(self, country='香港'):
    """按国家筛选节点"""
    country_map = {'香港': '🇭🇰', '新加坡': '🇸🇬', '日本': '🇯🇵', '美国': '🇺🇸'}
    flag = country_map.get(country, '')
    nodes = [n for n in self.available_nodes 
             if flag in n['name'] or country in n['name']]
    return random.choice(nodes) if nodes else None
```

### 定时任务

使用 crontab（Linux/macOS）：

```bash
# 每天早上 9 点运行
0 9 * * * cd /path/to/project && python selenium_with_proxy.py

# 每小时运行一次
0 * * * * cd /path/to/project && python selenium_with_proxy.py
```

---

## 🔒 安全提示

1. ⚠️ **不要泄露订阅链接**：包含你的 token，建议加入 `.gitignore`
2. 📝 **遵守网站规则**：查看目标网站的 `robots.txt`
3. ⏱️ **控制访问频率**：避免对服务器造成过大压力
4. ⚖️ **合法使用**：仅用于学习和合法用途

推荐的 `.gitignore` 配置：

```gitignore
# 敏感文件（包含订阅链接）
fetch_proxies.py

# 节点数据
proxies/
logs/

# Python
__pycache__/
*.pyc
*.pyo
```

---

## 📚 详细文档

- [Mihomo 完整教程](docs/MIHOMO_TUTORIAL.md) - 配置、API 使用、故障排查
- [快速参考手册](docs/QUICK_START.md) - 常用命令速查

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Mihomo](https://github.com/MetaCubeX/mihomo) - 代理工具
- [Selenium](https://www.selenium.dev/) - 浏览器自动化

---

**作者**: Ronchy2000  
**版本**: 2.0  
**更新**: 2025-10-30
