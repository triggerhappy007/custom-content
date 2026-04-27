#!/usr/bin/env python3
"""
Tanium Discover Interface Puller
---------------------------------
Reads Gateway URL and API token from a config text file,
fetches all 23 DiscoverInterface fields via the Tanium GraphQL Gateway API.

Config file format (default: tanium_config.txt):
    url=https://<customername>-api.cloud.tanium.com/plugin/products/gateway/graphql
    token=token-<your-api-token>

Usage:
    python tanium_discover.py
    python tanium_discover.py --config /path/to/config.txt
    python tanium_discover.py --status unmanaged
    python tanium_discover.py --output results.json
    python tanium_discover.py --list-fields
"""

import argparse
import json
import os
import sys
import requests


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        print(
            "\nCreate a file with the following content:\n"
            "  url=https://<customername>-api.cloud.tanium.com/plugin/products/gateway/graphql\n"
            "  token=token-<your-api-token>\n"
        )
        sys.exit(1)

    config = {}
    with open(config_path) as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                print(f"[WARN] Skipping malformed line {line_no}: {raw.rstrip()}")
                continue
            k, _, v = line.partition("=")
            config[k.strip().lower()] = v.strip()

    for key in ("url", "token"):
        if key not in config:
            print(f"[ERROR] Missing '{key}' in config file.")
            sys.exit(1)

    return config


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def gql(url: str, token: str, query: str, variables: dict = None) -> dict:
    headers = {"session": token, "Content-Type": "application/json"}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out.")
        sys.exit(1)

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code}: {r.text[:600]}")
        sys.exit(1)

    body = r.json()
    if "errors" in body:
        for err in body["errors"]:
            print(f"[ERROR] GraphQL: {err.get('message', err)}")
        sys.exit(1)

    return body


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------

INTROSPECT_QUERY = """
{
  __type(name: "DiscoverInterface") {
    fields {
      name
      type { kind name ofType { kind name } }
    }
  }
}
"""


def introspect_fields(url: str, token: str) -> set:
    body = gql(url, token, INTROSPECT_QUERY)
    type_info = body.get("data", {}).get("__type")
    if not type_info:
        print("[ERROR] Could not introspect DiscoverInterface type.")
        sys.exit(1)
    return {f["name"] for f in type_info["fields"]}


# ---------------------------------------------------------------------------
# All 23 confirmed DiscoverInterface fields
#
# Scalar          : computerId, firstManagedTime, firstSeenTime, id, isIgnored,
#                   isManaged, isUnmanageable, lastDiscoveredTime, lastManagedTime,
#                   lastSeenTime, locallyAdministeredMacAddress, macAddress,
#                   manufacturer, osGeneration, osPlatform
#
# List<scalar>    : discoveryMethods, hostnames, ipAddresses, natIPAddresses, openPorts
#
# List<{name}>    : labels, profiles, satellites
# ---------------------------------------------------------------------------

QUERY_ALL_23 = """
query DiscoverInterfaces($after: Cursor) {
  discoverInterfaces(first: 100, after: $after) {
    edges {
      node {
        id
        computerId
        macAddress
        locallyAdministeredMacAddress
        manufacturer
        osPlatform
        osGeneration
        isManaged
        isIgnored
        isUnmanageable
        firstSeenTime
        lastSeenTime
        lastDiscoveredTime
        firstManagedTime
        lastManagedTime
        ipAddresses
        natIPAddresses
        hostnames
        discoveryMethods
        openPorts
        labels      { name }
        profiles    { name }
        satellites  { name }
      }
    }
    pageInfo { hasNextPage endCursor }
    totalRecords
  }
}
"""


# ---------------------------------------------------------------------------
# Status filter (client-side using boolean flags)
# ---------------------------------------------------------------------------

STATUS_FILTERS = {
    "managed":      lambda n: n.get("isManaged") is True,
    "unmanaged":    lambda n: (n.get("isManaged") is False
                               and not n.get("isIgnored")
                               and not n.get("isUnmanageable")),
    "ignored":      lambda n: n.get("isIgnored") is True,
    "unmanageable": lambda n: n.get("isUnmanageable") is True,
}


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

