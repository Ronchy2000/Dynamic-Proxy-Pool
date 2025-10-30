# 🚀 Mihomo 动态 IP 池完整教程

## 📚 目录
1. [Mihomo 基础概念](#1-mihomo-基础概念)
2. [Mihomo 配置详解](#2-mihomo-配置详解)
3. [运行模式说明](#3-运行模式说明)
4. [API 使用指南](#4-api-使用指南)
5. [常见问题解决](#5-常见问题解决)
6. [脚本使用教程](#6-脚本使用教程)

---

## 1. Mihomo 基础概念

### 1.1 什么是 Mihomo？
Mihomo（原 Clash Meta）是一个强大的代理工具，支持：
- ✅ 多种代理协议（Shadowsocks, VMess, Trojan 等）
- ✅ 规则路由（国内直连，国外代理）
- ✅ 代理组切换
- ✅ RESTful API 控制

### 1.2 核心组件

```
┌─────────────────────────────────────────┐
│           Mihomo 核心引擎               │
├─────────────────────────────────────────┤
│  代理服务器 (7890/7891/7892)           │
│  - HTTP Proxy                           │
│  - SOCKS5 Proxy                         │
│  - Mixed Port                           │
├─────────────────────────────────────────┤
│  API 服务器 (9090)                      │
│  - 控制运行模式                         │
│  - 切换代理节点                         │
│  - 查询状态信息                         │
└─────────────────────────────────────────┘
```

---

## 2. Mihomo 配置详解

### 2.1 配置文件位置
- **macOS**: `~/.config/mihomo/config.yaml`
- **Windows**: `C:\Users\<用户名>\.config\mihomo\config.yaml`

### 2.2 关键配置项

```yaml
# 基础设置
port: 7892                    # HTTP 代理端口
socks-port: 7891             # SOCKS5 代理端口
mixed-port: 7890             # 混合端口（推荐）
allow-lan: false             # 是否允许局域网连接

# API 设置
external-controller: '127.0.0.1:9090'  # API 地址
secret: ''                   # API 密钥（可选）

# 运行模式
mode: rule                   # rule/global/direct

# 代理节点
proxies:
  - name: "🇭🇰 香港01"
    type: ss
    server: xxx.xxx.xxx.xxx
    port: 8388
    # ... 其他配置

# 代理组
proxy-groups:
  - name: GLOBAL
    type: select
    proxies:
      - NODE_TEST
      - DIRECT
  
  - name: NODE_TEST
    type: select
    proxies:
      - 🇭🇰 香港01
      - 🇸🇬 新加坡01
      - 🇯🇵 日本01
```

---

## 3. 运行模式说明

### 3.1 三种模式对比

| 模式 | 流量路由 | 使用场景 | IP 切换 |
|------|---------|---------|---------|
| **rule** | 按规则自动选择 | 日常使用 | ❌ 不适用 |
| **global** | 所有流量走代理 | IP 切换 | ✅ 必须用 |
| **direct** | 所有流量直连 | 不用代理 | ❌ 不适用 |

### 3.2 切换模式

#### 方法1：使用 API
```bash
# 切换到 global 模式
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs

# 切换到 rule 模式
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"rule"}' \
  http://127.0.0.1:9090/configs
```

#### 方法2：使用客户端界面
- 打开 Mihomo 图形界面
- 找到"模式"或"Mode"选项
- 选择"全局"或"Global"

### 3.3 为什么 IP 切换必须用 global 模式？

**rule 模式的问题：**
```
你的请求 → Mihomo 规则引擎
                ↓
         检查目标网站
                ↓
    是国内网站？ → DIRECT (直连，不走代理)
    是国外网站？ → 查看规则 → 可能走固定节点
```
**结果：** 即使切换了节点，规则可能强制使用其他路径！

**global 模式的行为：**
```
你的请求 → Mihomo → 当前选中的节点 → 目标网站
```
**结果：** 所有流量都走选中的节点，IP 切换生效！

---

## 4. API 使用指南

### 4.1 常用 API 端点

#### 查询配置信息
```bash
curl http://127.0.0.1:9090/configs
```

#### 切换运行模式
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs
```

#### 获取所有代理组
```bash
curl http://127.0.0.1:9090/proxies
```

#### 获取特定代理组信息
```bash
curl http://127.0.0.1:9090/proxies/GLOBAL
```

#### 切换代理节点
```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"name":"🇭🇰 香港01"}' \
  http://127.0.0.1:9090/proxies/GLOBAL
```

### 4.2 Python API 封装

```python
import requests

class MihomoAPI:
    def __init__(self, api_url="http://127.0.0.1:9090", secret=""):
        self.api_url = api_url
        self.headers = {}
        if secret:
            self.headers["Authorization"] = f"Bearer {secret}"
    
    def get_config(self):
        """获取配置"""
        response = requests.get(f"{self.api_url}/configs", headers=self.headers)
        return response.json()
    
    def set_mode(self, mode):
        """设置模式：rule/global/direct"""
        response = requests.patch(
            f"{self.api_url}/configs",
            json={"mode": mode},
            headers=self.headers
        )
        return response.status_code == 204
    
    def switch_node(self, group, node_name):
        """切换节点"""
        response = requests.put(
            f"{self.api_url}/proxies/{group}",
            json={"name": node_name},
            headers=self.headers
        )
        return response.status_code == 204
```

---

## 5. 常见问题解决

### 问题1: IP 切换不生效

**症状：** 切换节点后，IP 地址不变

**原因：**
1. ❌ Mihomo 运行在 `rule` 模式
2. ❌ 代理端口配置错误
3. ❌ 切换的不是实际使用的代理组

**解决方案：**
```bash
# 1. 切换到 global 模式
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs

# 2. 检查端口配置
curl http://127.0.0.1:9090/configs | grep -E 'port|mode'

# 3. 确认切换正确的代理组（通常是 GLOBAL）
```

### 问题2: 无法连接 Mihomo API

**症状：** `Connection refused` 或超时

**解决方案：**
1. 确认 Mihomo 已启动
2. 检查 API 地址和端口（默认 9090）
3. 检查是否设置了 `secret`（需要在请求头中添加）

```bash
# 测试 API 连接
curl http://127.0.0.1:9090/configs
```

### 问题3: 某些节点 IP 相同

**原因：** 多个节点可能共享同一个出口服务器

**解决方案：** 这是正常的，选择其他节点即可

---

## 6. 脚本使用教程

### 6.1 准备工作

1. **启动 Mihomo**
   ```bash
   # 确保 Mihomo 正在运行
   # 可以通过图形界面或命令行启动
   ```

2. **检查节点**
   ```bash
   cd /Users/ronchy2000/Documents/Developer/Workshop/Python_Study/爬虫学习/动态ip池
   python check_proxies.py
   ```

### 6.2 测试 IP 切换

#### 使用智能测试脚本（推荐）
```bash
python test_ip_switch_smart.py
```

这个脚本会：
- ✅ 自动检查 Mihomo 配置
- ✅ 自动切换到 global 模式
- ✅ 测试 3 个随机节点
- ✅ 显示详细的统计信息

#### 使用基础测试脚本
```bash
python test_ip_switch.py
```

### 6.3 运行爬虫

```bash
python selenium_with_proxy.py
```

**配置说明：**
```python
CONFIG = {
    "URL": "https://google.com",        # 目标网址
    "MAX_VISITS": 5,                    # 访问次数
    "HEADLESS": True,                   # 无头模式
    "USE_PROXY": True,                  # 使用代理
    "MIHOMO_PROXY": "http://127.0.0.1:7892",  # 代理地址
    "SWITCH_GROUP": "GLOBAL",           # 切换组
}
```

### 6.4 查看日志

```bash
# 查看访问日志
cat logs/visit_log.csv

# 查看最近10条
tail -n 10 logs/visit_log.csv
```

---

## 7. 快速命令参考

### 7.1 Mihomo 控制命令

```bash
# 查看当前模式
curl -s http://127.0.0.1:9090/configs | python3 -c "import sys,json; print('模式:', json.load(sys.stdin)['mode'])"

# 切换到 global 模式
curl -X PATCH -H "Content-Type: application/json" -d '{"mode":"global"}' http://127.0.0.1:9090/configs

# 查看当前选中节点
curl -s http://127.0.0.1:9090/proxies/GLOBAL | python3 -c "import sys,json; print('当前节点:', json.load(sys.stdin)['now'])"

# 切换节点
curl -X PUT -H "Content-Type: application/json" -d '{"name":"节点名"}' http://127.0.0.1:9090/proxies/GLOBAL

# 查询当前 IP
curl -x http://127.0.0.1:7892 https://api.ipify.org?format=json
```

### 7.2 脚本运行命令

```bash
# 1. 检查代理节点
python check_proxies.py

# 2. 智能测试 IP 切换
python test_ip_switch_smart.py

# 3. 运行爬虫（无头模式）
python selenium_with_proxy.py
```

---

## 8. 最佳实践

### 8.1 日常使用流程

```bash
# 1. 启动 Mihomo
# 2. 生成/更新节点配置
python generate_clash_profile.py

# 3. 检测可用节点
python check_proxies.py

# 4. 测试 IP 切换
python test_ip_switch_smart.py

# 5. 运行爬虫任务
python selenium_with_proxy.py
```

### 8.2 性能优化建议

1. **选择低延迟节点**
   - 延迟 < 500ms: 优秀
   - 延迟 500-1000ms: 可用
   - 延迟 > 1000ms: 较慢

2. **避免频繁切换**
   - 每次切换等待 0.3-1 秒
   - 使用泊松分布间隔访问

3. **监控失败率**
   - 定期运行 `check_proxies.py`
   - 删除持续失败的节点

---

## 9. 故障排查清单

- [ ] Mihomo 是否正在运行？
- [ ] API 端口是否正确（默认 9090）？
- [ ] 运行模式是否为 `global`？
- [ ] 代理端口是否匹配（7890/7891/7892）？
- [ ] 代理组配置是否正确（GLOBAL）？
- [ ] 节点列表是否为空？
- [ ] 网络连接是否正常？

---

## 10. 进阶技巧

### 10.1 按国家筛选节点

```python
# 只使用香港节点
hk_nodes = [n for n in pool.available_nodes if '🇭🇰' in n['name'] or '香港' in n['name']]
```

### 10.2 按延迟筛选节点

```python
# 只使用低延迟节点（< 500ms）
fast_nodes = [n for n in pool.available_nodes if n.get('latency_ms', 9999) < 500]
```

### 10.3 权重随机选择

```python
import random

def weighted_choice(nodes):
    """延迟越低，被选中概率越高"""
    weights = [1 / (n['latency_ms'] + 1) for n in nodes]
    return random.choices(nodes, weights=weights)[0]
```

---

## 📞 获取帮助

如果遇到问题：
1. 运行 `python test_ip_switch_smart.py` 查看详细诊断
2. 检查 Mihomo 日志
3. 参考本文档的"常见问题"部分

---

**最后更新：** 2025-10-30
**版本：** 1.0

