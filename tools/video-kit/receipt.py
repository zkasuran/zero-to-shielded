"""Panel rows read out of an evidence file a run wrote.

A demo script that spends real money on a real chain already produces the best
possible source for a slide: its own receipt. `channel_rows` turns one MoonWalk
`evidence/channel-*.json` into panel rows, one per step of the lifecycle, with the
gas and the amounts formatted from the atomic values in the file. Nothing here
invents a number, and a step that was refused on chain comes back as a failed row so
the marker and the colour rule land on the refusal.
"""

from __future__ import annotations

import json
from pathlib import Path

from panel import Row


def usd(atomic: int) -> str:
    """USDC has 6 decimals. Trailing zeros go, but money keeps at least two of them."""
    whole, _, fraction = f"{atomic / 1_000_000:.6f}".partition(".")
    fraction = fraction.rstrip("0")
    return f"${whole}.{fraction.ljust(2, '0')}"


def channel_rows(path: Path) -> list[Row]:
    data = json.loads(path.read_text(encoding="utf-8"))
    caps: dict[str, int] = {}
    rows: list[Row] = []
    for step in data["steps"]:
        kind = step["step"]
        if kind == "open":
            rows.append(Row(
                "open, funded by a signature alone",
                f"{usd(step['depositAtomic'])} deposit, {step['gasUsed']:,} gas", "pass",
            ))
        elif kind == "caps":
            caps = {name[:-6]: value for name, value in step.items() if name.endswith("Atomic")}
            rows.append(Row(
                "caps set in the contract",
                ", ".join(f"{name} {usd(value)}" for name, value in caps.items()), "pass",
            ))
        elif kind == "vouchers":
            rows.append(Row(
                f"{step['calls']} vouchers signed off chain",
                f"{usd(step['pricePerCallAtomic'])} a call, digest checked on chain", "pass",
            ))
        elif kind == "redeem":
            rows.append(Row(
                f"{step['callsRepresented']} calls redeemed in one transfer",
                f"{usd(step['totalAtomic'])}, {step['gasUsed']:,} gas, fee {usd(step['gasFeeAtomic'])}",
                "pass",
            ))
        elif kind == "capRefusal":
            limit = caps.get(step["subject"], caps.get("default"))
            against = f" against a {usd(limit)} cap" if limit is not None else ""
            rows.append(Row(
                f"{step['subject']}'s voucher for {usd(step['attemptedAtomic'])}{against}",
                f"{step['error']}, refused on chain", "fail",
            ))
        elif kind == "closeMutual":
            rows.append(Row(
                "mutual close, submitted by the service",
                f"{usd(step['refundAtomic'])} returned to the payer", "pass",
            ))
        else:
            rows.append(Row(kind, "", "plain"))
    summary = data.get("summary", {})
    if "payerTxCountStart" in summary:
        rows.append(Row(
            "transactions sent by the payer, before and after",
            f"{summary['payerTxCountStart']} then {summary['payerTxCountEnd']}", "pass",
        ))
    return rows
