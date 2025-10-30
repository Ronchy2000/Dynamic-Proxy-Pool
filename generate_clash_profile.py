# -*- coding: utf-8 -*-
"""根据 fetch_proxies 生成的 raw_nodes.yaml 构建 Clash/Mihomo 配置文件。

生成结果写入 proxies/clash_profile.yaml，包含：
- 固定的基本端口设置（7890/7891 与 Mihomo 默认一致，可按需修改）；
- 将原始节点全部放入一个 select 组，后续脚本会通过 REST API 逐个切换；
- 最终转发走 FINAL 代理组。
"""

from __future__ import annotations

import os
import sys
import yaml
from typing import Any, Dict, List, Tuple


def get_workspace_paths() -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    proxies_dir = os.path.join(base_dir, "proxies")
    return {
        "base": base_dir,
        "proxies": proxies_dir,
        "raw_yaml": os.path.join(proxies_dir, "raw_nodes.yaml"),
        "output": os.path.join(proxies_dir, "clash_profile.yaml"),
    }


def load_raw_nodes(raw_yaml: str) -> List[Dict[str, Any]]:
    if not os.path.exists(raw_yaml):
        raise FileNotFoundError(
            "未找到 raw_nodes.yaml，请先运行 fetch_proxies.py 生成订阅数据。"
        )
    with open(raw_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    proxies = data.get("proxies")
    if not proxies:
        raise ValueError("raw_nodes.yaml 中没有 proxies 数据，确认订阅是否解析成功。")
    return proxies


def ensure_unique_proxy_names(
    proxies: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    seen: Dict[str, int] = {}
    result: List[Dict[str, Any]] = []
    names: List[str] = []

    for idx, proxy in enumerate(proxies):
        base_name = str(proxy.get("name") or f"node-{idx}")
        count = seen.get(base_name, 0) + 1
        seen[base_name] = count

        unique_name = base_name if count == 1 else f"{base_name} #{count}"

        if unique_name != proxy.get("name"):
            proxy = dict(proxy)
            proxy["name"] = unique_name

        result.append(proxy)
        names.append(unique_name)

    return result, names


def build_profile(proxies: List[Dict[str, Any]]) -> Dict[str, Any]:
    unique_proxies, names = ensure_unique_proxy_names(proxies)

    profile = {
        "mixed-port": 7890,
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "bind-address": "*",
        "mode": "rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        # secret 可视需要填写；若不想使用可以删除此字段，但后续脚本要同步更新。
        "secret": "",
        "dns": {
            "enable": True,
            "ipv6": False,
            "default-nameserver": [
                "223.5.5.5",
                "119.29.29.29",
                "180.76.76.76",
                "1.1.1.1",
            ],
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "use-hosts": True,
            "nameserver": [
                "223.5.5.5",
                "119.29.29.29",
            ],
        },
    "proxies": unique_proxies,
        "proxy-groups": [
            {
                "name": "NODE_TEST",
                "type": "select",
                "proxies": names,
            },
            {
                "name": "FINAL",
                "type": "select",
                "proxies": ["NODE_TEST", "DIRECT"],
            },
        ],
        "rules": [
            "MATCH,FINAL",
        ],
    }
    return profile


def main() -> None:
    paths = get_workspace_paths()

    try:
        proxies = load_raw_nodes(paths["raw_yaml"])
    except Exception as exc:
        print(f"❌ 读取原始节点失败: {exc}")
        sys.exit(1)

    profile = build_profile(proxies)

    os.makedirs(paths["proxies"], exist_ok=True)
    with open(paths["output"], "w", encoding="utf-8") as f:
        yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)

    print("✅ 已生成 Clash/Mihomo 配置文件:")
    print(f"   {paths['output']}")
    print("👉 请在 Mihomo 中导入该文件作为单独配置，并确认 external-controller/secret 设置与此一致。")


if __name__ == "__main__":
    main()
