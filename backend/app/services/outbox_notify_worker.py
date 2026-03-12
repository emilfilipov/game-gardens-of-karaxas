from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
import re
from threading import Event, Thread
import time
from typing import Any, Protocol

from sqlalchemy.engine import make_url

DEFAULT_OUTBOX_NOTIFY_CHANNEL = "world_outbox_new"


class NotifyConnection(Protocol):
    def listen(self, channel: str) -> None: ...

    def poll(self, timeout_seconds: float) -> list[str]: ...

    def close(self) -> None: ...


class NotifyConnector(Protocol):
    def open(self) -> NotifyConnection: ...


@dataclass(frozen=True)
class OutboxWakeSignal:
    reason: str
    channel: str
    payload: str | None
    outbox_id: int | None
    topic: str | None
    received_at: datetime


@dataclass
class OutboxNotifyWorkerStats:
    connection_attempts: int = 0
    connection_successes: int = 0
    connection_failures: int = 0
    notifications_received: int = 0
    wake_dispatches: int = 0
    wake_handler_failures: int = 0


WakeHandler = Callable[[OutboxWakeSignal], None]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def parse_outbox_notify_payload(payload: str | None) -> tuple[int | None, str | None]:
    raw = (payload or "").strip()
    if not raw:
        return (None, None)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        if raw.isdigit():
            return (int(raw), None)
        return (None, None)

    if isinstance(parsed, dict):
        outbox_id_raw = parsed.get("outbox_id")
        topic_raw = parsed.get("topic")
        outbox_id: int | None = None
        if isinstance(outbox_id_raw, int):
            outbox_id = outbox_id_raw
        elif isinstance(outbox_id_raw, str) and outbox_id_raw.strip().isdigit():
            outbox_id = int(outbox_id_raw.strip())

        topic = str(topic_raw).strip() if topic_raw is not None else None
        if topic == "":
            topic = None
        return (outbox_id, topic)

    if isinstance(parsed, int):
        return (parsed, None)

    return (None, None)


