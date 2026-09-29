"""Quick sanity check: list the accounts visible to the configured API key."""

from config import get_client


def main() -> None:
    client = get_client()
    accounts = client.get_accounts()
    for account in accounts.accounts:
        balance = account.available_balance
        print(f"{account.currency:<8} {balance['value']:>20}")


if __name__ == "__main__":
    main()
