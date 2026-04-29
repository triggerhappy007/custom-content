#!/usr/bin/env python3
"""
tanium_sensor_deploy.py
-----------------------
Registers/deploys Tanium sensors from an XML or JSON file
into Tanium Data Service (TDS) via the Tanium REST API v2.

Supported input formats:
  --input sensors.xml    Tanium sensor export XML
  --input sensors.json   JSON array of sensor payloads (same structure as API)

Usage:
    python tanium_sensor_deploy.py --input sensors.xml
    python tanium_sensor_deploy.py --input sensors.json
    python tanium_sensor_deploy.py --input sensors.xml --config custom_config.json --force
    python tanium_sensor_deploy.py --input sensors.xml --dry-run
"""

import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
import html
from pathlib import Path

import requests
import urllib3

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default config path
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = Path(__file__).parent / "tanium_config.json"

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """Load JSON config file."""
    if not config_path.exists():
        log.error(f"Config file not found: {config_path}")
        log.info("Create a tanium_config.json file based on the template below:\n")
        print(json.dumps(CONFIG_TEMPLATE, indent=2))
        sys.exit(1)
    with open(config_path) as f:
        cfg = json.load(f)
    required = ["host", "credentials"]
    for key in required:
        if key not in cfg:
            log.error(f"Missing required config key: '{key}'")
            sys.exit(1)
    return cfg


CONFIG_TEMPLATE = {
    "host": "https://your-tanium-server.example.com",
    "credentials": {
        "username": "admin",
        "password": "your_password"
    },
    "verify_ssl": True,
    "timeout_seconds": 30,
    "content_set": "Default"
}

# ---------------------------------------------------------------------------
# Tanium REST API v2 client
# ---------------------------------------------------------------------------

