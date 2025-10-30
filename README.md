# 🌐 Mihomo 动态 IP 池系统

一个基于 Mihomo 的智能动态 IP 切换系统，支持自动切换代理节点访问网站，模拟真实用户行为。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)


## 📖 项目简介

### 🎯 动机与背景

在进行网络爬虫开发时，我们经常面临以下挑战：

1. **IP 封禁问题**：频繁访问同一网站容易被检测和封禁
2. **地理位置限制**：某些内容仅对特定地区开放
3. **反爬虫机制**：网站会识别机器人行为并限制访问
4. **大规模数据采集**：需要分布式 IP 来提高效率

**本项目提供了完整的解决方案：**
- ✅ 使用你自己的机场订阅，自动获取数百个代理节点
- ✅ 智能切换 IP 地址，每次请求使用不同的出口
- ✅ 模拟真实用户行为（泊松分布间隔、随机 UA 等）
- ✅ 无头浏览器运行，节省资源
- ✅ 完整的日志记录，便于分析和调试

---

## ✨ 功能特性

- 🔄 **动态 IP 切换**：每次访问自动切换不同的代理节点
- 📊 **智能间隔模式**：
  - 固定间隔（测试模式）
  - 泊松分布间隔（生产模式，模拟真实用户）
- 👻 **无头浏览器**：后台运行，不显示窗口
- 🎭 **反检测机制**：
  - 随机 User-Agent
  - 随机窗口大小
  - 随机滚动行为
- 📝 **完整日志**：记录每次访问的 IP、节点、时间等
- ⚡ **并发检测**：快速测试所有节点可用性（20 并发）
- 🛠️ **自动配置**：从机场订阅自动生成 Mihomo 配置

---

## 🚀 快速开始

### 前置要求

- **Python 3.8+**
- **Mihomo** (Clash Meta) 客户端
- **机场订阅链接** (支持 Clash/V2Ray 格式)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用流程

#### 第 1 步：获取代理节点

编辑 `fetch_proxies.py`，替换为你的机场订阅链接：

```python
subscriptions = [
    'https://your-airport.com/api/v1/client/subscribe?token=YOUR_TOKEN',
    # 可以添加多个订阅链接
]
```

运行脚本获取节点：

```bash
python fetch_proxies.py
```

**输出文件：**
- `proxies/raw_nodes.json` - 所有节点的 JSON 格式
- `proxies/raw_nodes.yaml` - Clash 格式的节点配置
- `proxies/all_proxies.txt` - 所有节点的 host:port 列表

#### 第 2 步：生成 Mihomo 配置

```bash
python generate_clash_profile.py
```

**输出文件：**
- `proxies/clash_profile.yaml` - 完整的 Mihomo 配置文件

#### 第 3 步：配置 Mihomo

1. 将生成的 `clash_profile.yaml` 导入 Mihomo 客户端
2. 启动 Mihomo
3. **重要：切换到全局模式（global）**

```bash
# 切换到全局模式
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs
```

#### 第 4 步：检测可用节点

```bash
python check_proxies.py
```

这个脚本会：
- 并发测试所有节点（默认 20 个并发）
- 测试目标：`https://www.google.com`
- 测试超时：8 秒
- 生成可用节点列表：`proxies/proxy_test_results.json`

#### 第 5 步：运行爬虫
> 刷取访问量等。

```bash
python selenium_with_proxy.py
```

---

## ⚙️ 配置说明

### 基础配置

编辑 `selenium_with_proxy.py` 中的 `CONFIG` 字典：

```python
CONFIG = {
    # 基础配置
    "URL": "https://google.com",        # 目标网址
    "MAX_VISITS": 5,                    # 访问次数（0=无限）
    "WAIT_AFTER_LOAD": 2,               # 页面加载后等待秒数
    
    # 访问间隔模式
    "INTERVAL_MODE": "poisson",         # 'fixed' 或 'poisson'
    "INTERVAL_MEAN": 10,                # 间隔均值（秒）
    
    # 代理配置
    "USE_PROXY": True,                  # 是否使用代理
    "HEADLESS": True,                   # 无头模式
    "MIHOMO_API": "http://127.0.0.1:9090",
    "MIHOMO_PROXY": "http://127.0.0.1:7892",
    "SWITCH_GROUP": "GLOBAL",           # 代理组名称
}
```

### 间隔模式详解

#### 固定间隔模式（测试用）

```python
"INTERVAL_MODE": "fixed",
"INTERVAL_MEAN": 10,  # 每次固定等待 10 秒
```

- ✅ 简单可控
- ❌ 容易被识别为机器人
- 📊 适用：快速测试、调试

#### 泊松分布模式（推荐）

```python
"INTERVAL_MODE": "poisson",
"INTERVAL_MEAN": 10,  # 平均等待 10 秒，但每次随机
```

- ✅ 模拟真实用户行为
- ✅ 不易被检测为机器人
- ✅ 符合网络流量统计规律
- 📊 适用：生产环境、大规模爬取

**数学原理：**

泊松过程（Poisson Process）描述的是事件随机发生的过程，如：
- 用户访问网站
- 电话呼叫到达
- 顾客到达商店

在泊松过程中，两次事件之间的时间间隔服从**指数分布**：

```
P(T > t) = e^(-λt)
其中 λ = 1/mean
```

这使得每次访问间隔不固定，但整体符合统计规律，更像真实用户。

---

## 📁 文件说明

