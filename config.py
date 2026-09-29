"""Load Coinbase API credentials from a local, git-ignored JSON config file."""

import json
from pathlib import Path

from coinbase.rest import RESTClient

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Copy config.example.json to config.json and fill in your API key."
        )

    with path.open(encoding="utf-8") as f:
        config = json.load(f)

    # Also accept the key file format downloaded from the Coinbase Developer Platform.
    api_key = config.get("api_key") or config.get("name")
    api_secret = config.get("api_secret") or config.get("privateKey")
    if not api_key or not api_secret:
        raise ValueError(f"{path} must contain 'api_key' and 'api_secret'.")

    return {**config, "api_key": api_key, "api_secret": api_secret}


def get_client(path: Path | str = DEFAULT_CONFIG_PATH) -> RESTClient:
    config = load_config(path)
    return RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])
