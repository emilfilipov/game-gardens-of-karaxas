#!/usr/bin/env python3
"""Concurrent probe utility for publish-drain behavior.

Usage:
  python backend/scripts/publish_drain_stress_probe.py \
    --base-url https://karaxas-backend.example \
    --tokens-file tokens.txt \
    --requests 500 \
    --concurrency 50

tokens.txt format: one bearer access token per line.
Run this before/after a publish activation to compare status-code distribution and latency.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import statistics
import time

import httpx


@dataclass
class ProbeResult:
    status_code: int
    latency_ms: float


async def _worker(
    client: httpx.AsyncClient,
    base_url: str,
    queue: asyncio.Queue[str],
    results: list[ProbeResult],
) -> None:
    while True:
        token = await queue.get()
        if token == "__STOP__":
            queue.task_done()
            return
        started = time.perf_counter()
        status = 0
        try:
            response = await client.get(
                f"{base_url.rstrip('/')}/auth/me",
                headers={"Authorization": f"Bearer {token}", "X-Client-Version": "1.0.0"},
            )
            status = response.status_code
        except Exception:
            status = 599
        latency = (time.perf_counter() - started) * 1000.0
        results.append(ProbeResult(status_code=status, latency_ms=latency))
        queue.task_done()


async def run_probe(base_url: str, tokens: list[str], total_requests: int, concurrency: int) -> list[ProbeResult]:
    queue: asyncio.Queue[str] = asyncio.Queue()
    for index in range(total_requests):
        queue.put_nowait(tokens[index % len(tokens)])
    for _ in range(concurrency):
        queue.put_nowait("__STOP__")

    results: list[ProbeResult] = []
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        workers = [
            asyncio.create_task(_worker(client, base_url, queue, results))
            for _ in range(concurrency)
        ]
        await queue.join()
        for task in workers:
            await task
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish-drain stress probe")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--tokens-file", required=True)
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=50)
    args = parser.parse_args()

    with open(args.tokens_file, "r", encoding="utf-8") as handle:
        tokens = [line.strip() for line in handle.readlines() if line.strip()]
    if not tokens:
        raise SystemExit("No tokens loaded from tokens file.")

    results = asyncio.run(
        run_probe(
            base_url=args.base_url,
            tokens=tokens,
            total_requests=max(1, args.requests),
            concurrency=max(1, args.concurrency),
        )
    )

    by_status: dict[int, int] = {}
    for row in results:
        by_status[row.status_code] = by_status.get(row.status_code, 0) + 1
    latencies = [row.latency_ms for row in results]
    print("Requests:", len(results))
    print("Status distribution:", dict(sorted(by_status.items(), key=lambda kv: kv[0])))
    print("Latency avg ms:", round(statistics.mean(latencies), 3))
    print("Latency p95 ms:", round(sorted(latencies)[int(max(0, len(latencies) - 1) * 0.95)], 3))


if __name__ == "__main__":
    main()

