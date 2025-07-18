import sys
import io
import requests
import datetime
import numpy as np
from PIL import Image
from PyQt5.QtCore import Qt, QCoreApplication, QUrl
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QTextEdit, QMessageBox, QLabel, QHBoxLayout,
    QScrollArea, QComboBox, QDateEdit, QGridLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QTextOption
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QDialog, QDialogButtonBox


QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

WEATHER_API_KEY = 'rdPOfU5PvJxo71oMV8JBQS3yirmeutMTowPlxaUC'
WEATHER_API_URL = f'https://api.nasa.gov/insight_weather/?api_key={WEATHER_API_KEY}&feedtype=json&ver=1.0'

ROVER_API_KEY = "0QxccLOP2QBAOixGds65ZXVF3VX6EcIDyAZ6BDRW"
ROVER_API_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos"
ROVER = "Curiosity"
LANDING_DATE = datetime.date(2012, 8, 6)
MAX_DATE = datetime.date(2025, 5, 20)
CAMERAS = ["FHAZ", "RHAZ", "MAST", "CHEMCAM", "MAHLI", "MARDI", "NAVCAM"]

def pil2pixmap(im):
    im = im.convert("RGBA")
    data = np.array(im)
    h, w, ch = data.shape
    bytes_per_line = ch * w
    qimg = QImage(data.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg)

