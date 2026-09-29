"""Test authentication against the Advanced Trade API using List Accounts.

GET https://api.coinbase.com/api/v3/brokerage/accounts
Docs: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/accounts/list-accounts
"""

import sys

from requests.exceptions import ConnectionError, HTTPError

from config import get_client


def main() -> int:
    try:
        client = get_client()
    except (FileNotFoundError, ValueError) as e:
        print(f"Config error: {e}")
        return 1

    try:
        # One account is enough to prove the key is accepted.
        response = client.get_accounts(limit=1)
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        print(f"Authentication failed (HTTP {status}): {e}")
        if status == 401:
            print("Check that the API key name and private key are correct and the key is not expired.")
        elif status == 403:
            print("The key was accepted but lacks permission. Enable the 'View' permission on the key.")
        return 1
    except ConnectionError as e:
        print(f"Could not reach the Coinbase API: {e}")
        return 1
    except Exception as e:
        # The JWT signer raises a plain Exception when the private key can't be loaded.
        print(f"Could not sign the request (is api_secret a valid EC private key?): {e}")
        return 1

    print("Authentication succeeded.")
    print(f"Accounts returned: {len(response.accounts)} (has_next={response.has_next})")
    for account in response.accounts:
        print(f"  {account.currency}: {account.available_balance['value']} ({account.uuid})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
