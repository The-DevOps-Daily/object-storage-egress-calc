#!/usr/bin/env python3
"""Price one month of object storage on every provider in providers.json.

    python3 calc.py --storage-gb 1000 --egress-gb 10000 --gets 5000000 --puts 100000

Prices come from providers.json, where every number has a source URL. The
fine print (free-egress ratios, fair-use policies, bundles, minimum charges,
minimum storage duration) is applied, and anything that puts a scenario
outside a provider's terms is printed as a note next to the price.
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def tiered(amount, tiers):
    """Cost of `amount` units on [[up_to, price], ...] tiers; up_to None = rest."""
    cost, done = 0.0, 0.0
    for up_to, price in tiers:
        span = amount - done if up_to is None else min(amount, up_to) - done
        if span <= 0:
            break
        cost += span * price
        done += span
    return cost


def price(p, s):
    """Return (monthly cost in USD, [notes]) for provider p and scenario s."""
    notes = []
    storage_gb = s["storage_gb"]
    egress_gb = s["egress_gb"]

    # Storage, with a minimum billable amount and a minimum storage duration.
    billable_storage = max(storage_gb, p.get("min_billable_storage_gb", 0))
    if billable_storage > storage_gb:
        notes.append(f"billed for {billable_storage:g} GB minimum")
    min_days = p.get("min_storage_days", 0)
    if min_days and s["lifetime_days"] < min_days:
        # Deleting early is charged as if the object stayed min_days; spread
        # over a month that is roughly min_days / lifetime_days times the data.
        factor = min_days / max(s["lifetime_days"], 1)
        notes.append(f"objects kept {s['lifetime_days']} days are billed for {min_days}")
        billable_storage *= factor

    bundle = p.get("bundle")
    if bundle:
        cost = bundle["price"]
        cost += max(0.0, billable_storage - bundle["storage_gb"]) * bundle["extra_storage_per_gb"]
        cost += max(0.0, egress_gb - bundle["egress_gb"]) * bundle["extra_egress_per_gb"]
    else:
        cost = tiered(billable_storage, p["storage_tiers"])
        eg = p["egress"]
        free = eg.get("free_gb", 0.0)
        ratio = eg.get("free_ratio_of_storage")
        if ratio is not None:
            free = max(free, ratio * storage_gb)
        cost += tiered(max(0.0, egress_gb - free), eg["tiers"])
        policy = eg.get("policy_max_ratio_of_storage")
        if policy is not None and egress_gb > policy * storage_gb:
            notes.append(eg.get("policy_note", "egress above the provider's fair-use policy"))

    req = p.get("requests", {})
    puts = max(0, s["puts"] - req.get("free_class_a", 0))
    gets = max(0, s["gets"] - req.get("free_class_b", 0))
    cost += puts / 1000 * req.get("class_a_per_1000", 0.0)
    cost += gets / 1000 * req.get("class_b_per_1000", 0.0)
    cost += egress_gb * p.get("retrieval_per_gb", 0.0)

    minimum = p.get("minimum_monthly", 0.0)
    if cost < minimum:
        notes.append(f"minimum monthly charge ${minimum:g}")
        cost = minimum
    return cost, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--storage-gb", type=float, required=True, help="data stored, GB")
    ap.add_argument("--egress-gb", type=float, required=True, help="data served to the internet per month, GB")
    ap.add_argument("--gets", type=float, default=0, help="GET/HEAD requests per month")
    ap.add_argument("--puts", type=float, default=0, help="PUT/COPY/POST/LIST requests per month")
    ap.add_argument("--lifetime-days", type=int, default=365, help="how long an object lives before it is deleted")
    ap.add_argument("--providers", default=os.path.join(HERE, "providers.json"))
    a = ap.parse_args()
    s = {"storage_gb": a.storage_gb, "egress_gb": a.egress_gb, "gets": a.gets,
         "puts": a.puts, "lifetime_days": a.lifetime_days}

    data = json.load(open(a.providers))
    rows = sorted((price(p, s) + (p["name"],) for p in data["providers"]), key=lambda r: r[0])
    print(f"{a.storage_gb:,.0f} GB stored, {a.egress_gb:,.0f} GB egress, {a.gets:,.0f} GETs, "
          f"{a.puts:,.0f} PUTs, objects live {a.lifetime_days} days (prices as of {data['as_of']})")
    width = max(len(r[2]) for r in rows)
    for cost, notes, name in rows:
        print(f"  {name:<{width}}  ${cost:>10,.2f}  {'; '.join(notes)}")


if __name__ == "__main__":
    main()
