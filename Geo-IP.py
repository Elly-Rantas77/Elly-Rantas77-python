import sys
import requests
import folium
import io
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QComboBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt


class GeoIPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛰️ Geo IP Scanner - Starship Terminal")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #0d0d0d;
                color: #00ffcc;
                font-family: 'Consolas';
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #1a1a1a;
                color: #00ffcc;
                border: 1px solid #00ffcc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #00cc66;
                color: black;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #00ff99;
            }
            QLabel {
                font-weight: bold;
                color: #00ffff;
            }
        """)

        self.popular_ips = {
             "Google DNS 8.8.8.8": "8.8.8.8",
            "Google DNS 8.8.4.4": "8.8.4.4",
            "Cloudflare DNS 1.1.1.1": "1.1.1.1",
            "Cloudflare DNS 1.0.0.1": "1.0.0.1",
            "Quad9 DNS 9.9.9.9": "9.9.9.9",
            "Quad9 DNS 149.112.112.112": "149.112.112.112",
            "OpenDNS 208.67.222.222": "208.67.222.222",
            "OpenDNS 208.67.220.220": "208.67.220.220",
            # Major Cloud Providers
            "Google Cloud 35.190.247.13": "35.190.247.13",
            "Google Cloud 34.102.136.180": "34.102.136.180",
            "AWS S3 52.216.0.0": "52.216.0.0",
            "AWS EC2 3.5.140.0": "3.5.140.0",
            "AWS CloudFront 13.32.0.0": "13.32.0.0",
            "Azure 40.112.0.0": "40.112.0.0",
            "Azure 52.160.0.0": "52.160.0.0",
            # Social Media & Big Sites
            "Facebook 157.240.0.0": "157.240.0.0",
            "Facebook 69.63.176.0": "69.63.176.0",
            "Twitter 104.244.42.1": "104.244.42.1",
            "Twitter 199.16.156.0": "199.16.156.0",
            "Netflix CDN 52.94.0.0": "52.94.0.0",
            "Netflix CDN 198.38.96.0": "198.38.96.0",
            "Apple 17.172.224.47": "17.172.224.47",
            "Apple 17.178.96.59": "17.178.96.59",
            "LinkedIn 108.174.10.10": "108.174.10.10",
            "LinkedIn 108.174.10.11": "108.174.10.11",
            "Wikipedia 91.198.174.192": "91.198.174.192",
            "Wikipedia 208.80.154.224": "208.80.154.224",
            "YouTube 172.217.10.14": "172.217.10.14",
            "YouTube 216.58.194.206": "216.58.194.206",
            "Instagram 157.240.0.1": "157.240.0.1",
            "Dropbox 108.160.160.0": "108.160.160.0",
            "Reddit 151.101.65.140": "151.101.65.140",
            "Reddit 151.101.1.140": "151.101.1.140",
            "GitHub 140.82.112.3": "140.82.112.3",
            "GitHub 140.82.113.4": "140.82.113.4",
            "Slack 13.107.42.15": "13.107.42.15",
            "Spotify 35.186.224.25": "35.186.224.25",
            "Salesforce 96.43.144.41": "96.43.144.41",
            "Adobe 192.150.16.26": "192.150.16.26",
            "Zoom 52.223.208.184": "52.223.208.184",
            "TikTok 47.242.168.0": "47.242.168.0",
            "Pinterest 151.101.192.84": "151.101.192.84",
            "Yahoo 98.139.183.24": "98.139.183.24",
            "eBay 66.135.192.87": "66.135.192.87",
            "PayPal 173.0.82.20": "173.0.82.20",
            # CDNs and ISPs
            "Cloudflare 104.16.0.0": "104.16.0.0",
            "Cloudflare 104.24.0.0": "104.24.0.0",
            "Akamai 23.45.0.0": "23.45.0.0",
            "Akamai 104.64.0.0": "104.64.0.0",
            "Comcast 68.86.80.0": "68.86.80.0",
            "Comcast 68.85.255.0": "68.85.255.0",
            "Verizon 96.110.0.0": "96.110.0.0",
            "T-Mobile 66.209.0.0": "66.209.0.0",
            "AT&T 12.0.0.0": "12.0.0.0",
        }

        self.build_ui()
        self.show_world_map()

    def build_ui(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        ip_layout = QHBoxLayout()

        self.popular_ip_dropdown = QComboBox()
        self.popular_ip_dropdown.addItem("Select Popular IP")
        for name in self.popular_ips:
            self.popular_ip_dropdown.addItem(name)
        self.popular_ip_dropdown.currentIndexChanged.connect(self.popular_ip_selected)

        top_layout.addWidget(QLabel("🌐 Popular IPs:"))
        top_layout.addWidget(self.popular_ip_dropdown)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Type any IP (e.g., 8.8.8.8)")
        self.lookup_btn = QPushButton("🚀 Scan")
        self.lookup_btn.clicked.connect(self.lookup_ip)

        ip_layout.addWidget(QLabel("🛰️ IP Address:"))
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(self.lookup_btn)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.map_view = QWebEngineView()

        layout.addLayout(top_layout)
        layout.addLayout(ip_layout)
        layout.addWidget(QLabel("📡 Geo IP Info:"))
        layout.addWidget(self.result_text, 2)
        layout.addWidget(QLabel("🗺️ Location Map:"))
        layout.addWidget(self.map_view, 5)

        self.setLayout(layout)

    def popular_ip_selected(self, index):
        if index == 0:
            return
        name = self.popular_ip_dropdown.currentText()
        ip = self.popular_ips.get(name, "")
        self.ip_input.setText(ip)

    def lookup_ip(self):
        ip = self.ip_input.text().strip()
        if not ip:
            self.result_text.setText("⚠️ Please enter an IP address.")
            return

        url = f"http://ip-api.com/json/{ip}?fields=66846719"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if data['status'] != 'success':
                self.result_text.setText(f"❌ Error: {data.get('message', 'Unknown error')}")
                self.map_view.setHtml("")
                return

            info = (
                f"🧠 IP: {data.get('query', '')}\n"
                f"🌍 Continent: {data.get('continent', '')}\n"
                f"🇺🇳 Country: {data.get('country', '')} ({data.get('countryCode', '')})\n"
                f"🏙️ Region: {data.get('regionName', '')} ({data.get('region', '')})\n"
                f"📍 City: {data.get('city', '')}\n"
                f"📮 ZIP: {data.get('zip', '')}\n"
                f"🕐 Timezone: {data.get('timezone', '')}\n"
                f"📡 Latitude: {data.get('lat', '')}\n"
                f"📡 Longitude: {data.get('lon', '')}\n"
                f"📶 ISP: {data.get('isp', '')}\n"
                f"🏢 Organization: {data.get('org', '')}\n"
                f"🔌 AS: {data.get('as', '')}\n"
                f"🔁 Reverse DNS: {data.get('reverse', '')}\n"
                f"📱 Mobile: {data.get('mobile', '')}\n"
                f"🛡️ Proxy/VPN: {data.get('proxy', '')}\n"
                f"📦 Hosting: {data.get('hosting', '')}\n"
            )
            self.result_text.setText(info)

            lat = data.get('lat')
            lon = data.get('lon')

            m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB dark_matter")
            folium.Marker([lat, lon], tooltip=ip).add_to(m)

            data_html = io.BytesIO()
            m.save(data_html, close_file=False)
            html_str = data_html.getvalue().decode()
            self.map_view.setHtml(html_str)

        except Exception as e:
            self.result_text.setText(f"🚫 Failed to retrieve data: {e}")
            self.map_view.setHtml("")

    def show_world_map(self):
        m = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB dark_matter")
        data_html = io.BytesIO()
        m.save(data_html, close_file=False)
        html_str = data_html.getvalue().decode()
        self.map_view.setHtml(html_str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeoIPApp()
    window.show()
    sys.exit(app.exec())
