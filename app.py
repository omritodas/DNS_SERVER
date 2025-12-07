from flask import Flask, render_template_string, request, redirect
import time
import subprocess
import os

# ===== CONFIG =====
DNS_SERVER_IP = "192.168.0.5"          # Your DNS server IP
DOMAIN = "home.local"                  # Local domain

FORWARD_ZONE_FILE = "/etc/bind/db.home.local"
REVERSE_ZONE_FILE = "/etc/bind/db.192.168.0"
RECORDS_FILE = "/etc/bind/webdns/records.txt"

app = Flask(__name__)

# ===== MAIN HTML TEMPLATE WITH INLINE CSS =====
HTML = """
<!doctype html>
<html>
<head>
    <title>Local DNS Manager</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 30px; background:#f0f2f5;">

<div style="max-width:900px; margin:auto; background:white; padding:25px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.15);">

<h1 style="margin-top:0; font-size:28px; color:#333;">Local DNS Manager (Bind9)</h1>
<h3 style="color:#666;">Domain: {{ domain }}</h3>

<!-- Current Records Table -->
<div style="margin-top:25px;">
    <h3 style="margin-bottom:10px;">Current Records</h3>

    <table style="width:100%; border-collapse: collapse;">
        <tr style="background:#e9ecef;">
            <th style="padding:10px; border:1px solid #ccc;">Name</th>
            <th style="padding:10px; border:1px solid #ccc;">IP</th>
            <th style="padding:10px; border:1px solid #ccc;">Action</th>
        </tr>

        {% for name, ip in records %}
        <tr>
            <td style="padding:10px; border:1px solid #ccc;">{{ name }}.{{ domain }}</td>
            <td style="padding:10px; border:1px solid #ccc;">{{ ip }}</td>
            <td style="padding:10px; border:1px solid #ccc;">
                <form method="post" action="/delete" style="display:inline;">
                    <input type="hidden" name="name" value="{{ name }}">
                    <input type="submit" value="Delete"
                        style="background:#d9534f; border:none; color:white; padding:6px 12px; border-radius:5px; cursor:pointer;">
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>

<!-- Add Record -->
<div style="margin-top:30px;">
    <h3>Add New Record</h3>
    <form method="post" action="/add">

        <label style="display:block; margin-bottom:6px;">Host (without domain):</label>
        <input type="text" name="name" placeholder="pc1" required
               style="padding:8px; width:250px; border-radius:5px; border:1px solid #ccc;">

        <label style="display:block; margin-top:10px; margin-bottom:6px;">IP Address:</label>
        <input type="text" name="ip" placeholder="192.168.0.10" required
               style="padding:8px; width:250px; border-radius:5px; border:1px solid #ccc;">

        <br><br>
        <input type="submit" value="Add Record"
               style="background:#0275d8; border:none; color:white; padding:10px 20px; border-radius:5px; cursor:pointer;">
    </form>
</div>

<!-- Forward Lookup -->
<div style="margin-top:30px;">
    <h3>Forward Lookup Test</h3>
    <form method="post" action="/test/forward">
        <input type="text" name="hostname" placeholder="pc1.{{ domain }}" required
               style="padding:8px; width:300px; border-radius:5px; border:1px solid #ccc;">
        <input type="submit" value="Test"
               style="background:#5cb85c; border:none; color:white; padding:8px 16px; border-radius:5px; cursor:pointer;">
    </form>
</div>

<!-- Reverse Lookup -->
<div style="margin-top:30px;">
    <h3>Reverse Lookup Test</h3>
    <form method="post" action="/test/reverse">
        <input type="text" name="ip" placeholder="192.168.0.10" required
               style="padding:8px; width:300px; border-radius:5px; border:1px solid #ccc;">
        <input type="submit" value="Test"
               style="background:#5bc0de; border:none; color:white; padding:8px 16px; border-radius:5px; cursor:pointer;">
    </form>
</div>

</div>

</body>
</html>
"""