class TaniumClient:
    def __init__(self, cfg: dict):
        self.host = cfg["host"].rstrip("/")
        self.verify_ssl = cfg.get("verify_ssl", True)
        self.timeout = cfg.get("timeout_seconds", 30)
        self.content_set = cfg.get("content_set", "Default")
        self.session = requests.Session()
        self.session.verify = self.verify_ssl

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.warning("SSL verification disabled — not recommended in production.")

        self._authenticate(cfg["credentials"])

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _authenticate(self, creds: dict) -> None:
        """Obtain a Tanium session token."""
        url = f"{self.host}/api/v2/session/login"
        payload = {
            "username": creds["username"],
            "password": creds["password"],
        }
        log.info(f"Authenticating to {self.host} as '{creds['username']}' ...")
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        token = resp.json().get("data", {}).get("session")
        if not token:
            log.error("Authentication succeeded but no session token returned.")
            sys.exit(1)
        self.session.headers.update({"session": token})
        log.info("Authentication successful.")

    # ------------------------------------------------------------------
    # Sensor operations
    # ------------------------------------------------------------------

    def get_sensor_by_name(self, name: str) -> dict | None:
        """Return existing sensor dict if found, else None."""
        url = f"{self.host}/api/v2/sensors"
        params = {"filter[name]": name}
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data[0] if data else None

    def create_sensor(self, payload: dict) -> dict:
        """POST a new sensor to TDS."""
        url = f"{self.host}/api/v2/sensors"
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def update_sensor(self, sensor_id: int, payload: dict) -> dict:
        """PATCH an existing sensor in TDS."""
        url = f"{self.host}/api/v2/sensors/{sensor_id}"
        resp = self.session.patch(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def deploy_sensor(self, payload: dict, force_update: bool = False) -> dict:
        """Create or update a sensor; returns the resulting sensor object."""
        name = payload.get("name", "")
        existing = self.get_sensor_by_name(name)

        if existing:
            sensor_id = existing["id"]
            if force_update:
                log.info(f"Sensor '{name}' already exists (id={sensor_id}). Updating ...")
                result = self.update_sensor(sensor_id, payload)
                log.info(f"Sensor '{name}' updated successfully.")
            else:
                log.warning(
                    f"Sensor '{name}' already exists (id={sensor_id}). "
                    "Use --force to overwrite."
                )
                return existing
        else:
            log.info(f"Creating new sensor '{name}' ...")
            result = self.create_sensor(payload)
            log.info(f"Sensor '{name}' created successfully (id={result.get('id')}).")

        return result

    def logout(self) -> None:
        try:
            self.session.delete(f"{self.host}/api/v2/session/login", timeout=self.timeout)
            log.info("Session closed.")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# XML parsing
# ---------------------------------------------------------------------------

OS_MAP = {"0": "Windows", "1": "Linux", "2": "macOS"}
SENSOR_TYPE_MAP = {"8": "Python", "6": "Shell"}


def parse_sensors_xml(xml_path: Path) -> list[dict]:
    """
    Parse a Tanium sensor export XML and return a list of sensor payload dicts
    ready to POST to the REST API v2.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    sensors = []

    for sensor_el in root.findall("sensor"):

        def _text(tag):
            el = sensor_el.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        # --- Queries ---
        queries = []
        for q_el in sensor_el.findall("./queries/sensor_query"):
            st_el = q_el.find("sensor_type")
            os_el = q_el.find("os")
            raw_q = q_el.find("query")

            queries.append({
                "script_type": SENSOR_TYPE_MAP.get(
                    st_el.text if st_el is not None else "", "Shell"
                ),
                "platform": OS_MAP.get(
                    os_el.text if os_el is not None else "", "Windows"
                ),
                "script": html.unescape(raw_q.text if raw_q is not None and raw_q.text else ""),
            })

        # --- Columns ---
        columns = []
        for col_el in sensor_el.findall("./columns/column"):
            def _col_text(tag):
                el = col_el.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            columns.append({
                "name": _col_text("n"),
                "index": int(_col_text("column_index") or 0),
                "hidden_flag": int(_col_text("hidden_flag") or 0),
                "result_type": int(_col_text("result_type") or 1),
                "ignore_case_flag": int(_col_text("ignore_case_flag") or 1),
            })

        payload = {
            "name": _text("n"),
            "category": _text("category"),
            "description": _text("description"),
            "result_type": int(_text("result_type") or 1),
            "query_interval_seconds": int(_text("qseconds") or 900),
            "ignore_case_flag": int(_text("ignore_case_flag") or 1),
            "delimiter": _text("delimiter") or "|",
            "hidden_flag": int(_text("hidden_flag") or 0),
            "queries": queries,
            "columns": columns,
            "content_set": {"name": _text("./content_set/n") or "Default"},
        }

        sensors.append(payload)
        log.debug(f"Parsed sensor: {payload['name']}")

    return sensors

# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------

def parse_sensors_json(json_path: Path) -> list[dict]:
    """
    Load a JSON file that is either:
      - a JSON array of sensor payload dicts, or
      - a JSON object with a top-level "sensors" or "data" key.

    Each sensor dict should follow the Tanium REST API v2 sensor schema.
    Minimal required key: name.
    """
    with open(json_path) as f:
        raw = json.load(f)

    if isinstance(raw, list):
        sensors = raw
    elif isinstance(raw, dict):
        sensors = raw.get("sensors") or raw.get("data") or [raw]
    else:
        log.error("JSON file must contain an array or an object with a 'sensors' key.")
        sys.exit(1)

    if not sensors:
        log.warning("No sensors found in JSON file.")

    for s in sensors:
        if "name" not in s:
            log.error("Each sensor entry must have a 'name' field.")
            sys.exit(1)

    log.debug(f"Parsed {len(sensors)} sensor(s) from JSON.")
    return sensors


# ---------------------------------------------------------------------------
# Input loader — auto-detects or dispatches by extension
# ---------------------------------------------------------------------------

def load_sensors(input_path: Path) -> list[dict]:
    """Detect file format and parse accordingly."""
    suffix = input_path.suffix.lower()
    if suffix == ".xml":
        log.info(f"Detected XML input: {input_path}")
        return parse_sensors_xml(input_path)
    elif suffix == ".json":
        log.info(f"Detected JSON input: {input_path}")
        return parse_sensors_json(input_path)
    else:
        # Try to sniff the content
        with open(input_path) as f:
            first_char = f.read(1).strip()
        if first_char == "<":
            log.info(f"Sniffed XML content in: {input_path}")
            return parse_sensors_xml(input_path)
        elif first_char in ("{", "["):
            log.info(f"Sniffed JSON content in: {input_path}")
            return parse_sensors_json(input_path)
        else:
            log.error(
                f"Cannot determine format of '{input_path}'. "
                "Use a .xml or .json extension, or ensure the file starts with '<', '{{' or '['."
            )
            sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Deploy Tanium sensors to TDS via REST API v2.\n"
            "Accepts both Tanium XML exports and JSON sensor payloads."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python tanium_sensor_deploy.py --input sensors.xml
  python tanium_sensor_deploy.py --input sensors.json
  python tanium_sensor_deploy.py --input sensors.xml --force
  python tanium_sensor_deploy.py --input sensors.xml --dry-run
        """,
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        metavar="FILE",
        help="Path to sensor file (.xml or .json).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to JSON config file (default: {DEFAULT_CONFIG}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing sensors with the same name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the input and print payloads without contacting the API.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # --- Validate input file ---
    if not args.input.exists():
        log.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # --- Parse input (XML or JSON) ---
    sensors = load_sensors(args.input)
    log.info(f"Found {len(sensors)} sensor(s): {[s['name'] for s in sensors]}")

    # --- Dry run ---
    if args.dry_run:
        log.info("Dry-run mode — no API calls will be made.")
        for sensor in sensors:
            print(json.dumps(sensor, indent=2))
        return

    # --- Load config & connect ---
    cfg = load_config(args.config)
    client = TaniumClient(cfg)

    # --- Deploy each sensor ---
    results = []
    try:
        for sensor in sensors:
            result = client.deploy_sensor(sensor, force_update=args.force)
            results.append(result)
    finally:
        client.logout()

    log.info(f"Done. {len(results)} sensor(s) processed.")


if __name__ == "__main__":
    main()
