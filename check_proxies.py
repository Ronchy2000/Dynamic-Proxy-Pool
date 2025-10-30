"""使用 Mihomo /proxies/{name}/delay 并发检测节点可用性并产出可用列表（加速版）。"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, List

import aiohttp
import yaml
import requests
from tqdm import tqdm


@dataclass
class MihomoConfig:
    controller: str = "http://127.0.0.1:9090"
    secret: str = ""
    proxy_group: str = "NODE_TEST"         # 仅用于读取节点名；不再做切换
    test_url: str = "https://www.google.com"
    timeout: float = 8.0                   # 单节点测试超时（秒）
    max_concurrency: int = 20              # 并发数量（可适当调大）
    verify_tls: bool = True                # aiohttp SSL 验证


def get_proxies_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies")


def load_profile(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _auth_header(cfg: MihomoConfig) -> dict:
    return {"Authorization": f"Bearer {cfg.secret}"} if cfg.secret else {}


def list_group_proxies(cfg: MihomoConfig) -> Iterable[str]:
    """
    从 proxy-group 获取节点列表（只取名字，不切组）。
    Clash/Mihomo: GET /proxies/{group} -> {"all": [...], "now": "..."}
    """
    url = f"{cfg.controller}/proxies/{cfg.proxy_group}"
    resp = requests.get(url, headers=_auth_header(cfg), timeout=cfg.timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("all", []) or []


async def test_one_proxy(session: aiohttp.ClientSession, cfg: MihomoConfig, name: str) -> Tuple[str, Optional[float], Optional[str]]:
    """
    并发测试单个节点：
      GET /proxies/{name}/delay?url=...&timeout=...（timeout 单位 ms）
    返回: (name, latency_ms or None, error or None)
    """
    # Mihomo 的 delay 接口 timeout 为毫秒
    params = {
        "url": cfg.test_url,
        "timeout": str(int(cfg.timeout * 1000)),
    }
    url = f"{cfg.controller}/proxies/{name}/delay"
    try:
        async with session.get(url, params=params, timeout=cfg.timeout) as resp:
            if resp.status != 200:
                return name, None, f"HTTP {resp.status}"
            data = await resp.json()
            # 正常返回示例：{"delay": 123}
            delay = data.get("delay")
            if isinstance(delay, (int, float)):
                return name, float(delay), None
            return name, None, f"bad payload: {data}"
    except Exception as e:
        return name, None, repr(e)


async def run_tests_async(cfg: MihomoConfig, names: Iterable[str]) -> Tuple[List[Tuple[str, float]], List[Tuple[str, str]]]:
    """
    并发跑所有节点测试，返回 (ok_list, failed_list)
    ok_list: [(name, latency_ms), ...]
    failed_list: [(name, error), ...]
    """
    headers = _auth_header(cfg)
    timeout = aiohttp.ClientTimeout(total=cfg.timeout + 1.0)
    connector = aiohttp.TCPConnector(ssl=cfg.verify_tls, limit=0)  # limit=0 由我们自己用 semaphore 控制并发

    ok, failed = [], []
    sem = asyncio.Semaphore(cfg.max_concurrency)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
        tasks = []

        async def worker(nm: str):
            async with sem:
                return await test_one_proxy(session, cfg, nm)

        for nm in names:
            tasks.append(asyncio.create_task(worker(nm)))

        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Proxy Test (async)"):
            name, latency, err = await f
            if latency is not None:
                ok.append((name, latency))
            else:
                failed.append((name, err or "unknown error"))

    return ok, failed


def save_results(dir_path: str, ok: list, failed: list) -> None:
    """
    写入 JSON 结果，文件头含 meta（生成说明与统计）。
    """
    output = os.path.join(dir_path, "proxy_test_results.json")
    payload = {
        "meta": {
            "generated_by": "check_proxies.py",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": {"ok": len(ok), "failed": len(failed)},
            "note": "此文件由 check_proxies.py 生成（async加速版），包含可用/不可用代理及延迟(ms)。",
        },
        "ok": [{"name": n, "latency_ms": round(lat, 2)} for n, lat in ok],
        "failed": [{"name": n, "error": err} for n, err in failed],
    }
    with open(output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"💾 结果已写入: {output}")
    print(f"   -> 可用代理: {len(ok)} ，失败代理: {len(failed)}")


def main():
    proxies_dir = get_proxies_dir()
    profile_path = os.path.join(proxies_dir, "clash_profile.yaml")

    if not os.path.exists(profile_path):
        print("❌ 未找到 clash_profile.yaml，请先生成后再测试。")
        return

    profile = load_profile(profile_path)
    secret = profile.get("secret", "") or ""

    cfg = MihomoConfig(secret=secret)

    try:
        names = list(list_group_proxies(cfg))
    except requests.RequestException as exc:
        print("❌ 无法从 Mihomo 获取节点列表，请确认客户端已启动且 external-controller/secret 正确。")
        print(f"   详细信息: {exc}")
        return

    if not names:
        print("❌ 未获取到节点，请确认分组名称是否为 NODE_TEST。")
        return

    print(f"🚀 准备并发测试 {len(names)} 个节点：{cfg.controller} -> /proxies/{{name}}/delay ，目标 {cfg.test_url}")
    print(f"   并发数: {cfg.max_concurrency} ，超时: {cfg.timeout}s ，TLS校验: {cfg.verify_tls}")

    ok, failed = asyncio.run(run_tests_async(cfg, names))

    # 打印摘要
    print("\n测试完成：")
    for name, latency in ok:
        print(f"   ✅ {name} -> {latency:.0f} ms")
    for name, error in failed:
        print(f"   ❌ {name} -> {error}")

    print(f"\n统计：可用 {len(ok)} ，失败 {len(failed)} ，总计 {len(names)}")

    save_results(proxies_dir, ok, failed)


if __name__ == "__main__":
    main()
