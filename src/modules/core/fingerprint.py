import json

from dataclasses import dataclass


@dataclass
class Fingerprint:
    client_identifier: str
    browser_version: str
    headers: dict
    build_number: int = 364202
    timezone: str = "America/New_York"
    super_properties: str = ""


def get_fingerprints() -> list[Fingerprint]:
    with open("input/fingerprints.json", "r") as f:
        data = json.load(f)
    return [
        Fingerprint(
            client_identifier=fp["client-identifier"],
            browser_version=fp["browser-version"],
            headers=fp["headers"],
        )
        for fp in data
    ]
