from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from focus_reminder.app import constants
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.infrastructure.storage.config_repository import ConfigRepository
from focus_reminder.infrastructure.storage.event_repository import ReminderEventRepository
from focus_reminder.infrastructure.storage.sqlite_manager import SQLiteManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ApiContext:
    config_repo: ConfigRepository
    event_repo: ReminderEventRepository

    @classmethod
    def from_defaults(cls) -> "ApiContext":
        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config_repo = ConfigRepository(constants.CONFIG_PATH)
        sqlite = SQLiteManager(constants.DB_PATH)
        sqlite.initialize()
        event_repo = ReminderEventRepository(sqlite)
        return cls(config_repo=config_repo, event_repo=event_repo)


class FocusApiHandler(BaseHTTPRequestHandler):
    context: ApiContext | None = None

    server_version = "FocusReminderApi/1.0"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            route = parsed.path
            qs = parse_qs(parsed.query)

            if route == "/api/health":
                self._send_json(200, {"ok": True, "service": "focus-reminder-api"})
                return

            if route == "/api/config":
                cfg = self._require_context().config_repo.load().to_dict()
                self._send_json(200, {"config": cfg})
                return

            if route == "/api/dashboard":
                days = self._int_query(qs, "days", 7, min_value=1, max_value=30)
                event_limit = self._int_query(qs, "event_limit", 100, min_value=1, max_value=500)
                payload = self._build_dashboard_payload(days=days, event_limit=event_limit)
                self._send_json(200, payload)
                return

            if route == "/api/events":
                limit = self._int_query(qs, "limit", 100, min_value=1, max_value=500)
                rows = self._require_context().event_repo.get_recent_events(limit=limit)
                self._send_json(200, {"events": rows})
                return

            self._send_json(404, {"error": "not_found"})
        except Exception as exc:  # pragma: no cover - runtime protection
            logger.exception("GET handler failed")
            self._send_json(500, {"error": "server_error", "detail": str(exc)})

    def do_PUT(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            route = parsed.path
            if route != "/api/config":
                self._send_json(404, {"error": "not_found"})
                return

            body = self._read_json_body()
            if not isinstance(body, dict):
                self._send_json(400, {"error": "invalid_json"})
                return

            incoming = body.get("config", body)
            if not isinstance(incoming, dict):
                self._send_json(400, {"error": "invalid_payload"})
                return

            cfg = FocusConfig.from_dict(incoming).sanitized()
            self._require_context().config_repo.save(cfg)
            self._send_json(200, {"config": cfg.to_dict()})
        except Exception as exc:  # pragma: no cover - runtime protection
            logger.exception("PUT handler failed")
            self._send_json(500, {"error": "server_error", "detail": str(exc)})

    def do_DELETE(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            route = parsed.path
            if route == "/api/events":
                self._require_context().event_repo.clear_all_events()
                self._send_json(200, {"ok": True})
                return

            self._send_json(404, {"error": "not_found"})
        except Exception as exc:  # pragma: no cover - runtime protection
            logger.exception("DELETE handler failed")
            self._send_json(500, {"error": "server_error", "detail": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logger.info("%s - %s", self.address_string(), format % args)

    def _build_dashboard_payload(self, days: int, event_limit: int) -> dict[str, Any]:
        ctx = self._require_context()
        now = datetime.now()

        trend = [
            {"date": label, "count": count}
            for label, count in ctx.event_repo.get_last_n_days_counts(days, now)
        ]
        hourly = [
            {"hour": hour, "count": count}
            for hour, count in ctx.event_repo.get_hourly_distribution(now)
        ]
        level_distribution = [
            {"key": key, "count": count}
            for key, count in ctx.event_repo.get_level_distribution(days, now)
        ]
        trigger_reason_distribution = [
            {"key": key, "count": count}
            for key, count in ctx.event_repo.get_trigger_reason_distribution(days, now)
        ]
        dismiss_reason_distribution = [
            {"key": key, "count": count}
            for key, count in ctx.event_repo.get_dismiss_reason_distribution(days, now)
        ]
        events = ctx.event_repo.get_recent_events(limit=event_limit)

        return {
            "today_count": ctx.event_repo.get_today_count(now),
            "period_days": days,
            "period_count": sum(item["count"] for item in trend),
            "trend": trend,
            "hourly": hourly,
            "level_distribution": level_distribution,
            "trigger_reason_distribution": trigger_reason_distribution,
            "dismiss_reason_distribution": dismiss_reason_distribution,
            "events": events,
        }

    def _int_query(
        self,
        query: dict[str, list[str]],
        name: str,
        default: int,
        min_value: int,
        max_value: int,
    ) -> int:
        raw = query.get(name, [str(default)])[0]
        try:
            value = int(raw)
        except ValueError:
            value = default
        return max(min_value, min(max_value, value))

    def _require_context(self) -> ApiContext:
        if self.context is None:
            raise RuntimeError("API context not initialized")
        return self.context

    def _read_json_body(self) -> Any:
        length_raw = self.headers.get("Content-Length", "0")
        try:
            length = int(length_raw)
        except ValueError:
            length = 0
        body = self.rfile.read(max(0, length))
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

    def _send_json(self, code: int, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_api_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    FocusApiHandler.context = ApiContext.from_defaults()
    server = ThreadingHTTPServer((host, int(port)), FocusApiHandler)
    logger.info("Focus API server running on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Focus API server stopped by user")
    finally:
        server.server_close()