def fetch_interfaces(url: str, token: str) -> list:
    results = []
    after   = None
    page    = 0
    total   = None

    while True:
        page += 1
        body = gql(url, token, QUERY_ALL_23, {"after": after})
        data = body.get("data", {}).get("discoverInterfaces")
        if data is None:
            print("[ERROR] Unexpected response:")
            print(json.dumps(body, indent=2)[:800])
            sys.exit(1)

        if total is None:
            total = data.get("totalRecords", "?")
            print(f"[INFO] Total interfaces: {total}")

        nodes = [edge["node"] for edge in data.get("edges", [])]
        results.extend(nodes)
        print(f"[INFO] Page {page}: {len(nodes)} records (cumulative: {len(results)})")

        pi = data.get("pageInfo", {})
        if not pi.get("hasNextPage"):
            break
        after = pi.get("endCursor")

    return results


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def cell(iface: dict, field: str) -> str:
    """Render any field value as a plain string for display."""
    val = iface.get(field)
    if isinstance(val, list):
        parts = []
        for v in val:
            parts.append(v.get("name", str(v)) if isinstance(v, dict) else str(v))
        return ", ".join(parts)
    if val is None:
        return ""
    return str(val)


# Columns for the terminal table (subset for readability)
TABLE_COLS = [
    ("IP Addresses",   "ipAddresses"),
    ("MAC Address",    "macAddress"),
    ("Hostnames",      "hostnames"),
    ("OS Platform",    "osPlatform"),
    ("OS Generation",  "osGeneration"),
    ("Manufacturer",   "manufacturer"),
    ("Managed",        "isManaged"),
    ("Ignored",        "isIgnored"),
    ("Last Seen",      "lastSeenTime"),
]


def print_table(interfaces: list) -> None:
    if not interfaces:
        print("No interfaces found.")
        return

    widths = {h: len(h) for h, _ in TABLE_COLS}
    for iface in interfaces:
        for h, f in TABLE_COLS:
            widths[h] = max(widths[h], len(cell(iface, f)))

    sep = "+-" + "-+-".join("-" * widths[h] for h, _ in TABLE_COLS) + "-+"
    hdr = "| " + " | ".join(h.ljust(widths[h]) for h, _ in TABLE_COLS) + " |"

    print(sep)
    print(hdr)
    print(sep)
    for iface in interfaces:
        row = "| " + " | ".join(cell(iface, f).ljust(widths[h]) for h, f in TABLE_COLS) + " |"
        print(row)
    print(sep)
    print(f"\nTotal: {len(interfaces)} interface(s)\n")


def save_json(interfaces: list, path: str) -> None:
    """Save full 23-field data to JSON."""
    with open(path, "w") as f:
        json.dump(interfaces, f, indent=2, default=str)
    print(f"[INFO] Full results (all 23 fields) saved to: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pull Tanium Discover interfaces (all 23 fields) via the GraphQL Gateway API."
    )
    parser.add_argument("--config", default="tanium_config.txt",
                        help="Path to config text file (default: tanium_config.txt)")
    parser.add_argument("--status",
                        choices=["unmanaged", "managed", "ignored", "unmanageable"],
                        default=None,
                        help="Filter by status (default: all)")
    parser.add_argument("--output", default=None,
                        help="Save results to this JSON file")
    parser.add_argument("--list-fields", action="store_true",
                        help="Print all available DiscoverInterface fields and exit")
    args = parser.parse_args()

    cfg   = load_config(args.config)
    url   = cfg["url"].rstrip("/")
    if "/graphql" not in url:
        url += "/plugin/products/gateway/graphql"
    token = cfg["token"]

    print("[INFO] Introspecting DiscoverInterface schema ...")
    available = introspect_fields(url, token)

    if args.list_fields:
        print(f"\nAll fields on DiscoverInterface ({len(available)}):\n")
        for f in sorted(available):
            print(f"  {f}")
        return

    print(f"[INFO] Schema confirmed {len(available)} fields. Fetching data ...")
    print(f"[INFO] Connecting to: {url}")
    if args.status:
        print(f"[INFO] Will filter results to status: {args.status}")
    else:
        print("[INFO] Fetching all interfaces (no status filter)")

    interfaces = fetch_interfaces(url, token)

    if args.status:
        fn = STATUS_FILTERS[args.status]
        interfaces = [n for n in interfaces if fn(n)]
        print(f"[INFO] After '{args.status}' filter: {len(interfaces)} interface(s)")

    print_table(interfaces)

    out = args.output or "tanium_discover_results.json"
    save_json(interfaces, out)


if __name__ == "__main__":
    main()