# ===== LOOKUP RESULT PAGE (INLINE CSS) =====
LOOKUP_HTML = """
<!doctype html>
<html>
<head>
    <title>DNS Lookup Result</title>
</head>
<body style="font-family: Arial; margin: 30px; background:#f0f2f5;">

<div style="max-width:900px; margin:auto; background:white; padding:25px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.15);">

<h2 style="margin-top:0;">{{ title }}</h2>

<pre style="background:#f8f9fa; padding:15px; border-radius:6px; border:1px solid #ccc;">{{ output }}</pre>

<a href="/" style="display:inline-block; margin-top:15px; text-decoration:none; background:#0275d8; color:white; padding:8px 16px; border-radius:5px;">
    ← Back to DNS Manager
</a>

</div>

</body>
</html>
"""

# ===== BACKEND FUNCTIONS =====

def ensure_files():
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    if not os.path.exists(RECORDS_FILE):
        open(RECORDS_FILE, "w").close()
    for path in (FORWARD_ZONE_FILE, REVERSE_ZONE_FILE):
        if not os.path.exists(path):
            open(path, "w").close()

def load_records():
    ensure_files()
    records = []
    try:
        with open(RECORDS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) == 2:
                    records.append((parts[0], parts[1]))
    except FileNotFoundError:
        pass
    return records

def save_records(records):
    ensure_files()
    with open(RECORDS_FILE, "w") as f:
        for name, ip in records:
            f.write(f"{name} {ip}\n")

def generate_zone_files(records):
    """Generate forward and reverse zone files."""
    ensure_files()
    serial = int(time.strftime("%Y%m%d%H"))

    forward_header = f"""$TTL 604800
@   IN  SOA ns1.{DOMAIN}. admin.{DOMAIN}. (
        {serial}
        604800
        86400
        2419200
        604800 )

@       IN  NS      ns1.{DOMAIN}.
ns1     IN  A       {DNS_SERVER_IP}
"""

    reverse_header = f"""$TTL 604800
@   IN  SOA ns1.{DOMAIN}. admin.{DOMAIN}. (
        {serial}
        604800
        86400
        2419200
        604800 )

@       IN  NS      ns1.{DOMAIN}.
"""

    forward_lines = [forward_header]
    reverse_lines = [reverse_header]

    for name, ip in records:
        forward_lines.append(f"{name}    IN  A   {ip}")

        parts = ip.split(".")
        if len(parts) == 4 and parts[:3] == ["192", "168", "0"]:
            reverse_lines.append(f"{parts[3]}    IN  PTR {name}.{DOMAIN}.")

    with open(FORWARD_ZONE_FILE, "w") as f:
        f.write("\n".join(forward_lines) + "\n")

    with open(REVERSE_ZONE_FILE, "w") as f:
        f.write("\n".join(reverse_lines) + "\n")

def reload_bind():
    subprocess.run(["sudo", "systemctl", "reload", "bind9"])

# ===== ROUTES =====

@app.route("/")
def index():
    records = load_records()
    return render_template_string(HTML, records=records, domain=DOMAIN)

@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name", "").strip()
    ip = request.form.get("ip", "").strip()
    if name and ip:
        records = load_records()
        records = [r for r in records if r[0] != name]
        records.append((name, ip))
        save_records(records)
        generate_zone_files(records)
        reload_bind()
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_record():
    name = request.form.get("name", "").strip()
    if name:
        records = load_records()
        records = [r for r in records if r[0] != name]
        save_records(records)
        generate_zone_files(records)
        reload_bind()
    return redirect("/")

@app.route("/test/forward", methods=["POST"])
def test_forward():
    hostname = request.form.get("hostname", "").strip()
    result = subprocess.run(
        ["nslookup", hostname, "127.0.0.1"],
        capture_output=True,
        text=True
    )
    return render_template_string(LOOKUP_HTML, title=f"Forward Lookup: {hostname}", output=result.stdout + result.stderr)

@app.route("/test/reverse", methods=["POST"])
def test_reverse():
    ip = request.form.get("ip", "").strip()
    result = subprocess.run(
        ["nslookup", ip, "127.0.0.1"],
        capture_output=True,
        text=True
    )
    return render_template_string(LOOKUP_HTML, title=f"Reverse Lookup: {ip}", output=result.stdout + result.stderr)

if __name__ == "__main__":
    ensure_files()
    app.run(host="0.0.0.0", port=5000)
