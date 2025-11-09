from typing import Any

# DISCORD
DISCORD_TOKEN: str = ""


DELETE_RULES: dict[str, dict[str, Any]] = {
    "rule_1": {
        "description": "Complex AND rule example",
        "enabled": True,
        "conditions": {
            "operator": "AND",
            "filters": [
                {
                    "type": "guild",
                    "operator": "EQUALS",
                    "values": 123456789,
                },
                {
                    "type": "user",
                    "operator": "IN",
                    "values": [111111111, 222222222],
                },
                {
                    "type": "timestamp",
                    "operator": "BETWEEN",
                    "start": "2024-01-01T00:00:00",
                    "end": "2024-01-31T23:59:59",
                },
            ],
        },
    },
}

DRY_RUN: bool = True
MAX_DELETIONS_PER_RUN: int = 1000
BATCH_SIZE: int = 100
API_CALL_INTERVAL: float = 0.5
