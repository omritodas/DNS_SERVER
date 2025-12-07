# 🔧 Local DNS Manager (Bind9 + Flask)

A simple and powerful **web-based DNS management panel** built using **Python Flask** and **Bind9**, designed for local networks (home.lab or office LAN).

This tool allows you to:

✔ Add DNS A records  
✔ Auto-generate reverse PTR records  
✔ Delete DNS records  
✔ Reload Bind9 from web interface  
✔ Test Forward Lookup  
✔ Test Reverse Lookup  
✔ Clean and modern UI (inline CSS)  

Works perfectly inside **WSL (Windows Subsystem for Linux)** or **any Linux server**.

---

## 🚀 Features

### ⭐ DNS Management
- Add / remove A records
- Automatic **forward zone** generation
- Automatic **reverse zone** generation
- Auto-updates SOA serial
- Reloads Bind9 instantly

### ⭐ DNS Testing Tools
- Built-in **Forward Lookup Test**
- Built-in **Reverse Lookup Test**
- Results displayed in styled output box

### ⭐ Interface
- Modern inline CSS UI (no external files needed)
- Clean tables, buttons, forms
- Responsive layout

---

## 📁 Project Structure

dns-panel/
├── app.py # Main Flask application
└── README.md # This file


Bind9 zone files (not included in repo):



/etc/bind/db.home.local
/etc/bind/db.192.168.0
/etc/bind/webdns/records.txt


---

## 🛠 Requirements

### System:
- Ubuntu / Debian / WSL (Windows Subsystem for Linux)
- Python 3.x
- Bind9 DNS server installed

### Python packages:


pip install flask


---

## 📦 Installation (Bind9 + Flask)

### Install Bind9 and tools:


sudo apt update
sudo apt install bind9 bind9-utils dnsutils python3-pip -y
pip3 install flask

⚙️ Bind9 Configuration

Edit:

sudo nano /etc/bind/named.conf.local


Add:

zone "home.local" {
    type master;
    file "/etc/bind/db.home.local";
};

zone "0.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/db.192.168.0";
};


Create these files:

/etc/bind/db.home.local
/etc/bind/db.192.168.0


Example forward zone file:

$TTL 604800
@   IN  SOA ns1.home.local. admin.home.local. (
        2025120601
        604800
        86400
        2419200
        604800 )

@       IN  NS      ns1.home.local.
ns1     IN  A       192.168.0.5


Restart Bind9:

sudo systemctl restart bind9

▶️ Run the DNS Manager Web App

Navigate to project folder:

cd ~/webdns
python3 app.py


Open in your browser:

http://localhost:5000


If using WSL, access from Windows browser:

http://127.0.0.1:5000

🌐 Using the Web Panel
Add DNS Record

Enter hostname (ex: pc1)

Enter IP (ex: 192.168.0.10)

Click Add Record

Delete DNS Record

Click Delete next to the row

Test DNS

Forward Test: pc1.home.local

Reverse Test: 192.168.0.10


🔒 Permissions

Allow Flask app to reload Bind9:

sudo visudo


Add:

omrito ALL=NOPASSWD: /bin/systemctl reload bind9

💡 Running on Windows (WSL)

Install WSL:

wsl --install


Install Ubuntu.

Setup Bind9 + Flask inside WSL.

Access UI via Windows browser:

http://localhost:5000

🤝 Contributing

Pull requests are welcome!
Feel free to open issues for bugs or feature suggestions.
