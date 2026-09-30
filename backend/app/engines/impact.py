"""
Payment Impact & What-If Financial Engine (Pure Python, No DB, No Network)
Deterministic cash-flow impact calculation with clear financial assumptions.
"""

from typing import Dict, Any, Optional

def calculate_payment_impact(
    amount: int,
    current_balance: int,
    upcoming_expenses: int,
    monthly_income: int
) -> Dict[str, Any]:
    available = current_balance - upcoming_expenses
    projected = available - amount

    monthly_impact_pct = round((amount / monthly_income * 100), 1) if monthly_income > 0 else 0.0

    # Determine risk level strictly according to Section 3.7:
    # EXCEEDS_AVAILABLE if projected < 0
    # HIGH if amount > 50% of available OR projected < 10% of income
    # MEDIUM if 25–50% of available
    # else LOW
    if projected < 0:
        level = "EXCEEDS_AVAILABLE"
    elif (available > 0 and amount > 0.50 * available) or (monthly_income > 0 and projected < 0.10 * monthly_income):
        level = "HIGH"
    elif available > 0 and (0.25 * available <= amount <= 0.50 * available):
        level = "MEDIUM"
    else:
        level = "LOW"

    assumptions = [
        f"Available liquidity = Current balance (₹{current_balance:,}) − Upcoming obligations (₹{upcoming_expenses:,}) = ₹{available:,}",
        f"Single simulated outlay = ₹{amount:,}",
        f"Projected remaining liquidity after payment = ₹{projected:,}",
        f"Impact on monthly income (₹{monthly_income:,}) = {monthly_impact_pct}%"
    ]

    return {
        "current_balance": current_balance,
        "upcoming_expenses": upcoming_expenses,
        "available_balance": available,
        "available_liquidity": available,
        "payment_amount": amount,
        "projected_balance": projected,
        "monthly_income": monthly_income,
        "monthly_impact_pct": monthly_impact_pct,
        "impact_level": level,
        "risk_level": level,
        "warning": "Exceeds available liquidity: Projected cash balance is negative" if level == "EXCEEDS_AVAILABLE" else None,
        "label": "Projected cash-flow impact",
        "assumptions": assumptions
    }

def calculate_what_if_scenario(
    payment_amount: int,
    current_balance: int,
    monthly_income: int,
    upcoming_expenses: int,
    loan_amount: int = 0,
    recurring_expense_delta: int = 0
) -> Dict[str, Any]:
    """
    Inputs: payment amount, monthly income, monthly expense, loan amount (EMI), recurring expense delta.
    Output: before/after table for net monthly cash flow, projected month-end balance, impact level, delta.
    """
    # Baseline (Before)
    baseline_expenses = upcoming_expenses
    baseline_net_monthly = monthly_income - baseline_expenses
    baseline_month_end = current_balance + baseline_net_monthly

    # Scenario (After)
    scenario_expenses = upcoming_expenses + loan_amount + recurring_expense_delta
    scenario_net_monthly = monthly_income - scenario_expenses
    scenario_month_end = (current_balance - payment_amount) + scenario_net_monthly

    delta_net = scenario_net_monthly - baseline_net_monthly
    delta_month_end = scenario_month_end - baseline_month_end

    # Impact Level for Scenario
    if scenario_month_end < 0:
        level = "NEGATIVE_BALANCE"
    elif scenario_month_end < (0.10 * monthly_income):
        level = "CRITICAL_LOW"
    elif scenario_net_monthly < 0:
        level = "DEFICIT"
    elif delta_net < -10000:
        level = "SIGNIFICANT"
    else:
        level = "MANAGEABLE"

    return {
        "before": {
            "monthly_income": monthly_income,
            "monthly_expenses": baseline_expenses,
            "net_monthly_cash_flow": baseline_net_monthly,
            "projected_month_end_balance": baseline_month_end
        },
        "after": {
            "payment_outlay": payment_amount,
            "monthly_income": monthly_income,
            "monthly_expenses": scenario_expenses,
            "loan_emi": loan_amount,
            "recurring_delta": recurring_expense_delta,
            "net_monthly_cash_flow": scenario_net_monthly,
            "projected_month_end_balance": scenario_month_end,
            "impact_level": level
        },
        "delta": {
            "net_cash_flow_change": delta_net,
            "month_end_balance_change": delta_month_end
        }
    }
