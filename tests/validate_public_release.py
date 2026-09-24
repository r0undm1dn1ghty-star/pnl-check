#!/usr/bin/env python3
"""Проверка структуры репозитория P&L Check."""
import os
import sys

REQUIRED = [
    "README.md", "LICENSE", "NOTICE.md", "AGENTS.md", "CLAUDE.md",
    "SAFETY_RAILS.md", "DATA_EVIDENCE_STANDARD.md",
    "skills/pnl-check/SKILL.md",
    "templates/context_questionnaire.md",
    "templates/pnl_structure.csv",
    "templates/data_gap_report.md",
    "integrations/claude-code/README.md",
    "integrations/mcp/README.md",
    "integrations/chatgpt/README.md",
]

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing = [f for f in REQUIRED if not os.path.exists(os.path.join(root, f))]
    if missing:
        print("MISSING:")
        for f in missing:
            print(f"  {f}")
        sys.exit(1)
    print("OK: все обязательные файлы на месте")
    sys.exit(0)

if __name__ == "__main__":
    main()
