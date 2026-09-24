#!/usr/bin/env python3
"""MCP-сервер P&L Check — локальная проверка структуры и данных P&L.

Чистый Python (stdlib), JSON-RPC 2.0 по stdio (протокол Model Context Protocol).
Запуск: python mcp_server.py   (подключение через MCP-клиент, см. README.md)

Инструменты:
  validate_pnl_structure  — проверка обязательных строк и единиц измерения
  check_evidence_levels   — каждый вывод обязан иметь уровень доказательности
  detect_gaps             — чего не хватает для безопасного решения
"""
import csv
import io
import json
import sys

# --- Обязательные строки управленческого P&L (стартовый набор) ---
REQUIRED_PNL_LINES = [
    "выручка", "себестоимость", "валовая прибыль", "коммерческие расходы",
    "управленческие расходы", "операционная прибыль", "прочие доходы",
    "прочие расходы", "финансовый результат", "налог", "чистая прибыль",
]

EVIDENCE_LEVELS = {"факт", "расчёт", "гипотеза", "догадка", "нет данных"}


def parse_csv_text(text: str) -> list[dict]:
    """Парсит CSV в список словарей (первая строка — заголовки)."""
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def validate_pnl_structure(csv_text: str) -> dict:
    """Проверяет структуру P&L: обязательные строки и единицы измерения."""
    try:
        rows = parse_csv_text(csv_text)
    except Exception as exc:
        return {"ok": False, "error": f"CSV не читается: {exc}"}

    if not rows:
        return {"ok": False, "error": "Пустой CSV"}

    headers = list(rows[0].keys())
    name_col = headers[0] if headers else "название"
    value_cols = [h for h in headers[1:] if h]

    present = {str(r.get(name_col, "")).strip().lower() for r in rows}
    missing = [line for line in REQUIRED_PNL_LINES if line not in present]

    # Единицы измерения: хотя бы одна колонка со значением должна быть числовой
    numeric_cols = []
    for col in value_cols:
        sample = [r.get(col, "") for r in rows if r.get(col, "").strip()]
        if sample and all(_is_number(v) for v in sample[:5]):
            numeric_cols.append(col)

    return {
        "ok": not missing and bool(numeric_cols),
        "missing_lines": missing,
        "numeric_columns": numeric_cols,
        "total_rows": len(rows),
        "note": "Проверена только структура. Значения — заявление компании, не подтверждение.",
    }


def check_evidence_levels(rows: list[dict]) -> dict:
    """Проверяет, что каждый вывод имеет уровень доказательности."""
    bad = []
    level_col = None
    for row in rows:
        for col, val in row.items():
            if "уровень" in col.lower() or "evidence" in col.lower():
                level_col = col
                break
        if level_col:
            break

    if level_col is None:
        return {"ok": False, "error": "Нет колонки с уровнем доказательности (уровень/evidence)"}

    for i, row in enumerate(rows, start=2):
        val = str(row.get(level_col, "")).strip().lower()
        if val and val not in EVIDENCE_LEVELS:
            bad.append(f"строка {i}: неизвестный уровень '{val}'")
        if not val:
            bad.append(f"строка {i}: уровень не указан")

    return {
        "ok": not bad,
        "issues": bad[:20],
        "count": len(rows),
        "allowed_levels": sorted(EVIDENCE_LEVELS),
    }


def detect_gaps(questionnaire_text: str, pnl_rows: list[dict]) -> dict:
    """Находит пробелы в данных: чего не хватает для безопасного решения."""
    gaps = []
    q = questionnaire_text.lower()
    missing_checks = []
    for marker, label in [
        ("юрлицо", "Юридическое лицо"),
        ("период", "Период"),
        ("источник", "Источники данных"),
        ("единиц", "Единицы измерения"),
    ]:
        if marker not in q:
            missing_checks.append(label)

    if missing_checks:
        gaps.append("Опросник: " + ", ".join(missing_checks))

    if not pnl_rows:
        gaps.append("Нет данных P&L")
    else:
        # Проверяем, есть ли колонки с фактическими значениями
        sample = pnl_rows[0]
        value_cols = [k for k in sample.keys() if k and k != list(sample.keys())[0]]
        if not value_cols:
            gaps.append("P&L: нет колонок со значениями")

    return {"ok": not gaps, "gaps": gaps}


def _is_number(value: str) -> bool:
    v = value.strip().replace(" ", "").replace(",", ".").replace("₽", "").replace("руб", "")
    if not v:
        return False
    try:
        float(v)
        return True
    except ValueError:
        return False


# --- JSON-RPC 2.0 (MCP over stdio) ---

def _read_request() -> dict | None:
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _respond(req: dict, result: dict | None = None, error: dict | None = None) -> None:
    resp = {"jsonrpc": "2.0", "id": req.get("id")}
    if error is not None:
        resp["error"] = error
    else:
        resp["result"] = result
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "validate_pnl_structure",
        "description": "Проверяет структуру P&L: обязательные строки и числовые колонки.",
        "inputSchema": {
            "type": "object",
            "properties": {"csv_text": {"type": "string", "description": "CSV-текст структуры P&L"}},
            "required": ["csv_text"],
        },
    },
    {
        "name": "check_evidence_levels",
        "description": "Проверяет, что каждый вывод имеет уровень доказательности.",
        "inputSchema": {
            "type": "object",
            "properties": {"rows": {"type": "array", "items": {"type": "object"}}},
            "required": ["rows"],
        },
    },
    {
        "name": "detect_gaps",
        "description": "Находит пробелы в данных для безопасного решения.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "questionnaire_text": {"type": "string"},
                "pnl_rows": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["questionnaire_text", "pnl_rows"],
        },
    },
]


def main() -> None:
    while True:
        req = _read_request()
        if req is None:
            break
        method = req.get("method", "")

        if method == "initialize":
            _respond(req, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "pnl-check", "version": "0.3.0"},
            })
        elif method == "tools/list":
            _respond(req, {"tools": TOOLS})
        elif method == "tools/call":
            name = req.get("params", {}).get("name", "")
            args = req.get("params", {}).get("arguments", {})
            try:
                if name == "validate_pnl_structure":
                    result = validate_pnl_structure(args.get("csv_text", ""))
                elif name == "check_evidence_levels":
                    result = check_evidence_levels(args.get("rows", []))
                elif name == "detect_gaps":
                    result = detect_gaps(args.get("questionnaire_text", ""), args.get("pnl_rows", []))
                else:
                    _respond(req, error={"code": -32601, "message": f"Неизвестный инструмент: {name}"})
                    continue
                _respond(req, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]})
            except Exception as exc:
                _respond(req, error={"code": -32603, "message": str(exc)})
        elif method == "ping":
            _respond(req, {})
        else:
            _respond(req, error={"code": -32601, "message": f"Метод не поддерживается: {method}"})


if __name__ == "__main__":
    main()
