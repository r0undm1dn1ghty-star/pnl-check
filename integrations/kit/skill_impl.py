# -*- coding: utf-8 -*-
"""Реализация P&L Check для skillkit. Вход: {"lines": {...}, "cash": {...}, "standard": "IFRS"}."""
import re
SKILL_NAME = "pnl-check"
SKILL_VERSION = "0.4.0"
SKILL_DESCRIPTION = ("Разбор P&L публичной компании: сверка «прибыль vs деньги», уровни "
                     "доказательности, ловушки отчётности, бриф с уверенностью.")
INPUT_SCHEMA = {"type": "object", "properties": {"input": {"type": "object"}}}
OUTPUT_SCHEMA = {"type": "object", "properties": {
    "confidence": {"type": "string"}, "flags": {"type": "array"},
    "adversarial": {"type": "array"}, "brief": {"type": "object"}}}
SYSTEM_PROMPT = """Ты — аналитик P&L публичных компаний. ПРАВИЛА:
(1) каждый вывод помечай уровнем: факт / расчёт / гипотеза;
(2) ОБЯЗАТЕЛЬНО сверяй прибыль и денежный поток — расхождение объясняй явно;
(3) ловушки: FCF с субсидиями ≠ чистый операционный FCF; прибыль с разовыми статьями ≠ операционная;
стандарт отчётности обязателен (не сравнивать РСБУ и МСФО); рост финансовых расходов = флаг долга;
(4) в брифе обязательны «Уверенность» (high/medium/low) и «Adversarial self-check».
Никаких цифр без источника."""

TRAPS = [
    ("субсид", "FCF с субсидиями ≠ чистый операционный FCF — пересчитать без нерыночных поступлений"),
    ("разов", "прибыль с разовыми статьями ≠ операционная — требовать разбивку (LTI, обесценение)"),
    ("lti", "LTI-программа и обесценение — разовые статьи, не операционное ухудшение"),
    ("обесцен", "обесценение разовое — проверить примечания"),
    ("гудвил", "списание гудвила — разовое, не операционный результат"),
]


def run(input_value=None, **kw):
    d = input_value if isinstance(input_value, dict) else {"text": str(input_value or "")}
    lines = d.get("lines") or {}
    cash = d.get("cash") or {}
    text = (d.get("text") or "") + " " + " ".join(f"{k} {v}" for k, v in {**lines, **cash}.items())
    low = text.lower()
    # ВАЖНО: t[0] — ключевое слово (строка); итерация по строке дала бы буквы ('с' in low).
    flags = [{"trap": t[0], "fix": t[1]} for t in TRAPS if t[0] in low]
    if re.search(r"субсид|субвенци|грант", low):
        flags.append({"trap": "субсидии", "fix": "вычтите субсидии из FCF и сверьте с чистым операционным FCF"})
    profit = lines.get("net_profit") or lines.get("прибыль")
    ocf = cash.get("ocf") or cash.get("операционный поток")
    mismatch = None
    if isinstance(profit, (int, float)) and isinstance(ocf, (int, float)):
        mismatch = {"profit": profit, "ocf": ocf,
                    "note": ("знаки расходятся: разбирай разовые статьи" if (profit < 0 < ocf) else
                             "кэш и прибыль расходятся — нужна сверка") if profit * ocf < 0 else
                            "направления совпадают — сверка простая"}
    conf = "high" if lines and cash else ("medium" if lines or cash else "low")
    adversarial = ["Какой вывод был бы принят без сверки прибыль vs кэш и чем грозил",
                   "Какая строка может быть не тем, чем кажется (GMV vs выручка, EBITDA vs прибыль)"]
    if mismatch:
        adversarial.append(f"Расхождение: {mismatch['note']}")
    return {"confidence": conf, "flags": flags, "standard": d.get("standard", "не указан"),
            "mismatch": mismatch, "adversarial": adversarial,
            "brief": {"level_of_evidence": "факт/расчёт/гипотеза — проставить по каждой строке",
                      "open_questions": ["структура долга", "разовые статьи", "устойчивость нерынночных поступлений"]}}
