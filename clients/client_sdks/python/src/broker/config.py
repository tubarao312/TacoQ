from dataclasses import dataclass


@dataclass
class BrokerConfig:
    """Configuration for a broker."""

    url: str
    username: str
    password: str
