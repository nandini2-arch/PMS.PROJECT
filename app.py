"""Parking Management System - website (Flask).
Run:  pip install flask   then   python app.py   and open http://127.0.0.1:5000
Login: admin / admin123
"""
from flask import Flask, render_template_string, request, redirect, session, flash
import parking_core as pc

app = Flask(__name__)
app.secret_key = "change-this-secret"

PAGE = """
<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Parking</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#f1f5f9;color:#0f172a}
 header{background:#1e3a8a;color:#fff;padding:14px 24px;display:flex;justify-content:space-between;align-items:center}
 header a{color:#fff;margin-left:16px;text-decoration:none}
 main{max-width:960px;margin:24px auto;padding:0 16px}
 .card{background:#fff;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 1px 4px #0002}
 .grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
 .slot{padding:16px 4px;text-align:center;border-radius:10px;font-weight:600}
 .free{background:#dcfce7;color:#166534}.busy{background:#fee2e2;color:#991b1b}
 input,select,button{padding:9px;border-radius:8px;border:1px solid #cbd5e1;font-size:15px}
 button{background:#2563eb;color:#fff;border:0;cursor:pointer}
 button.red{background:#dc2626}
 table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #e2e8f0;text-align:left}
 .msg{background:#fef9c3;padding:10px;border-radius:8px;margin-bottom:14px}
 .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
 .stat{background:#eff6ff;padding:14px;border-radius:10px}.stat b{display:block;font-size:24px}
</style></head><body>
<header><h2 style="margin:0">🅿️ Smart Parking</h2>
{% if session.get('user') %}<nav><a href="/">Dashboard</a><a href="/reports">Reports</a><a href="/logout">Logout</a></nav>{% endif %}</header>
<main>
{% for m in get_flashed_messages() %}<div class="msg">{{ m }}</div>{% endfor %}

{% if page == 'login' %}
<div class="card" style="max-width:340px;margin:60px auto"><h3>Admin Login</h3>
<form method="post" style="display:grid;gap:10px">
<input name="user" placeholder="Username" required><input name="pw" type="password" placeholder="Password" required>
<button>Login</button></form></div>

{% elif page == 'home' %}
<div class="card"><h3>Slots ({{ r.free }} free of {{ r.total_slots }})</h3><div class="grid">
{% for s in range(1, r.total_slots + 1) %}
 <div class="slot {{ 'busy' if s in used else 'free' }}">Slot {{ s }}<br>{{ used.get(s, 'Free') }}</div>
{% endfor %}</div></div>

<div class="card"><h3>Park a vehicle</h3>
<form method="post" action="/park" style="display:flex;gap:10px;flex-wrap:wrap">
<input name="plate" placeholder="Plate e.g. AP39AB1234" required>
<select name="vtype"><option>Bike</option><option>Car</option><option>Truck</option></select>
<button>Park</button></form></div>

<div class="card"><h3>Parked now</h3>
<form style="margin-bottom:10px"><input name="q" placeholder="Search plate" value="{{ q }}"><button>Search</button></form>
<table><tr><th>Slot</th><th>Plate</th><th>Type</th><th>Entry</th><th></th></tr>
{% for v in vehicles %}<tr><td>{{ v.slot }}</td><td>{{ v.plate }}</td><td>{{ v.type }}</td><td>{{ v.entry }}</td>
<td><form method="post" action="/exit/{{ v.plate }}"><button class="red">Exit &amp; Bill</button></form></td></tr>
{% else %}<tr><td colspan="5">No vehicles.</td></tr>{% endfor %}</table></div>

{% else %}
<div class="stats">
<div class="stat">Occupied<b>{{ r.occupied }}</b></div><div class="stat">Free<b>{{ r.free }}</b></div>
<div class="stat">Vehicles served<b>{{ r.vehicles_served }}</b></div><div class="stat">Revenue<b>₹{{ r.revenue }}</b></div></div>
<div class="card" style="margin-top:18px"><h3>History</h3>
<table><tr><th>Slot</th><th>Plate</th><th>Type</th><th>Entry</th><th>Exit</th><th>Fee</th></tr>
{% for v in rows %}<tr><td>{{ v.slot }}</td><td>{{ v.plate }}</td><td>{{ v.type }}</td><td>{{ v.entry }}</td><td>{{ v.exit }}</td><td>{{ v.fee }}</td></tr>{% endfor %}
</table></div>
{% endif %}
</main></body></html>
"""


def guard():
    return None if session.get("user") else redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == "admin" and request.form["pw"] == "admin123":
            session["user"] = "admin"
            return redirect("/")
        flash("Wrong username or password")
    return render_template_string(PAGE, page="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def home():
    if guard():
        return guard()
    q = request.args.get("q", "")
    vehicles = pc.active(pc.search(q) if q else pc.load())
    used = {int(v["slot"]): v["plate"] for v in pc.active(pc.load())}
    return render_template_string(PAGE, page="home", r=pc.report(), used=used, vehicles=vehicles, q=q)


@app.route("/park", methods=["POST"])
def park():
    if guard():
        return guard()
    try:
        rec = pc.park(request.form["plate"], request.form["vtype"])
        flash(f"Parked in slot {rec['slot']}")
    except ValueError as e:
        flash(str(e))
    return redirect("/")


@app.route("/exit/<plate>", methods=["POST"])
def exit_(plate):
    if guard():
        return guard()
    try:
        rec = pc.exit_vehicle(plate)
        flash(f"{rec['plate']} bill: ₹{rec['fee']}")
    except ValueError as e:
        flash(str(e))
    return redirect("/")


@app.route("/reports")
def reports():
    if guard():
        return guard()
    return render_template_string(PAGE, page="reports", r=pc.report(), rows=pc.load())


if __name__ == "__main__":
    app.run(debug=True)
