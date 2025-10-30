"""
从机场订阅获取代理节点
支持 Clash/V2Ray 等多种订阅格式
"""
import os
import requests
import base64
import yaml
import json
import re


def safe_base64_decode(data: str) -> bytes:
    """解码可能缺少填充的 Base64 字符串。"""
    padding = (-len(data)) % 4
    return base64.b64decode(data + "=" * padding)

def get_proxies_dir():
    """获取代理文件目录"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    proxies_dir = os.path.join(script_dir, "proxies")
    if not os.path.exists(proxies_dir):
        os.makedirs(proxies_dir)
    return proxies_dir

def parse_vmess(link: str):
    """解析 vmess:// 链接并返回节点描述。"""
    try:
        raw_payload = link.strip().replace('vmess://', '', 1)
        decoded = safe_base64_decode(raw_payload).decode('utf-8')
        config = json.loads(decoded)
        server = config.get('add')
        port = config.get('port')
        name = config.get('ps') or f"vmess-{server}:{port}"
        if server and port:
            return {
                "name": name,
                "type": "vmess",
                "server": server,
                "port": int(port),
                "config": config,
                "raw_link": link.strip(),
            }
    except Exception:
        return {
            "name": "vmess-raw",
            "type": "vmess",
            "server": None,
            "port": None,
            "config": None,
            "raw_link": link.strip(),
        }
    return None

def parse_ss(link: str):
    """解析 ss:// 链接并返回节点描述。"""
    raw = link.strip()
    body = raw.replace('ss://', '', 1)
    # ss 链接可能包含 fragment，先剥离
    fragment = ''
    if '#' in body:
        body, fragment = body.split('#', 1)
    try:
        decoded = safe_base64_decode(body).decode('utf-8')
    except Exception:
        decoded = body

    server = None
    port = None
    if '@' in decoded:
        try:
            _, server_part = decoded.rsplit('@', 1)
            if ':' in server_part:
                server, port = server_part.split(':', 1)
        except ValueError:
            pass

    name = fragment or f"ss-{server}:{port}" if server and port else "ss-node"
    return {
        "name": name,
        "type": "ss",
        "server": server,
        "port": int(port) if port and port.isdigit() else None,
        "config": None,
        "raw_link": raw,
    }

def parse_trojan(link: str):
    """解析 trojan:// 链接并返回节点描述。"""
    raw = link.strip()
    body = raw.replace('trojan://', '', 1)
    server = None
    port = None
    password = None
    name = "trojan-node"

    try:
        if '@' in body:
            credential, server_part = body.split('@', 1)
            password = credential
            server_part = server_part.split('#')[0].split('?')[0]
            if ':' in server_part:
                server, port = server_part.split(':', 1)
        if '#' in raw:
            name = raw.split('#', 1)[1]
    except ValueError:
        pass

    return {
        "name": name or f"trojan-{server}:{port}",
        "type": "trojan",
        "server": server,
        "port": int(port) if port and port.isdigit() else None,
        "config": {
            "type": "trojan",
            "password": password,
            "server": server,
            "port": int(port) if port and port.isdigit() else None,
            "name": name or f"trojan-{server}:{port}",
        } if server and port and password else None,
        "raw_link": raw,
    }

def collect_from_yaml(config, source_url):
    """从 Clash YAML 配置中提取节点。"""
    nodes = []
    proxies = config.get('proxies') if isinstance(config, dict) else None
    if not proxies:
        return nodes

    for proxy in proxies:
        if not isinstance(proxy, dict):
            continue
        server = proxy.get('server')
        port = proxy.get('port')
        name = proxy.get('name') or f"{server}:{port}"
        nodes.append({
            "name": name,
            "type": proxy.get('type', 'unknown'),
            "server": server,
            "port": port,
            "config": proxy,
            "raw_link": None,
            "source": source_url,
        })
    return nodes


def fetch_from_clash_subscription(subscription_url):
    """从订阅链接获取节点描述列表。"""
    try:
        print(f"🔄 正在获取订阅: {subscription_url[:50]}...")

        headers = {'User-Agent': 'ClashForAndroid/2.5.12'}
        response = requests.get(subscription_url, headers=headers, timeout=30)
        response.raise_for_status()

        content = response.text
        nodes = []

        # 方式 1：直接解析为 YAML
        try:
            config = yaml.safe_load(content)
            if isinstance(config, dict):
                yaml_nodes = collect_from_yaml(config, subscription_url)
                if yaml_nodes:
                    print("  ✅ YAML 格式解析成功")
                    return yaml_nodes
        except Exception:
            pass

        # 方式 2：尝试 Base64 解码后解析
        try:
            decoded_text = safe_base64_decode(content.strip()).decode('utf-8')
            try:
                config = yaml.safe_load(decoded_text)
                if isinstance(config, dict):
                    yaml_nodes = collect_from_yaml(config, subscription_url)
                    if yaml_nodes:
                        print("  ✅ Base64+YAML 格式解析成功")
                        return yaml_nodes
            except Exception:
                pass

            for line in decoded_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('vmess://'):
                    node = parse_vmess(line)
                elif line.startswith('ss://'):
                    node = parse_ss(line)
                elif line.startswith('trojan://'):
                    node = parse_trojan(line)
                else:
                    node = None
                if node:
                    node["source"] = subscription_url
                    nodes.append(node)
            if nodes:
                print("  ✅ Base64+节点列表解析成功")
                return nodes
        except Exception:
            pass

        # 方式 3：逐行解析节点链接
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('vmess://'):
                node = parse_vmess(line)
            elif line.startswith('ss://'):
                node = parse_ss(line)
            elif line.startswith('trojan://'):
                node = parse_trojan(line)
            elif re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', line):
                server, port = line.split(':', 1)
                node = {
                    "name": f"raw-{server}:{port}",
                    "type": "raw",
                    "server": server,
                    "port": int(port),
                    "config": None,
                    "raw_link": line,
                }
            else:
                node = None

            if node:
                node["source"] = subscription_url
                nodes.append(node)

        if nodes:
            print("  ✅ 节点链接解析成功")
        return nodes

    except Exception as err:
        print(f"❌ 获取订阅失败: {err}")
        import traceback
        traceback.print_exc()
        return []