BUTTON_STYLE = """
    QPushButton {
        background-color: #4CAF50;
        border-radius: 8px;
        padding: 8px 14px;
        color: white;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""
class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class RoverPhotosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #121212; color: #eee;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(15)

        self.camera_box = QComboBox()
        self.camera_box.addItems(CAMERAS)
        self.camera_box.setStyleSheet("background-color: #222; color: #eee; padding: 4px; border-radius: 4px;")

        self.date_picker = QDateEdit()
        self.date_picker.setDate(datetime.date(2020, 1, 1))
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setMinimumDate(LANDING_DATE)
        self.date_picker.setMaximumDate(MAX_DATE)
        self.date_picker.setStyleSheet("background-color: #222; color: #eee; padding: 4px; border-radius: 4px;")

        search_button = QPushButton("🔍 Search")
        search_button.setStyleSheet(BUTTON_STYLE)
        search_button.clicked.connect(self.search_photos)

        controls.addWidget(QLabel("Camera:"))
        controls.addWidget(self.camera_box)
        controls.addWidget(QLabel("Date:"))
        controls.addWidget(self.date_picker)
        controls.addWidget(search_button)

        layout.addLayout(controls)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_layout = QGridLayout()
        self.image_layout.setSpacing(15)
        self.image_container.setLayout(self.image_layout)
        self.scroll_area.setWidget(self.image_container)
        layout.addWidget(self.scroll_area)
        
    def show_full_image(self, image: QPixmap):
        dialog = QDialog(self)
        dialog.setWindowTitle("📷 Full Image Viewer")
        dialog.setStyleSheet("background-color: #222; color: #fff;")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)

        image_label = QLabel()
        image_label.setPixmap(image.scaledToWidth(780, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        buttons = QDialogButtonBox()
        save_button = QPushButton("💾 Save Image")
        save_button.setStyleSheet(BUTTON_STYLE)
        buttons.addButton(save_button, QDialogButtonBox.ActionRole)
        buttons.addButton("Close", QDialogButtonBox.RejectRole)

        def save_image():
            file_path, _ = QFileDialog.getSaveFileName(dialog, "Save Image", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
            if file_path:
                image.save(file_path)

        save_button.clicked.connect(save_image)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()
        
    def create_click_handler(self, img):
        def handler(event):
            viewer = PhotoViewer(img, self)
            viewer.exec_()
            return handler


    def search_photos(self):
        camera = self.camera_box.currentText().lower()
        date = self.date_picker.date().toString("yyyy-MM-dd")
        params = {'earth_date': date, 'camera': camera, 'api_key': ROVER_API_KEY}
        url = ROVER_API_URL.format(rover=ROVER.lower())

        try:
            response = requests.get(url, params=params)
            photos = response.json().get("photos", [])
            self.display_photos(photos)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not fetch rover photos: {e}")

    def display_photos(self, photos):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not photos:
            label = QLabel("No photos found for selected date and camera.")
            label.setStyleSheet("color: #aaa; font-style: italic;")
            self.image_layout.addWidget(label, 0, 0)
            return

        columns = 3
        for index, photo in enumerate(photos):
            try:
                img_data = requests.get(photo["img_src"]).content
                full_img = Image.open(io.BytesIO(img_data))
                thumb_img = full_img.copy()
                thumb_img.thumbnail((250, 250))
                pixmap = pil2pixmap(thumb_img)

                label = ClickableLabel()
                label.setPixmap(pixmap)
                label.setToolTip(f"{photo['camera']['full_name']} on {photo['earth_date']}")
                label.setStyleSheet("border: 2px solid #444; border-radius: 6px; padding: 4px;")
                label.setAlignment(Qt.AlignCenter)

                # Connect click signal to open full image
                full_image = pil2pixmap(Image.open(io.BytesIO(img_data)))  # Load full image
                label.clicked.connect(lambda img=full_image: self.show_full_image(img))


                row = index // columns
                col = index % columns
                self.image_layout.addWidget(label, row, col)

            except Exception as e:
                print(f"Failed to load image: {e}")
            


class MarsWeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Mars Explorer Dashboard")
        self.setGeometry(200, 200, 950, 700)
        self.setStyleSheet("""
                           QMainWindow {
                               background-color: #121212;
                               color: #eee;
                               }
                           QTabWidget::pane {
            border: none;
            background: #121212;
            }
            QTabBar {
                margin: 10px 10px 0px 10px;  /* Top, Right, Bottom, Left */
                }
            QTabBar::tab {
                background: #1e1e1e;
                color: #bbb;
                padding: 12px 20px;
                border-radius: 8px 8px 0 0;
                font-weight: 600;
                margin-right: 12px;  /* Space between tabs */
                margin-top: 6px;     /* Space from top edge */
                    }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
                }
            """)


        tabs = QTabWidget()
        tabs.addTab(self.init_weather_tab(), "🌡️")
        tabs.addTab(self.init_map_tab(), "🗺️")
        tabs.addTab(RoverPhotosTab(), "📸")

        self.setCentralWidget(tabs)

    def init_weather_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        widget.setLayout(layout)
        widget.setStyleSheet("background-color: #121212; color: #eee;")
        


        heading = QLabel("Mars Weather Data")
        heading.setStyleSheet("font-size: 18pt; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(heading)

        self.weather_output = QTextEdit()
        self.weather_output.setFont(QFont("Courier", 10))
        self.weather_output.setReadOnly(True)
        self.weather_output.setStyleSheet("background-color: #2b2b2b; color: white;")
        self.weather_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.weather_output.setWordWrapMode(QTextOption.WordWrap)
        self.weather_output.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.weather_output.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)


        layout.addWidget(self.weather_output)

        fetch_btn = QPushButton("Fetch Mars Weather")
        fetch_btn.setStyleSheet(BUTTON_STYLE)
        fetch_btn.clicked.connect(self.fetch_weather)
        layout.addWidget(fetch_btn)

        plot_btn = QPushButton("View Graphs")
        plot_btn.setStyleSheet(BUTTON_STYLE)
        plot_btn.clicked.connect(self.plot_graphs)
        layout.addWidget(plot_btn)

        return widget

    def init_map_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        widget.setLayout(layout)
        map_view = QWebEngineView()
        map_view.load(QUrl("https://mars.nasa.gov/maps/location/"))
        layout.addWidget(map_view)
        return widget

    def fetch_weather(self):
        try:
            response = requests.get(WEATHER_API_URL)
            data = response.json()
            self.weather_data = data
            sol_keys = data.get('sol_keys', [])

            if not sol_keys:
                self.weather_output.setText("No data available.")
                return

            output = ""
            for sol in sol_keys:
                sol_data = data[sol]
                at = sol_data.get('AT', {})
                hws = sol_data.get('HWS', {})
                wd = sol_data.get('WD', {}).get('most_common', {})
                pre = sol_data.get('PRE', {})
                output += f"\nSOL: {sol}\n"
                output += f"  Season: {sol_data.get('season', 'N/A')}\n"
                output += f"  Temp (°C): Min: {at.get('mn')} | Max: {at.get('mx')} | Avg: {at.get('av')}\n"
                output += f"  Wind (m/s): Avg: {hws.get('av')}\n"
                output += f"  Wind Dir: {wd.get('compass_point', 'N/A')}\n"
                output += f"  Pressure (Pa): Avg: {pre.get('av')}\n"

            self.weather_output.setText(output)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch weather data:\n{e}")

    def plot_graphs(self):
        if not hasattr(self, 'weather_data') or 'sol_keys' not in self.weather_data:
            QMessageBox.warning(self, "No Data", "Please fetch data first.")
            return

        sol_keys = self.weather_data['sol_keys']
        sols, temps, pressures, winds = [], [], [], []

        for sol in sorted(sol_keys, key=int):
            sol_data = self.weather_data[sol]
            at = sol_data.get('AT', {})
            pre = sol_data.get('PRE', {})
            hws = sol_data.get('HWS', {})

            if None in (at.get('av'), pre.get('av'), hws.get('av')):
                continue

            sols.append(sol)
            temps.append(at['av'])
            pressures.append(pre['av'])
            winds.append(hws['av'])

        if not sols:
            QMessageBox.warning(self, "No Plots", "Insufficient data.")
            return

        plt.figure(figsize=(12, 6))
        plt.subplot(3, 1, 1)
        plt.plot(sols, temps, marker='o')
        plt.title("Average Temperature (°C)")
        plt.grid(True)

        plt.subplot(3, 1, 2)
        plt.plot(sols, pressures, marker='s', color='orange')
        plt.title("Average Pressure (Pa)")
        plt.grid(True)

        plt.subplot(3, 1, 3)
        plt.plot(sols, winds, marker='^', color='green')
        plt.title("Average Wind Speed (m/s)")
        plt.xlabel("Sol")
        plt.grid(True)

        plt.tight_layout()
        plt.show()
        

class PhotoViewer(QMessageBox):
    def __init__(self, img: Image.Image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View & Save Photo")
        self.setStyleSheet("background-color: #222; color: white;")
        self.setStandardButtons(QMessageBox.Save | QMessageBox.Close)
        
        # Convert PIL Image to QPixmap
        self.full_img = img
        pixmap = pil2pixmap(img)

        label = QLabel()
        label.setPixmap(pixmap.scaledToWidth(800, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.layout().addLayout(layout, 0, 0)

        self.button(QMessageBox.Save).clicked.connect(self.save_image)

    def save_image(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "mars_photo.png", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)")
        if path:
            try:
                self.full_img.save(path)
                QMessageBox.information(self, "Saved", f"Image saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image:\n{e}")

        
        



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MarsWeatherApp()
    window.show()
    sys.exit(app.exec_())
