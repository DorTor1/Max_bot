"""Компактные callback payload: gp:v1:<action>[:<arg>]"""

PREFIX = "gp:v1"


def encode(action: str, arg: str | None = None) -> str:
    if arg is None:
        return f"{PREFIX}:{action}"
    return f"{PREFIX}:{action}:{arg}"


def decode(payload: str) -> tuple[str, str | None]:
    parts = payload.split(":", 2)
    if len(parts) < 3 or parts[0] != "gp" or parts[1] != "v1":
        return "", None
    rest = payload[len("gp:v1:") :]
    if ":" in rest:
        action, arg = rest.split(":", 1)
        return action, arg
    return rest, None
