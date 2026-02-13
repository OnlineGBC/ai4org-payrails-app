from typing import Tuple


def validate_routing_number(routing_number: str) -> bool:
    """ABA routing number checksum validation."""
    if len(routing_number) != 9 or not routing_number.isdigit():
        return False

    digits = [int(d) for d in routing_number]
    checksum = (
        3 * (digits[0] + digits[3] + digits[6])
        + 7 * (digits[1] + digits[4] + digits[7])
        + (digits[2] + digits[5] + digits[8])
    )
    return checksum % 10 == 0


def validate_account_number(account_number: str) -> bool:
    """Basic account number length validation."""
    if not account_number.isdigit():
        return False
    return 4 <= len(account_number) <= 17


def generate_micro_deposits() -> Tuple[str, str]:
    """Generate mock micro-deposit amounts for verification."""
    import random
    amount_1 = f"0.{random.randint(1, 99):02d}"
    amount_2 = f"0.{random.randint(1, 99):02d}"
    return amount_1, amount_2


def verify_micro_deposits(
    stored_amount_1: str,
    stored_amount_2: str,
    submitted_amount_1: str,
    submitted_amount_2: str,
) -> bool:
    """Verify micro-deposit amounts match."""
    return stored_amount_1 == submitted_amount_1 and stored_amount_2 == submitted_amount_2


def mock_plaid_verification(routing_number: str, account_number: str) -> dict:
    """Mock Plaid instant verification stub."""
    return {
        "status": "verified",
        "institution_name": "Mock Bank",
        "account_type": "checking",
        "account_mask": account_number[-4:],
    }
