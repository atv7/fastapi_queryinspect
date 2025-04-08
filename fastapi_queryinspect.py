import logging
import time
import re
from contextvars import ContextVar
from typing import Optional, Dict, Any, List, Union
from collections import Counter

from fastapi import FastAPI, Request, Response
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen

log = logging.getLogger(__name__)

query_inspect_ctx: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "query_inspect_ctx", default=None
)


class QueryInspect:
    def __init__(self, app: Optional[FastAPI] = None):
        self.app = app
        self._config: Dict[str, bool | Union[int, float]] = {
            "QUERYINSPECT_ENABLED": True,
            "QUERYINSPECT_HEADERS": True,
            "QUERYINSPECT_HEADERS_COMBINED": True,
            "QUERYINSPECT_LOG": True,
            "QUERYINSPECT_SLOW_THRESHOLD": 0.5,
            "QUERYINSPECT_DUPLICATE_LIMIT": 5,
        }
        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI):
        @app.middleware("http")
        async def query_inspect_middleware(request: Request, call_next):
            if not self._config.get("QUERYINSPECT_ENABLED"):
                return await call_next(request)

            qi_data = {
                "r_start": time.time(),
                "q_start": 0,
                "r_time": 0,
                "q_time": 0,
                "reads": 0,
                "writes": 0,
                "conns": 0,
                "queries": [],
            }
            token = query_inspect_ctx.set(qi_data)

            try:
                response = await call_next(request)
                return self.process_response(qi_data, response, app)
            finally:
                query_inspect_ctx.reset(token)

        listen(Engine, "connect", self.connect)
        listen(Engine, "before_cursor_execute", self.before_cursor_execute)
        listen(Engine, "after_cursor_execute", self.after_cursor_execute)

    def configure(self, **settings: Union[bool, int, float]):
        self._config.update(settings)

    def connect(self, dbapi_connection, connection_record):
        qi_data = query_inspect_ctx.get()
        if qi_data is None:
            return
        qi_data["conns"] += 1

    def before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        qi_data = query_inspect_ctx.get()
        if qi_data is None:
            return
        qi_data["q_start"] = time.time()

        qi_data["current_query"] = {
            "sql": statement,
            "start": time.time(),
            "parameters": parameters,
        }

    def after_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        qi_data = query_inspect_ctx.get()
        if qi_data is None or "current_query" not in qi_data:
            return

        query = qi_data["current_query"]
        duration = time.time() - query["start"]

        query["time"] = duration
        query["type"] = (
            "SELECT" if statement.lower().startswith("select") else "OTHER"
        )
        qi_data["queries"].append(query)

        qi_data["q_time"] += duration
        if query["type"] == "SELECT":
            qi_data["reads"] += 1
        else:
            qi_data["writes"] += 1

        del qi_data["current_query"]

    def analyze_sql_queries(
        self, queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        sql_count = len(queries)
        sql_time = sum(q["time"] for q in queries)
        sql_tables = Counter()
        sql_tb_info = {}

        query_fingerprints = Counter(
            re.sub(r"\s+", " ", q["sql"].strip()) for q in queries
        )
        duplicate_count = sum(c for c in query_fingerprints.values() if c > 1)

        for query in queries:
            if query["time"] >= self._config["QUERYINSPECT_SLOW_THRESHOLD"]:
                log.warning(
                    "SLOW QUERY (%.3f sec): %s", query["time"], query["sql"]
                )

            if query["type"] == "SELECT":
                if match := re.search(
                    r"FROM\s+([\w`]+)", query["sql"], re.IGNORECASE
                ):
                    table_name = re.sub(r"\W", "", match.group(1))
                    sql_tables[table_name] += 1
                    sql_tb_info.setdefault(table_name, query["sql"])

        return {
            "count": sql_count,
            "duplicates": duplicate_count,
            "time_ms": round(sql_time * 1000, 1),
            "tables": dict(sql_tables.most_common()),
            "tables_info": sql_tb_info,
        }

    def process_response(
        self, qi_data: Dict[str, Any], response: Response, app: FastAPI
    ):
        qi_data["r_time"] = time.time() - qi_data["r_start"]
        qi_data["q_time_ms"] = round(qi_data["q_time"] * 1000, 1)
        qi_data["r_time_ms"] = round(qi_data["r_time"] * 1000, 1)

        if self._config.get("QUERYINSPECT_LOG"):
            stats = self.analyze_sql_queries(qi_data["queries"])

            log.info(
                "[SQL] %d queries (%d duplicates), %d ms SQL time, %d ms total request time",
                stats["count"],
                stats["duplicates"],
                stats["time_ms"],
                qi_data["r_time_ms"],
            )

            duplicate_limit = self._config["QUERYINSPECT_DUPLICATE_LIMIT"]
            for table, count in stats["tables"].items():
                if count >= duplicate_limit:
                    log.warning(
                        "MULTIPLE ACCESS (%d times): %s\nExample query: %s",
                        count,
                        table,
                        stats["tables_info"][table],
                    )

        if self._config.get("QUERYINSPECT_HEADERS"):
            response.headers["x-queryinspect-combined"] = (
                f"reads={qi_data['reads']},"
                f"writes={qi_data['writes']},"
                f"conns={qi_data['conns']},"
                f"rtime={qi_data['r_time_ms']}ms"
            )

        return response
