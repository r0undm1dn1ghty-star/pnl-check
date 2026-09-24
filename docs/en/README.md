# P&L Check — English

**P&L Check** is an open-source, evidence-controlled financial diagnostic for AI agents and Russian management-accounting contexts. It helps a company determine whether the available numbers can support a management decision.

## Workflow

**collect facts → reconcile profit and cash → prepare a decision brief**

## What it does NOT do

- Does not replace a CFO, accountant, tax adviser, lawyer, credit committee, or insolvency practitioner.
- Never guesses missing data.
- Never recommends layoffs, business closure, tax avoidance, hidden liabilities, or debt restructuring.
- Does not use the 100 public cards as an industry benchmark.

## Quick start

1. Choose an environment: [Claude Code](../../integrations/claude-code/README.md), a compatible agent skill, or [ChatGPT](../../integrations/chatgpt/README.md).
2. Fill in the [company questionnaire](../../templates/context_questionnaire.md) and attach the [P&L structure](../../templates/pnl_structure.csv).
3. Provide source documents and exports, not just final figures.
4. Ask the agent to start with the **Data Card**. If incomplete, the correct result is a [data gap report](../../templates/data_gap_report.md), not conclusions.
5. Check the result against the [safety rails](../../SAFETY_RAILS.md) and escalate tax/legal/labor/credit questions to a specialist.

## License

Apache 2.0. See [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE.md).
