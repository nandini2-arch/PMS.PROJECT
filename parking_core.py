"""Parking Management System - core logic (used by console app and website)."""
import csv
import os
from datetime import datetime

FILE = "parking.csv"
TOTAL_SLOTS = 10
RATES = {"Bike": 10, "Car": 20, "Truck": 40}   # Rs per hour
FIELDS = ["slot", "plate", "type", "entry", "exit", "fee"]
FMT = "%Y-%m-%d %H:%M:%S"


def load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def save(rows):
    with open(FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def active(rows):
    return [r for r in rows if not r["exit"]]


def find(rows, plate):
    for r in active(rows):
        if r["plate"] == plate:
            return r
    return None


def clean_plate(plate):
    plate = plate.strip().upper().replace(" ", "")
    if not (4 <= len(plate) <= 12 and plate.isalnum()):
        raise ValueError("Plate must be 4-12 letters/digits")
    return plate


def park(plate, vtype):
    plate = clean_plate(plate)
    if vtype not in RATES:
        raise ValueError("Type must be Bike, Car or Truck")
    rows = load()
    if find(rows, plate):
        raise ValueError("Vehicle is already parked")
    used = {int(r["slot"]) for r in active(rows)}
    free = [s for s in range(1, TOTAL_SLOTS + 1) if s not in used]
    if not free:
        raise ValueError("Parking is full")
    rec = {"slot": free[0], "plate": plate, "type": vtype,
           "entry": datetime.now().strftime(FMT), "exit": "", "fee": ""}
    rows.append(rec)
    save(rows)
    return rec


def exit_vehicle(plate):
    plate = clean_plate(plate)
    rows = load()
    rec = find(rows, plate)
    if not rec:
        raise ValueError("Vehicle not found")
    now = datetime.now()
    secs = (now - datetime.strptime(rec["entry"], FMT)).total_seconds()
    hours = max(1, -(-int(secs) // 3600))        # round up, minimum 1 hour
    rec["exit"] = now.strftime(FMT)
    rec["fee"] = hours * RATES[rec["type"]]
    save(rows)
    return rec


def update_plate(old, new):
    old, new = clean_plate(old), clean_plate(new)
    rows = load()
    rec = find(rows, old)
    if not rec:
        raise ValueError("Vehicle not found")
    if find(rows, new):
        raise ValueError("New plate is already parked")
    rec["plate"] = new
    save(rows)


def delete_entry(plate):
    plate = clean_plate(plate)
    rows = load()
    rec = find(rows, plate)
    if not rec:
        raise ValueError("Vehicle not found")
    rows.remove(rec)
    save(rows)


def search(text):
    text = text.strip().upper()
    return [r for r in load() if text in r["plate"]]


def report():
    rows = load()
    done = [r for r in rows if r["exit"]]
    now = len(active(rows))
    by_type = {t: sum(1 for r in rows if r["type"] == t) for t in RATES}
    return {"total_slots": TOTAL_SLOTS, "occupied": now,
            "free": TOTAL_SLOTS - now, "vehicles_served": len(done),
            "revenue": sum(int(r["fee"]) for r in done), "by_type": by_type}