class OutboxNotifyWorker:
    def __init__(
        self,
        *,
        connector: NotifyConnector,
        wake_handler: WakeHandler,
        channel: str = DEFAULT_OUTBOX_NOTIFY_CHANNEL,
        listen_timeout_seconds: float = 5.0,
        reconnect_delay_seconds: float = 2.0,
        logger: logging.Logger | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        normalized_channel = (channel or "").strip() or DEFAULT_OUTBOX_NOTIFY_CHANNEL
        self._connector = connector
        self._wake_handler = wake_handler
        self._channel = normalized_channel
        self._listen_timeout_seconds = max(0.0, float(listen_timeout_seconds))
        self._reconnect_delay_seconds = max(0.0, float(reconnect_delay_seconds))
        self._logger = logger or logging.getLogger("children-of-ikphelion.outbox_notify")
        self._sleep_fn = sleep_fn or time.sleep
        self.stats = OutboxNotifyWorkerStats()

    def run(self, stop_event: Event) -> None:
        while not stop_event.is_set():
            connection: NotifyConnection | None = None
            try:
                self.stats.connection_attempts += 1
                connection = self._connector.open()
                self.stats.connection_successes += 1
                connection.listen(self._channel)
                self._dispatch_wake(reason="startup", payload=None)

                while not stop_event.is_set():
                    payloads = connection.poll(self._listen_timeout_seconds)
                    if not payloads:
                        self._dispatch_wake(reason="heartbeat", payload=None)
                        continue

                    self.stats.notifications_received += len(payloads)
                    for payload in payloads:
                        self._dispatch_wake(reason="notify", payload=payload)
            except Exception:
                self.stats.connection_failures += 1
                if stop_event.is_set():
                    break
                self._logger.warning(
                    "Outbox LISTEN worker connection dropped; reconnecting in %.2fs",
                    self._reconnect_delay_seconds,
                    exc_info=True,
                )
                if self._reconnect_delay_seconds > 0:
                    self._sleep_fn(self._reconnect_delay_seconds)
            finally:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception:
                        self._logger.debug("Failed closing LISTEN connection", exc_info=True)

    def _dispatch_wake(self, *, reason: str, payload: str | None) -> None:
        outbox_id, topic = parse_outbox_notify_payload(payload)
        signal = OutboxWakeSignal(
            reason=reason,
            channel=self._channel,
            payload=payload,
            outbox_id=outbox_id,
            topic=topic,
            received_at=_now_utc(),
        )
        try:
            self._wake_handler(signal)
            self.stats.wake_dispatches += 1
        except Exception:
            self.stats.wake_handler_failures += 1
            self._logger.exception("Outbox wake handler failed")


@dataclass
class OutboxNotifyWorkerHandle:
    worker: OutboxNotifyWorker
    thread: Thread
    stop_event: Event


def start_outbox_notify_worker(
    *,
    connector: NotifyConnector,
    wake_handler: WakeHandler,
    channel: str = DEFAULT_OUTBOX_NOTIFY_CHANNEL,
    listen_timeout_seconds: float = 5.0,
    reconnect_delay_seconds: float = 2.0,
    logger: logging.Logger | None = None,
) -> OutboxNotifyWorkerHandle:
    stop_event = Event()
    worker = OutboxNotifyWorker(
        connector=connector,
        wake_handler=wake_handler,
        channel=channel,
        listen_timeout_seconds=listen_timeout_seconds,
        reconnect_delay_seconds=reconnect_delay_seconds,
        logger=logger,
    )
    thread = Thread(target=worker.run, args=(stop_event,), name="aop-outbox-listen-worker", daemon=True)
    thread.start()
    return OutboxNotifyWorkerHandle(worker=worker, thread=thread, stop_event=stop_event)


def stop_outbox_notify_worker(handle: OutboxNotifyWorkerHandle | None, *, join_timeout_seconds: float = 3.0) -> None:
    if handle is None:
        return
    handle.stop_event.set()
    handle.thread.join(timeout=max(0.0, float(join_timeout_seconds)))


class PsycopgNotifyConnection:
    _CHANNEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def listen(self, channel: str) -> None:
        normalized = (channel or "").strip()
        if not normalized or not self._CHANNEL_PATTERN.fullmatch(normalized):
            raise ValueError("invalid PostgreSQL LISTEN channel")
        self._connection.execute(f'LISTEN "{normalized}"')

    def poll(self, timeout_seconds: float) -> list[str]:
        timeout = max(0.0, float(timeout_seconds))
        notifies_fn = getattr(self._connection, "notifies", None)
        if not callable(notifies_fn):
            if timeout > 0:
                time.sleep(timeout)
            return []

        try:
            iterator = notifies_fn(timeout=timeout, stop_after=64)
        except TypeError:
            try:
                iterator = notifies_fn(timeout=timeout)
            except TypeError:
                iterator = notifies_fn()

        payloads: list[str] = []
        start = time.monotonic()
        for notification in iterator:
            payload = getattr(notification, "payload", "")
            payloads.append(str(payload))
            if len(payloads) >= 64:
                break
            if timeout > 0 and (time.monotonic() - start) >= timeout:
                break
        return payloads

    def close(self) -> None:
        close_fn = getattr(self._connection, "close", None)
        if callable(close_fn):
            close_fn()


class PsycopgNotifyConnector:
    def __init__(self, dsn: str, *, connect_fn: Callable[..., Any] | None = None) -> None:
        normalized = (dsn or "").strip()
        if not normalized:
            raise ValueError("dsn must not be empty")
        self._dsn = normalized
        self._connect_fn = connect_fn or _default_psycopg_connect

    def open(self) -> NotifyConnection:
        connection = self._connect_fn(self._dsn, autocommit=True)
        return PsycopgNotifyConnection(connection)


def _default_psycopg_connect(dsn: str, *, autocommit: bool) -> Any:
    try:
        import psycopg
    except Exception as exc:
        raise RuntimeError("psycopg is required for PostgreSQL LISTEN/NOTIFY worker") from exc
    return psycopg.connect(dsn, autocommit=autocommit)


def psycopg_dsn_from_sqlalchemy_url(database_url: str) -> str:
    url = make_url((database_url or "").strip())
    drivername = url.drivername.split("+", 1)[0]
    normalized = url.set(drivername=drivername)
    return normalized.render_as_string(hide_password=False)


def build_noop_wake_handler(*, logger: logging.Logger | None = None) -> WakeHandler:
    log = logger or logging.getLogger("children-of-ikphelion.outbox_notify")

    def _handle(signal: OutboxWakeSignal) -> None:
        if signal.reason == "notify":
            log.info(
                "Outbox wake signal received channel=%s outbox_id=%s topic=%s",
                signal.channel,
                signal.outbox_id,
                signal.topic,
            )

    return _handle
