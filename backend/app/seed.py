import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import User, Recipient, PaymentIntent, PaymentPolicy, Transaction, DecisionTrace, PaymentSuggestion

def seed_database(db: Session, force: bool = False):
    # Check if already seeded
    if not force and db.query(User).count() > 0:
        return

    # Clear existing data if force
    if force:
        db.query(DecisionTrace).delete()
        db.query(Transaction).delete()
        db.query(PaymentSuggestion).delete()
        db.query(PaymentPolicy).delete()
        db.query(PaymentIntent).delete()
        db.query(Recipient).delete()
        db.query(User).delete()
        db.commit()

    random.seed(42)
    now = datetime.now(timezone.utc)

    # 1. User
    user = User(
        id="usr_demo",
        name="Demo User",
        email="demo@intentpay.local",
        monthly_income=50000,
        current_balance=36000,
        upcoming_expenses=15500,
        created_at=now - timedelta(days=95),
        updated_at=now - timedelta(days=95)
    )
    db.add(user)

    # 2. Recipients (10 verified)
    recipients_data = [
        ("rcp_01", "Landlord", True, "Rent"),
        ("rcp_02", "Bescom", True, "Utilities"),
        ("rcp_03", "Water Board", True, "Utilities"),
        ("rcp_04", "Netflix", True, "Entertainment"),
        ("rcp_05", "ACT Fibernet", True, "Internet"),
        ("rcp_06", "Mother", True, "Family"),
        ("rcp_07", "Big Bazaar", True, "Food"),
        ("rcp_08", "Uber", True, "Travel"),
        ("rcp_09", "Amazon", True, "Shopping"),
        ("rcp_10", "Airtel", True, "Utilities"),
    ]
    for rid, rname, rver, rhint in recipients_data:
        db.add(Recipient(
            id=rid,
            name=rname,
            is_verified=rver,
            category_hint=rhint,
            created_at=now - timedelta(days=95),
            updated_at=now - timedelta(days=95)
        ))

    # 3. Intents (4 ACTIVE)
    intents_data = [
        PaymentIntent(
            id="PI-001",
            purpose="Monthly Apartment Rent",
            recipient="Landlord",
            category="Rent",
            amount=15000,
            max_amount=None,
            currency="INR",
            frequency="MONTHLY",
            day_of_month=5,
            trigger="SALARY_RECEIVED",
            action="AUTO_PAY",
            conditions=[{"field": "amount", "operator": "==", "value": 15000}],
            status="ACTIVE",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentIntent(
            id="PI-002",
            purpose="Electricity Bill",
            recipient="Bescom",
            category="Utilities",
            amount=None,
            max_amount=3000,
            currency="INR",
            frequency="MONTHLY",
            day_of_month=None,
            trigger="NONE",
            action="AUTO_PAY",
            conditions=[{"field": "bill_amount", "operator": "<=", "value": 3000}],
            status="ACTIVE",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentIntent(
            id="PI-003",
            purpose="Gambling & Betting Blocked",
            recipient="Stake Casino",
            category="Entertainment",
            amount=None,
            max_amount=None,
            currency="INR",
            frequency="ONCE",
            day_of_month=None,
            trigger="NONE",
            action="BLOCK",
            conditions=[],
            status="ACTIVE",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentIntent(
            id="PI-004",
            purpose="Netflix Subscription",
            recipient="Netflix",
            category="Entertainment",
            amount=499,
            max_amount=None,
            currency="INR",
            frequency="MONTHLY",
            day_of_month=None,
            trigger="NONE",
            action="AUTO_PAY",
            conditions=[{"field": "amount", "operator": "==", "value": 499}],
            status="ACTIVE",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
    ]
    for pi in intents_data:
        db.add(pi)

    # 4. Policies (5 ACTIVE)
    policies_data = [
        PaymentPolicy(
            id="PD-001",
            policy_type="NEW_RECIPIENT_LIMIT",
            threshold=5000,
            scope=None,
            scope_value=None,
            period=None,
            limit=None,
            action="VERIFY",
            status="ACTIVE",
            description="Require verification for payments over ₹5,000 to new recipients",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentPolicy(
            id="PD-002",
            policy_type="PERIOD_LIMIT",
            threshold=None,
            scope="CATEGORY",
            scope_value="Shopping",
            period="WEEK",
            limit=10000,
            action="VERIFY",
            status="ACTIVE",
            description="Require verification if weekly Shopping spend exceeds ₹10,000",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentPolicy(
            id="PD-003",
            policy_type="MAX_TRANSACTION_AMOUNT",
            threshold=25000,
            scope=None,
            scope_value=None,
            period=None,
            limit=None,
            action="VERIFY",
            status="ACTIVE",
            description="Require verification for any single transaction above ₹25,000",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentPolicy(
            id="PD-004",
            policy_type="PERIOD_LIMIT",
            threshold=None,
            scope="CATEGORY",
            scope_value="Family",
            period="MONTH",
            limit=20000,
            action="VERIFY",
            status="ACTIVE",
            description="Require verification if monthly Family category spend exceeds ₹20,000",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
        PaymentPolicy(
            id="PD-005",
            policy_type="PERIOD_LIMIT",
            threshold=None,
            scope="RECIPIENT",
            scope_value="Mother",
            period="MONTH",
            limit=10000,
            action="VERIFY",
            status="ACTIVE",
            description="Require verification if monthly transfers to Mother exceed ₹10,000",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=90)
        ),
    ]
    for pol in policies_data:
        db.add(pol)

    # 5. Transactions: Exactly 27 transactions ending >= 1 day ago
    # Distribution: 21 ALLOW, 5 VERIFY, 1 HOLD
    raw_txs = [
        # Rent (3 months, 3 ALLOW)
        {"id": "TX-0001", "rec": "Landlord", "amt": 15000, "cat": "Rent", "days_ago": 65, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Rent auto-pay intent PI-001"},
        {"id": "TX-0002", "rec": "Landlord", "amt": 15000, "cat": "Rent", "days_ago": 35, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Rent auto-pay intent PI-001"},
        {"id": "TX-0003", "rec": "Landlord", "amt": 15000, "cat": "Rent", "days_ago": 5, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Rent auto-pay intent PI-001"},

        # Electricity (3 ALLOW around 2200 baseline)
        {"id": "TX-0004", "rec": "Bescom", "amt": 2150, "cat": "Utilities", "days_ago": 62, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Electricity bill auto-pay intent PI-002"},
        {"id": "TX-0005", "rec": "Bescom", "amt": 2240, "cat": "Utilities", "days_ago": 32, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Electricity bill auto-pay intent PI-002"},
        {"id": "TX-0006", "rec": "Bescom", "amt": 2190, "cat": "Utilities", "days_ago": 12, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Electricity bill auto-pay intent PI-002"},

        # Internet on 5th of last 3 months (3 ALLOW, ₹999)
        {"id": "TX-0007", "rec": "ACT Fibernet", "amt": 999, "cat": "Internet", "days_ago": 66, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard utility payment within normal behavior"},
        {"id": "TX-0008", "rec": "ACT Fibernet", "amt": 999, "cat": "Internet", "days_ago": 36, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard utility payment within normal behavior"},
        {"id": "TX-0009", "rec": "ACT Fibernet", "amt": 999, "cat": "Internet", "days_ago": 6, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard utility payment within normal behavior"},

        # Netflix (3 ALLOW)
        {"id": "TX-0010", "rec": "Netflix", "amt": 499, "cat": "Entertainment", "days_ago": 70, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Netflix auto-pay intent PI-004"},
        {"id": "TX-0011", "rec": "Netflix", "amt": 499, "cat": "Entertainment", "days_ago": 40, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Netflix auto-pay intent PI-004"},
        {"id": "TX-0012", "rec": "Netflix", "amt": 499, "cat": "Entertainment", "days_ago": 10, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Matched Netflix auto-pay intent PI-004"},

        # Family / Mother (2 ALLOW)
        {"id": "TX-0013", "rec": "Mother", "amt": 5000, "cat": "Family", "days_ago": 50, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Within monthly Family and Mother limits"},
        {"id": "TX-0014", "rec": "Mother", "amt": 5000, "cat": "Family", "days_ago": 18, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Within monthly Family and Mother limits"},

        # Food (Big Bazaar) (4 ALLOW)
        {"id": "TX-0015", "rec": "Big Bazaar", "amt": 1850, "cat": "Food", "days_ago": 75, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard recurring grocery spend"},
        {"id": "TX-0016", "rec": "Big Bazaar", "amt": 2200, "cat": "Food", "days_ago": 48, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard recurring grocery spend"},
        {"id": "TX-0017", "rec": "Big Bazaar", "amt": 1600, "cat": "Food", "days_ago": 22, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard recurring grocery spend"},
        {"id": "TX-0018", "rec": "Big Bazaar", "amt": 1950, "cat": "Food", "days_ago": 8, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Standard recurring grocery spend"},

        # Travel (Uber) (2 ALLOW)
        {"id": "TX-0019", "rec": "Uber", "amt": 650, "cat": "Travel", "days_ago": 42, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Routine transportation fare"},
        {"id": "TX-0020", "rec": "Uber", "amt": 480, "cat": "Travel", "days_ago": 14, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Routine transportation fare"},

        # Shopping (Amazon) (1 ALLOW)
        {"id": "TX-0021", "rec": "Amazon", "amt": 3200, "cat": "Shopping", "days_ago": 28, "dec": "ALLOW", "stat": "EXECUTED_SIMULATED", "reason": "Within weekly shopping limit of ₹10,000"},

        # VERIFY Items (5 total)
        {"id": "TX-0022", "rec": "TNEB Electricity", "amt": 4200, "cat": "Utilities", "days_ago": 15, "dec": "VERIFY", "stat": "PENDING_VERIFICATION", "reason": "Amount ₹4,200 exceeds intent PI-002 max threshold of ₹3,000"},
        {"id": "TX-0023", "rec": "ABC Electronics", "amt": 35000, "cat": "Shopping", "days_ago": 12, "dec": "VERIFY", "stat": "PENDING_VERIFICATION", "reason": "New recipient above ₹5,000 (PD-001), transaction > ₹25,000 (PD-003), and high amount anomaly"},
        {"id": "TX-0024", "rec": "Amazon", "amt": 11000, "cat": "Shopping", "days_ago": 7, "dec": "VERIFY", "stat": "PENDING_VERIFICATION", "reason": "Exceeds weekly Shopping period limit of ₹10,000 (PD-002)"},
        {"id": "TX-0025", "rec": "Mother", "amt": 12000, "cat": "Family", "days_ago": 3, "dec": "VERIFY", "stat": "PENDING_VERIFICATION", "reason": "Exceeds monthly limit of ₹10,000 for recipient Mother (PD-005)"},
        {"id": "TX-0026", "rec": "Cloud Kitchen Fresh", "amt": 5800, "cat": "Food", "days_ago": 2, "dec": "VERIFY", "stat": "PENDING_VERIFICATION", "reason": "New recipient above ₹5,000 (PD-001)"},

        # HOLD Items (1 total)
        {"id": "TX-0027", "rec": "High Risk Offshore Tech", "amt": 1500000, "cat": "Transfer", "days_ago": 1, "dec": "HOLD", "stat": "HELD", "reason": "Transaction amount ₹15,00,000 exceeds simulation ceiling of ₹10,00,000"},
    ]

    for item in raw_txs:
        t_time = now - timedelta(days=item["days_ago"], hours=random.randint(1, 8))
        tx = Transaction(
            id=item["id"],
            recipient=item["rec"],
            amount=item["amt"],
            currency="INR",
            category=item["cat"],
            purpose=f"Payment to {item['rec']}",
            status=item["stat"],
            decision=item["dec"],
            timestamp=t_time,
            created_at=t_time,
            updated_at=t_time
        )
        db.add(tx)

        # Create DecisionTrace for each transaction
        rules_eval = []
        if item["dec"] == "ALLOW":
            rules_eval.append({"id": "RULE-ALLOW", "label": "Standard Checks", "result": "PASS", "detail": "All conditions and policies met"})
        elif item["dec"] == "VERIFY":
            rules_eval.append({"id": "RULE-VERIFY", "label": "Security Verification", "result": "FAIL", "detail": item["reason"]})
        else:
            rules_eval.append({"id": "RULE-HOLD", "label": "Ceiling Limit", "result": "FAIL", "detail": item["reason"]})

        trace = DecisionTrace(
            id=f"TR-{item['id'][3:]}",
            transaction_id=item["id"],
            decision=item["dec"],
            reasons=[item["reason"]],
            rules_evaluated=rules_eval,
            intent_evaluation={"matched": item["cat"] in ["Rent", "Utilities", "Entertainment"]},
            policy_evaluation={"policies_checked": 5},
            behavior_signals=[],
            cash_flow_impact={
                "available": 20500,
                "projected": 20500 - item["amt"],
                "level": "LOW" if item["amt"] < 5000 else "HIGH"
            },
            raw_input={"amount": item["amt"], "recipient": item["rec"], "category": item["cat"]},
            created_at=t_time,
            updated_at=t_time
        )
        db.add(trace)

    # 6. Payment Suggestion (1 pending)
    suggestion = PaymentSuggestion(
        id="PSG-001",
        recipient="ACT Fibernet",
        suggested_amount=999,
        frequency="MONTHLY",
        day_of_month=5,
        category="Internet",
        reason="Detected consistent recurring payment of ₹999 on day 5 of the month for the last 3 months",
        status="PENDING",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2)
    )
    db.add(suggestion)

    db.commit()