| 文件 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `fetch_proxies.py` | 从机场订阅获取节点 | 订阅链接 | `raw_nodes.yaml/json` |
| `generate_clash_profile.py` | 生成 Mihomo 配置 | `raw_nodes.yaml` | `clash_profile.yaml` |
| `check_proxies.py` | 并发检测节点可用性 | `clash_profile.yaml` | `proxy_test_results.json` |
| `selenium_with_proxy.py` | 主程序：动态 IP 访问 | `proxy_test_results.json` | `logs/visit_log.csv` |
| `test_ip_switch_smart.py` | 智能测试脚本 | - | 终端输出 |

---

## 📊 运行示例

```bash
$ python selenium_with_proxy.py

✅ 加载 159 个可用节点
ℹ️  87 个节点不可用
🚀 开始访问任务
📍 目标 URL: https://google.com
🔢 最大访问次数: 5
⏱️  间隔模式: poisson (均值: 10秒)
   → 泊松分布（指数间隔），平均 10 秒，更自然
👻 无头模式: 开启（后台运行）
🌐 使用代理: 是
📊 代理池大小: 159
🔗 Mihomo API: http://127.0.0.1:9090
🔌 Mihomo 代理: http://127.0.0.1:7892
🔄 切换代理组: GLOBAL
------------------------------------------------------------

[访问 #1]
  🔄 切换节点: 🇯🇵日本全解锁 1.5X 01 (延迟: 599.0ms)
  ✅ 节点切换成功
  🔍 查询出口 IP...
  🌍 当前 IP: 156.246.92.93
  🖥️  设备: 1366x768
  👻 模式: 无头模式（后台运行）
  🌐 代理: http://127.0.0.1:7892
  ✅ 访问成功 - 页面: Google
  ⏳ 等待 3.9 秒（泊松分布）...

[访问 #2]
  🔄 切换节点: 🇵🇭 菲律宾【家宽】 (延迟: 995.0ms)
  ✅ 节点切换成功
  🔍 查询出口 IP...
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

# 查看特定 IP 的记录
grep "156.246.92.93" logs/visit_log.csv
```

**日志格式：**
```csv
timestamp_utc,visit_number,url,proxy_node,exit_ip,user_agent,screen_width,screen_height,status,note
2025-10-30T14:20:00Z,1,https://google.com,🇯🇵日本全解锁,156.246.92.93,Mozilla/5.0...,1366,768,SUCCESS,Google
```

---

## 🛠️ 常见问题

### Q1: IP 地址不切换？

**原因：** Mihomo 可能运行在 `rule` 模式

**解决：**
```bash
# 查看当前模式
curl http://127.0.0.1:9090/configs | grep mode

# 切换到 global 模式
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs
```

### Q2: 无法连接 Mihomo API？

**检查清单：**
1. Mihomo 是否正在运行？
2. API 端口是否正确？（默认 9090）
3. 是否设置了 secret？

### Q3: 所有节点检测都失败？

**可能原因：**
1. Mihomo 未启动或配置错误
2. 机场订阅已过期
3. 网络环境问题

**解决：**
```bash
# 重新获取节点
python fetch_proxies.py

# 重新生成配置
python generate_clash_profile.py

# 重新导入 Mihomo
```

### Q4: 部分节点可用，部分不可用？

这是正常的。机场节点质量参差不齐，建议：
- 使用延迟 < 500ms 的节点
- 定期运行 `check_proxies.py` 更新可用列表

---

## 📚 详细文档

- [Mihomo 完整教程](docs/MIHOMO_TUTORIAL.md) - Mihomo 配置、API 使用、故障排查
- [快速参考](docs/QUICK_START.md) - 常用命令和配置速查

---

## ⚡ 高级用法

### 筛选低延迟节点

```python
def get_fast_node(pool):
    """只选择延迟 < 500ms 的节点"""
    fast_nodes = [n for n in pool.available_nodes 
                  if n.get('latency_ms', 9999) < 500]
    return random.choice(fast_nodes) if fast_nodes else pool.get_random_node()
```

### 按国家筛选

```python
def get_hk_node(pool):
    """只使用香港节点"""
    hk_nodes = [n for n in pool.available_nodes 
                if '🇭🇰' in n['name'] or '香港' in n['name']]
    return random.choice(hk_nodes) if hk_nodes else None
```

### 权重随机选择

```python
def weighted_choice(nodes):
    """延迟越低，被选中概率越高"""
    weights = [1 / (n['latency_ms'] + 1) for n in nodes]
    return random.choices(nodes, weights=weights)[0]
```

---

## 🔒 安全提示

1. **不要泄露你的订阅链接**：`fetch_proxies.py` 中的订阅链接包含你的 token
2. **不要提交到公开仓库**：将 `fetch_proxies.py` 加入 `.gitignore`
3. **定期更换节点**：避免长期使用同一批 IP
4. **遵守目标网站的 robots.txt**
5. **控制访问频率**：避免对服务器造成过大压力

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

- **作者**: Ronchy2000
- **GitHub**: [Ronchy2000](https://github.com/ronchy2000)

---

## 🙏 致谢

- [Mihomo](https://github.com/MetaCubeX/mihomo) - 强大的代理工具
- [Selenium](https://www.selenium.dev/) - 浏览器自动化框架
- 所有为开源社区做出贡献的开发者

---

**最后更新：** 2025-10-30  
**版本：** 2.0
