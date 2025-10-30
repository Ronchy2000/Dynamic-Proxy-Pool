# ⚡ 快速开始指南

## 🎯 5分钟上手

### 步骤1：启动 Mihomo
```bash
# 打开 Mihomo 客户端
# 确保显示"运行中"状态
```

### 步骤2：切换到全局模式
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"mode":"global"}' \
  http://127.0.0.1:9090/configs
```

### 步骤3：测试 IP 切换
```bash
cd /Users/ronchy2000/Documents/Developer/Workshop/Python_Study/爬虫学习/动态ip池
python test_ip_switch_smart.py
```

### 步骤4：运行爬虫
```bash
python selenium_with_proxy.py
```

---

## 📝 关键配置

### Mihomo 配置
```
模式: global （必须！）
API: http://127.0.0.1:9090
代理: http://127.0.0.1:7892
```

### 脚本配置 (selenium_with_proxy.py)
```python
CONFIG = {
    "HEADLESS": True,                    # 无头模式
    "USE_PROXY": True,                   # 使用代理
    "MIHOMO_PROXY": "http://127.0.0.1:7892",
    "SWITCH_GROUP": "GLOBAL",            # 切换组
    "MAX_VISITS": 5,                     # 访问次数
}
```

---

## 🔧 常用命令

### 检查 Mihomo 状态
```bash
curl http://127.0.0.1:9090/configs | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'模式: {d[\"mode\"]}\n端口: {d[\"port\"]}')"
```

### 切换模式
```bash
# 全局模式（IP 切换必须）
curl -X PATCH -H "Content-Type: application/json" -d '{"mode":"global"}' http://127.0.0.1:9090/configs

# 规则模式（日常使用）
curl -X PATCH -H "Content-Type: application/json" -d '{"mode":"rule"}' http://127.0.0.1:9090/configs
```

### 测试当前 IP
```bash
curl -x http://127.0.0.1:7892 https://api.ipify.org?format=json
```

---

## ❗ 故障排查

### IP 不切换？
1. 检查模式：`必须是 global`
2. 检查端口：`7892（HTTP）或 7891（SOCKS）`
3. 重启 Mihomo

### 无法连接？
1. Mihomo 是否启动？
2. API 端口是否正确？（9090）
3. 防火墙是否阻止？

---

## 📚 详细文档

查看完整教程：`MIHOMO_TUTORIAL.md`

