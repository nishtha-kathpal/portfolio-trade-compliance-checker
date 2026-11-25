import csv
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PORTFOLIO_FILE = BASE_DIR / "portfolio_data.json"
TRADES_FILE = BASE_DIR / "trades_test.csv"
OUTPUT_FILE = BASE_DIR / "trade_results.csv"


# LOAD PORTFOLIO DATA

def load_portfolios():

    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# CREATE TRADE RESULT

def create_result(trade, decision, reason):

    return {
        "portfolio_id": trade.get("portfolio_id", ""),
        "security_id": trade.get("security_id", ""),
        "action": trade.get("action", ""),
        "quantity": trade.get("quantity", ""),
        "price": trade.get("price", ""),
        "security_type": trade.get("security_type", ""),
        "decision": decision,
        "reason": reason
    }


# TRADE COMPLIANCE VALIDATION

def check_trade(trade, portfolio):

    # STEP 1: VALIDATE TRADE DATA

    try:
        quantity = float(trade["quantity"])
        price = float(trade["price"])

        if (
            not math.isfinite(quantity)
            or not math.isfinite(price)
            or quantity <= 0
            or price <= 0
            or trade["action"] not in ["Buy", "Sell"]
            or trade["security_type"] not in ["Equity", "Bond", "ETF"]
        ):

            return create_result(
                trade,
                "Rejected",
                "Invalid trade data."
            )

    except (ValueError, TypeError, KeyError):

        return create_result(
            trade,
            "Rejected",
            "Invalid trade data."
        )

    security_id = trade["security_id"]
    action = trade["action"]

    # STEP 2: RESTRICTED SECURITY CHECK

    if security_id in portfolio["restricted_securities"]:

        return create_result(
            trade,
            "Rejected",
            "Security is restricted for this portfolio."
        )

    # FIND EXISTING HOLDING

    existing_holding = next(
        (
            holding
            for holding in portfolio["current_holdings"]
            if holding["security_id"] == security_id
        ),
        None
    )

    existing_quantity = (
        float(existing_holding["quantity"])
        if existing_holding
        else 0
    )

    # STEP 3: SELL CHECK

    if action == "Sell":

        if existing_quantity < quantity:

            return create_result(
                trade,
                "Rejected",
                "Insufficient holdings to sell."
            )

        return create_result(
            trade,
            "Approved",
            "Trade approved."
        )

    # STEP 4: BUY AFFORDABILITY CHECK

    cash_balance = float(portfolio["cash_balance"])

    trade_cost = quantity * price

    if trade_cost > cash_balance:

        return create_result(
            trade,
            "Rejected",
            "Insufficient cash for this buy order."
        )

    # STEP 5: POSITION CONCENTRATION CHECK

    post_trade_cash = cash_balance - trade_cost

    post_trade_quantity = existing_quantity + quantity

    post_trade_value_of_this_security = (
        post_trade_quantity * price
    )

    # Calculate value of every other security
    # using its own stored market price.

    value_of_other_holdings = sum(
        float(holding["quantity"]) *
        float(holding["market_price"])

        for holding in portfolio["current_holdings"]

        if holding["security_id"] != security_id
    )

    total_portfolio_value_after = (
        post_trade_cash
        + post_trade_value_of_this_security
        + value_of_other_holdings
    )

    if (
        not math.isfinite(total_portfolio_value_after)
        or total_portfolio_value_after <= 0
    ):

        return create_result(
            trade,
            "Rejected",
            "Invalid portfolio valuation."
        )

    position_pct = (
        post_trade_value_of_this_security
        / total_portfolio_value_after
    )

    max_position_pct = float(portfolio["max_position_pct"])

    if position_pct > max_position_pct:

        return create_result(
            trade,
            "Needs Manual Sign-off",
            "Exceeds maximum position concentration — requires approval."
        )

    # STEP 6: ALL CHECKS PASSED

    return create_result(
        trade,
        "Approved",
        "Trade approved."
    )


# PROCESS CSV TRADES

def process_trades():

    portfolios = load_portfolios()

    results = []

    required_columns = {
        "portfolio_id",
        "security_id",
        "action",
        "quantity",
        "price",
        "security_type"
    }

    with open(
        TRADES_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError("CSV is missing required columns.")

        for row in reader:

            portfolio_id = row.get("portfolio_id", "").strip()

            # Find portfolio reference data

            portfolio = portfolios.get(portfolio_id)

            if portfolio is None:

                result = create_result(
                    row,
                    "Rejected",
                    "Portfolio not found."
                )

            else:

                result = check_trade(row, portfolio)

            results.append(result)

    return results


# SAVE RESULTS TO CSV

def save_results(results):

    fieldnames = [
        "portfolio_id",
        "security_id",
        "action",
        "quantity",
        "price",
        "security_type",
        "decision",
        "reason"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(results)


# DISPLAY SUMMARY

def display_summary(results):

    approved = sum(
        r["decision"] == "Approved"
        for r in results
    )

    rejected = sum(
        r["decision"] == "Rejected"
        for r in results
    )

    manual = sum(
        r["decision"] == "Needs Manual Sign-off"
        for r in results
    )

    print("\n" + "=" * 50)
    print("PORTFOLIO TRADE COMPLIANCE SUMMARY")
    print("=" * 50)

    print(f"Total Trades       : {len(results)}")
    print(f"Approved           : {approved}")
    print(f"Rejected           : {rejected}")
    print(f"Needs Manual Sign-off: {manual}")

    print("=" * 50)

    for index, result in enumerate(results, start=1):

        print(f"\nTrade {index}")
        print(f"Portfolio : {result['portfolio_id']}")
        print(f"Security  : {result['security_id']}")
        print(f"Action    : {result['action']}")
        print(f"Quantity  : {result['quantity']}")
        print(f"Price     : {result['price']}")
        print(f"Decision  : {result['decision']}")
        print(f"Reason    : {result['reason']}")

    print("\nResults saved to:", OUTPUT_FILE)


# MAIN FUNCTION

def main():

    try:

        results = process_trades()

        save_results(results)

        display_summary(results)

    except FileNotFoundError as error:

        print("File not found:", error)

    except (ValueError, KeyError, TypeError) as error:

        print("Data error:", error)


if __name__ == "__main__":
    main()