def save_nodes(nodes):
    """将节点列表保存为多种格式，便于后续使用。"""
    proxies_dir = get_proxies_dir()

    json_path = os.path.join(proxies_dir, "raw_nodes.json")
    yaml_path = os.path.join(proxies_dir, "raw_nodes.yaml")
    links_path = os.path.join(proxies_dir, "raw_links.txt")
    hosts_path = os.path.join(proxies_dir, "all_proxies.txt")

    try:
        with open(json_path, 'w', encoding='utf-8') as f_json:
            json.dump(nodes, f_json, ensure_ascii=False, indent=2)

        clash_nodes = [node["config"] for node in nodes if isinstance(node.get("config"), dict)]
        if clash_nodes:
            with open(yaml_path, 'w', encoding='utf-8') as f_yaml:
                yaml.safe_dump({"proxies": clash_nodes}, f_yaml, allow_unicode=True, sort_keys=False)
        else:
            if os.path.exists(yaml_path):
                os.remove(yaml_path)

        raw_links = [node["raw_link"] for node in nodes if node.get("raw_link")]
        if raw_links:
            with open(links_path, 'w', encoding='utf-8') as f_links:
                for link in raw_links:
                    f_links.write(link + '\n')
        else:
            if os.path.exists(links_path):
                os.remove(links_path)

        host_entries = []
        for node in nodes:
            server = node.get("server")
            port = node.get("port")
            if server and port:
                host_entries.append(f"{server}:{port}")
        if host_entries:
            with open(hosts_path, 'w', encoding='utf-8') as f_hosts:
                for entry in sorted(set(host_entries)):
                    f_hosts.write(entry + '\n')

        print(f"✅ 已生成节点数据：\n  JSON -> {json_path}\n  YAML -> {yaml_path if clash_nodes else '无可用 Clash 节点'}\n  HOST -> {hosts_path}")
    except Exception as err:
        print(f"❌ 保存节点数据失败: {err}")


def debug_subscription(subscription_url):
    """调试订阅内容"""
    try:
        print(f"\n🔍 调试模式: 查看订阅原始内容")
        headers = {
            'User-Agent': 'ClashForAndroid/2.5.12'
        }
        response = requests.get(subscription_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        print(f"\n📄 原始内容前500字符:")
        print("="*60)
        print(content[:500])
        print("="*60)
        
        # 尝试 base64 解码
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            print(f"\n📄 Base64解码后前500字符:")
            print("="*60)
            print(decoded[:500])
            print("="*60)
        except:
            print("\n⚠️  不是 Base64 编码")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")

def main():
    """主函数"""
    # 你的机场订阅链接（支持多个）
    subscriptions = [
        '订阅1',
        '订阅2',
        '订阅3'
        # 可以添加更多订阅链接
    ]
    
    # 先调试第一个订阅，看看返回的是什么格式
    if subscriptions:
        debug_subscription(subscriptions[0])
    
    print("\n" + "="*60)
    print("开始解析订阅...")
    print("="*60 + "\n")
    
    all_nodes = []
    
    for sub_url in subscriptions:
        nodes = fetch_from_clash_subscription(sub_url)
        all_nodes.extend(nodes)
        print(f"  获取到 {len(nodes)} 个节点\n")

    if all_nodes:
        # 去重：根据 type+server+port+name
        seen = set()
        unique_nodes = []
        for node in all_nodes:
            key = (
                node.get("type"),
                node.get("server"),
                node.get("port"),
                node.get("name"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_nodes.append(node)

        save_nodes(unique_nodes)
        print(f"\n📊 总共获取 {len(unique_nodes)} 个节点描述")
    else:
        print("❌ 未获取到任何代理")
        print("\n💡 提示:")
        print("1. 检查订阅链接是否正确")
        print("2. 查看上面的调试信息，确认订阅格式")
        print("3. 可能需要根据实际格式修改解析代码")

if __name__ == '__main__':
    main()