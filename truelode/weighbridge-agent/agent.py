"""Weighbridge agent: read a scale indicator over serial, POST a weigh event.

Runs on a small PC at the bridge. Falls back to manual entry in the app where
no serial scale is wired. Demo mode generates a reading when --demo is passed.
"""
import argparse
import random
import time

import requests

# Many indicators stream ASCII frames like "ST,GS,+012345kg" — adjust the parse
# below to match the specific scale model on site.


def read_serial(port: str, baud: int) -> float:
    import serial  # pyserial; only needed in real deployments

    with serial.Serial(port, baud, timeout=2) as ser:
        line = ser.readline().decode(errors="ignore")
    digits = "".join(c for c in line if c.isdigit())
    return float(digits or 0)


def post_weigh(api: str, token: str, batch_id: str, kind: str, net_kg: float):
    r = requests.post(f"{api}/api/weighevents",
                      headers={"Authorization": f"Bearer {token}"},
                      json={"batch_id": batch_id, "kind": kind,
                            "net_kg": net_kg, "source": "SCALE_API"})
    r.raise_for_status()
    print("posted", kind, net_kg, "->", r.json().get("reconcile"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:5000")
    p.add_argument("--token", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--kind", default="PLANT_IN")
    p.add_argument("--port", default="COM3")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()

    net = round(random.uniform(29000, 31000)) if args.demo else read_serial(
        args.port, args.baud)
    post_weigh(args.api, args.token, args.batch, args.kind, net)


if __name__ == "__main__":
    main()
