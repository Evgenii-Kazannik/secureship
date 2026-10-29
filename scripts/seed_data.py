#!/usr/bin/env python3
"""Seed the SecureShip database. Safe to run multiple times (upserts on natural keys)."""

import json
import os
import random
from datetime import date, timedelta
from pathlib import Path

import psycopg

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_FIXTURES = _ROOT / "scripts" / "fixtures" / "demo-identities.json"
RANDOM_SEED = 42
TARGET_CUSTOMERS = 25
TARGET_SHIPMENTS = 50

# Load .env so the script works when run directly (not via docker-compose)
_env = _ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://secureship:secureship@localhost:5432/secureship",
)

# ---------------------------------------------------------------------------
# Generated data pools
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Alex", "Morgan", "Jamie", "Taylor", "Casey", "Riley", "Drew", "Blake",
    "Quinn", "Reese", "Parker", "Hayden", "Skyler", "Cameron", "Peyton",
    "Dakota", "Kendall", "Logan", "Rowan", "Sage", "Finley", "Elliot",
    "Harper", "River", "Emery",
]
LAST_NAMES = [
    "Williams", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore",
    "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez",
    "Lewis", "Lee", "Walker", "Hall", "Allen",
]
CITIES = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"),
    ("Houston", "TX", "77001"), ("Phoenix", "AZ", "85001"),
    ("Philadelphia", "PA", "19103"), ("San Antonio", "TX", "78201"),
    ("San Diego", "CA", "92101"), ("Dallas", "TX", "75201"),
    ("Denver", "CO", "80201"), ("Seattle", "WA", "98101"),
    ("Nashville", "TN", "37201"), ("Boston", "MA", "02101"),
    ("Las Vegas", "NV", "89101"), ("Atlanta", "GA", "30301"),
    ("Miami", "FL", "33101"), ("Minneapolis", "MN", "55401"),
    ("Tampa", "FL", "33601"), ("Pittsburgh", "PA", "15201"),
    ("Cleveland", "OH", "44101"), ("New Orleans", "LA", "70112"),
]
STREETS = [
    "Main St", "Oak Ave", "Pine Rd", "Maple Dr", "Cedar Ln",
    "Elm St", "Park Blvd", "Lake Dr", "Hill Rd", "River Rd",
    "Sunset Blvd", "Forest Ave", "Valley Rd", "Spring St", "Garden Ln",
]
CARRIERS = ["MockExpress", "SwiftShip", "ReliablePost", "QuickFreight"]
STATUSES = ["label_created", "in_transit", "out_for_delivery", "delivered", "exception"]
STATUS_WEIGHTS = [0.05, 0.40, 0.10, 0.35, 0.10]
DESCRIPTIONS = [
    "Wireless headphones", "Running shoes", "Coffee maker", "Yoga mat",
    "Backpack", "Phone charger", "Water bottle", "Desk lamp", "Keyboard",
    "Notebook set", "Sunglasses", "Watch", "Jacket", "Cookware set",
    "Bluetooth speaker", "Umbrella", "Tool kit", "Picture frame", "Puzzle",
    "Board game", "Candle set", "Tea set", "Art supplies", "Dumbbell",
    "Plant pot", "Throw pillow", "Sneakers", "Journal", "Hand cream",
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id           SERIAL PRIMARY KEY,
    first_name   TEXT NOT NULL,
    last_name    TEXT NOT NULL,
    phone_number TEXT NOT NULL UNIQUE,
    address      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shipments (
    id                SERIAL PRIMARY KEY,
    customer_id       INTEGER NOT NULL REFERENCES customers(id),
    tracking_number   TEXT NOT NULL UNIQUE,
    status            TEXT NOT NULL CHECK (status IN (
                          'label_created', 'in_transit', 'out_for_delivery',
                          'delivered', 'exception'
                      )),
    carrier           TEXT NOT NULL,
    origin            TEXT NOT NULL,
    destination       TEXT NOT NULL,
    estimated_delivery DATE,
    last_update       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS packages (
    id             SERIAL PRIMARY KEY,
    shipment_id    INTEGER NOT NULL REFERENCES shipments(id),
    description    TEXT NOT NULL,
    weight_kg      NUMERIC(6, 2),
    declared_value NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    state       TEXT NOT NULL DEFAULT 'anonymous',
    transcript  JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def upsert_customer(cur, first_name, last_name, phone_number, address):
    cur.execute(
        """
        INSERT INTO customers (first_name, last_name, phone_number, address)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (phone_number) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name  = EXCLUDED.last_name,
            address    = EXCLUDED.address
        RETURNING id
        """,
        (first_name, last_name, phone_number, address),
    )
    return cur.fetchone()[0]


def upsert_shipment(cur, customer_id, tracking, status, carrier, origin, dest, eta):
    cur.execute(
        """
        INSERT INTO shipments
            (customer_id, tracking_number, status, carrier, origin, destination, estimated_delivery)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tracking_number) DO UPDATE SET
            customer_id        = EXCLUDED.customer_id,
            status             = EXCLUDED.status,
            carrier            = EXCLUDED.carrier,
            origin             = EXCLUDED.origin,
            destination        = EXCLUDED.destination,
            estimated_delivery = EXCLUDED.estimated_delivery
        RETURNING id
        """,
        (customer_id, tracking, status, carrier, origin, dest, eta),
    )
    return cur.fetchone()[0]


def insert_package_if_missing(cur, shipment_id, description, weight_kg, declared_value):
    cur.execute("SELECT 1 FROM packages WHERE shipment_id = %s", (shipment_id,))
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO packages (shipment_id, description, weight_kg, declared_value) VALUES (%s, %s, %s, %s)",
        (shipment_id, description, weight_kg, declared_value),
    )


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


def seed(conn, rng):
    fixtures = json.loads(_FIXTURES.read_text())
    today = date.today()

    with conn.cursor() as cur:
        # --- Demo rows ---
        demo_ids: dict[str, int] = {}
        for c in fixtures["customers"]:
            cid = upsert_customer(cur, c["first_name"], c["last_name"], c["phone_number"], c["address"])
            demo_ids[f"{c['first_name']} {c['last_name']}"] = cid

        tracking_to_sid: dict[str, int] = {}
        for s in fixtures["shipments"]:
            sid = upsert_shipment(
                cur,
                demo_ids[s["customer_ref"]],
                s["tracking_number"],
                s["status"],
                s["carrier"],
                s["origin"],
                s["destination"],
                date.fromisoformat(s["estimated_delivery"]),
            )
            tracking_to_sid[s["tracking_number"]] = sid

        for p in fixtures["packages"]:
            insert_package_if_missing(
                cur, tracking_to_sid[p["tracking_number"]],
                p["description"], p["weight_kg"], p["declared_value"],
            )

        # --- Generated customers ---
        all_customer_ids = list(demo_ids.values())
        used_phones = {c["phone_number"] for c in fixtures["customers"]}
        used_names = set(demo_ids)
        phone_n = 4

        pairs = list(zip(rng.sample(FIRST_NAMES, len(FIRST_NAMES)), rng.sample(LAST_NAMES, len(LAST_NAMES))))
        for first, last in pairs:
            if len(all_customer_ids) >= TARGET_CUSTOMERS:
                break
            if f"{first} {last}" in used_names:
                continue
            phone = f"+1555123{phone_n:04d}"
            while phone in used_phones:
                phone_n += 1
                phone = f"+1555123{phone_n:04d}"
            used_phones.add(phone)
            used_names.add(f"{first} {last}")
            city, state, zipcode = rng.choice(CITIES)
            address = f"{rng.randint(1, 999)} {rng.choice(STREETS)}, {city}, {state} {zipcode}"
            cid = upsert_customer(cur, first, last, phone, address)
            all_customer_ids.append(cid)
            phone_n += 1

        # --- Generated shipments ---
        total = len(fixtures["shipments"])
        tracking_n = 10004
        while total < TARGET_SHIPMENTS:
            tracking = f"MX{tracking_n:05d}"
            tracking_n += 1
            cid = rng.choice(all_customer_ids)
            status = rng.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
            o_city, o_state, _ = rng.choice(CITIES)
            d_city, d_state, _ = rng.choice(CITIES)
            eta = today + timedelta(days=rng.randint(-14, 14))
            sid = upsert_shipment(
                cur, cid, tracking, status,
                rng.choice(CARRIERS),
                f"{o_city}, {o_state}",
                f"{d_city}, {d_state}",
                eta,
            )
            insert_package_if_missing(
                cur, sid,
                rng.choice(DESCRIPTIONS),
                round(rng.uniform(0.2, 15.0), 2),
                round(rng.uniform(10.0, 500.0), 2),
            )
            total += 1

    conn.commit()
    print(f"  customers : {len(all_customer_ids)}")
    print(f"  shipments : {total}")
    print(f"  packages  : {total}  (one per shipment)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Connecting to", DATABASE_URL.split("@")[-1])  # host only, no credentials
    rng = random.Random(RANDOM_SEED)
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
        print("Schema ready.")
        seed(conn, rng)
    print("Done.")


if __name__ == "__main__":
    main()
