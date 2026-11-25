
# Portfolio Trade Order Compliance & Execution Checker

## Overview
A Python application that validates proposed portfolio trades against compliance and execution-readiness rules. Each trade is classified as Approved, Rejected, or Needs Manual Sign-off, along with a reason.

## Project Structure
```text
portfolio-trade-checker/
├── main.py
├── portfolio_data.json
├── trades_test.csv
└── trade_results.csv
```

## Requirements
- Python 3.x
- Uses only Python built-in libraries.
- No external dependencies required.

## How to Run

1. Open a terminal in the project folder.
2. Execute the following command:

```bash
python main.py
```

## Input Files
- `portfolio_data.json` - Contains portfolio reference data such as cash balance, restricted securities, maximum position percentage, and current holdings.
- `trades_test.csv` - Contains proposed trades for validation.

## Output
The application generates `trade_results.csv`, containing:
- Trade details
- Compliance decision
- Reason for the decision

## Compliance Checks
1. Trade data validation.
2. Restricted security check.
3. Sell holdings validation.
4. Buy affordability check.
5. Position concentration check.
6. Trade approval.

