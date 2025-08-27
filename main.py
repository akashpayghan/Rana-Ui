import sys
import time
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QProgressBar, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

# ⭐ NEW: Import mavutil for pymavlink
from pymavlink import mavutil


# ---------------------------------------------------------------------
# ⭐ NEW: A dedicated class to handle the MAVLink connection in a separate thread.
# This prevents the UI from freezing during the connection process.
class MAVLinkConnector(QObject):
    # Signals to communicate results back to the main UI thread
    connection_successful = pyqtSignal(object)  # The object is the MAVLink connection
    connection_failed = pyqtSignal(str)  # The string is an error message

    def __init__(self, connection_string, parent=None):
        super().__init__(parent)
        self.connection_string = connection_string
        self.master = None

    def connect_blocking(self):
        """Attempts to establish a MAVLink connection."""
        try:
            self.master = mavutil.auto_connect(self.connection_string, baud=57600)

            # Wait for a HEARTBEAT message to confirm a valid connection
            self.master.wait_heartbeat(timeout=5)

            if not self.master.target_system:
                self.master.close()
                self.connection_failed.emit("Connected but failed to receive a valid heartbeat from the drone.")
                return

            self.connection_successful.emit(self.master)

        except Exception as e:
            error_message = f"Connection failed: {e}"
            self.connection_failed.emit(error_message)


# ---------------------------------------------------------------------

class DroneControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PARASHARS")
        self.setGeometry(100, 100, 1200, 800)
        self.setPalette(self.get_dark_palette())

        # ⭐ MODIFIED: We will use a MAVLink master object and a thread
        self.is_connected = False
        self.master = None
        self.connection_thread = None
        self.connector = None

        self.init_ui()

    def get_dark_palette(self):
        """Creates a dark color palette for the application."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(15, 23, 42))  # Gray-950
        palette.setColor(QPalette.ColorRole.WindowText, QColor(226, 232, 240))  # Slate-200
        palette.setColor(QPalette.ColorRole.Base, QColor(12, 18, 31))  # Darker background
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(12, 18, 31))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(15, 23, 42))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.Text, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(51, 65, 85))  # Gray-700
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        return palette

    def init_ui(self):
        """Initializes the main application layout and widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #0C121F; border: 1px solid #1E293B; border-radius: 10px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # App Logo (Placeholder Label)
        logo_label = QLabel("PARASHAR")
        logo_label.setStyleSheet("color: #06B6D4; font-size: 28px; font-weight: bold; letter-spacing: 2px;")
        header_layout.addWidget(logo_label)
        header_layout.addStretch()

        # Connection Status
        self.status_label = QLabel("STATUS: DISCONNECTED")
        self.status_label.setStyleSheet("color: #F87171; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.status_label)

        # Connect Button
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5; 
                color: white; 
                font-weight: bold;
                padding: 10px 20px; 
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #2338CA;
            }
        """)
        # ⭐ MODIFIED: This button will now try to connect to the drone's MAVLink system
        self.connect_btn.clicked.connect(self.connect_drone)
        header_layout.addWidget(self.connect_btn)

        main_layout.addWidget(header_frame)

        # --- Main Content Section (Horizontal Split) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Side: Log and Telemetry
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setSpacing(20)

        # Flight Log Section
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: #0C121F; border: 1px solid #1E293B; border-radius: 10px;")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(15, 15, 15, 15)
        log_title = QLabel("FLIGHT LOG")
        log_title.setStyleSheet("color: #818CF8; font-size: 18px; font-weight: bold;")
        log_layout.addWidget(log_title)
        self.log_feed = QTextEdit()
        self.log_feed.setReadOnly(True)
        self.log_feed.setStyleSheet(
            "background-color: #0F172A; border: 1px solid #1E293B; border-radius: 8px; color: #94A3B8;")
        self.log_feed.append("Awaiting connection...")
        log_layout.addWidget(self.log_feed)
        left_panel_layout.addWidget(log_frame)

        # Telemetry Section
        telemetry_frame = QFrame()
        telemetry_frame.setStyleSheet("background-color: #0C121F; border: 1px solid #1E293B; border-radius: 10px;")
        telemetry_layout = QVBoxLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(15, 15, 15, 15)
        telemetry_title = QLabel("TELEMETRY")
        telemetry_title.setStyleSheet("color: #06B6D4; font-size: 18px; font-weight: bold;")
        telemetry_layout.addWidget(telemetry_title)

        # Battery Bar
        battery_label = QLabel("BATTERY")
        battery_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.battery_bar = QProgressBar()
        self.battery_bar.setValue(75)
        self.battery_bar.setStyleSheet("""
            QProgressBar {
                height: 15px; 
                border-radius: 7px;
                background-color: #4B5563;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #22C55E;
                border-radius: 7px;
            }
        """)
        telemetry_layout.addWidget(battery_label)
        telemetry_layout.addWidget(self.battery_bar)

        # Signal Bar
        signal_label = QLabel("SIGNAL")
        signal_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.signal_bar = QProgressBar()
        self.signal_bar.setValue(90)
        self.signal_bar.setStyleSheet("""
            QProgressBar {
                height: 15px; 
                border-radius: 7px;
                background-color: #4B5563;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #4F46E5;
                border-radius: 7px;
            }
        """)
        telemetry_layout.addWidget(signal_label)
        telemetry_layout.addWidget(self.signal_bar)

        left_panel_layout.addWidget(telemetry_frame)
        content_layout.addLayout(left_panel_layout, 1)  # Set stretch factor

        # Right Side: Video Feed and Controls
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setSpacing(20)

        # Video Feed Section
        video_frame = QFrame()
        video_frame.setFrameShape(QFrame.Shape.StyledPanel)
        video_frame.setFrameShadow(QFrame.Shadow.Raised)
        video_frame.setStyleSheet("background-color: #0F172A; border: 1px solid #1E293B; border-radius: 15px;")
        video_layout = QVBoxLayout(video_frame)
        video_label = QLabel("LIVE VIDEO FEED")
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setStyleSheet("color: #64748B; font-size: 24px; font-weight: bold;")
        video_layout.addWidget(video_label)
        right_panel_layout.addWidget(video_frame, 3)  # Set stretch factor

        # Controls Section
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: #0C121F; border: 1px solid #1E293B; border-radius: 10px;")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(20)

        # Takeoff/Land Buttons
        self.takeoff_btn = QPushButton("TAKEOFF")
        self.takeoff_btn.setStyleSheet(
            "QPushButton {background-color: #10B981; color: white; padding: 12px 24px; font-weight: bold; border-radius: 10px;} QPushButton:hover {background-color: #059669;}")
        self.takeoff_btn.setEnabled(False)
        self.takeoff_btn.clicked.connect(self.log_takeoff)
        controls_layout.addWidget(self.takeoff_btn)

        self.land_btn = QPushButton("LAND")
        self.land_btn.setStyleSheet(
            "QPushButton {background-color: #F59E0B; color: white; padding: 12px 24px; font-weight: bold; border-radius: 10px;} QPushButton:hover {background-color: #D97706;}")
        self.land_btn.setEnabled(False)
        self.land_btn.clicked.connect(self.log_land)
        controls_layout.addWidget(self.land_btn)

        # Emergency Land Button
        self.emergency_btn = QPushButton("EMERGENCY LAND")
        self.emergency_btn.setStyleSheet(
            "QPushButton {background-color: #EF4444; color: white; padding: 12px 24px; font-weight: bold; border-radius: 20px;} QPushButton:hover {background-color: #DC2626;}")
        self.emergency_btn.clicked.connect(self.log_emergency_land)
        controls_layout.addWidget(self.emergency_btn)

        right_panel_layout.addWidget(controls_frame)

        # --- Raspberry Pi Connection Section ---
        rpi_frame = QFrame()
        rpi_frame.setStyleSheet("background-color: #0C121F; border: 1px solid #1E293B; border-radius: 10px;")
        rpi_layout = QGridLayout(rpi_frame)
        rpi_layout.setContentsMargins(15, 15, 15, 15)
        rpi_title = QLabel("RASPBERRY PI CONNECT")
        rpi_title.setStyleSheet("color: #F97316; font-size: 18px; font-weight: bold;")
        rpi_layout.addWidget(rpi_title, 0, 0, 1, 2)

        # Input field for the connection string
        rpi_link_label = QLabel("Connection String:")
        rpi_link_label.setStyleSheet("color: #94A3B8;")
        self.rpi_link_input = QLineEdit()
        # ⭐ MODIFIED: Placeholder text now guides the user for MAVLink connections
        self.rpi_link_input.setPlaceholderText("e.g., tcp:192.168.1.100:5760")
        self.rpi_link_input.setStyleSheet(
            "background-color: #1F2937; border: 1px solid #4B5563; border-radius: 5px; padding: 5px; color: #E5E7EB;")

        rpi_layout.addWidget(rpi_link_label, 1, 0)
        rpi_layout.addWidget(self.rpi_link_input, 1, 1)

        # Button to connect to the drone
        self.rpi_connect_btn = QPushButton("Connect to Drone")
        self.rpi_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #F97316; 
                color: white; 
                font-weight: bold;
                padding: 10px 20px; 
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #EA580C;
            }
        """)
        # ⭐ MODIFIED: This button will now call the new connection method
        self.rpi_connect_btn.clicked.connect(self.start_mavlink_connection)
        rpi_layout.addWidget(self.rpi_connect_btn, 2, 0, 1, 2)

        right_panel_layout.addWidget(rpi_frame)

        content_layout.addLayout(right_panel_layout, 2)
        main_layout.addLayout(content_layout)

    def log_message(self, message, color=""):
        """Appends a message to the log with optional color formatting."""
        time_str = time.strftime("[%H:%M:%S]")
        colored_message = f"<span style='color: #64748B;'>{time_str}</span> <span style='color: {color};'>{message}</span>"
        self.log_feed.append(colored_message)

    # ⭐ NEW: Method to initiate the MAVLink connection
    def start_mavlink_connection(self):
        connection_string = self.rpi_link_input.text().strip()

        if not connection_string:
            self.log_message("Please enter a connection string.", "#EF4444")
            return

        self.log_message(f"Attempting MAVLink connection to: {connection_string}...", "#F97316")
        self.rpi_connect_btn.setEnabled(False)
        self.rpi_link_input.setEnabled(False)

        # Create a new thread and the worker object
        self.connection_thread = QThread()
        self.connector = MAVLinkConnector(connection_string)
        self.connector.moveToThread(self.connection_thread)

        # Connect signals and slots
        self.connection_thread.started.connect(self.connector.connect_blocking)
        self.connector.connection_successful.connect(self.handle_connection_success)
        self.connector.connection_failed.connect(self.handle_connection_failure)

        # Clean up when the thread finishes
        self.connection_thread.finished.connect(self.connection_thread.deleteLater)
        self.connector.connection_successful.connect(self.connection_thread.quit)
        self.connector.connection_failed.connect(self.connection_thread.quit)

        # Start the thread
        self.connection_thread.start()

    # ⭐ NEW: Slot to handle a successful connection
    def handle_connection_success(self, master_conn):
        self.master = master_conn
        self.is_connected = True
        self.log_message("MAVLink Connection SUCCESSFUL!", "#22C55E")
        self.status_label.setText("STATUS: DRONE CONNECTED")
        self.status_label.setStyleSheet("color: #22C55E; font-size: 14px; font-weight: bold;")
        self.rpi_connect_btn.setText("DISCONNECT")
        self.rpi_connect_btn.setEnabled(True)
        self.rpi_link_input.setEnabled(True)
        self.takeoff_btn.setEnabled(True)
        self.land_btn.setEnabled(True)

    # ⭐ NEW: Slot to handle a failed connection
    def handle_connection_failure(self, error_message):
        self.log_message(f"Connection FAILED: {error_message}", "#EF4444")
        self.rpi_connect_btn.setEnabled(True)
        self.rpi_link_input.setEnabled(True)

    def connect_drone(self):
        """Simulates the drone connection process."""
        self.log_message("Attempting connection...", "#F59E0B")
        self.status_label.setText("STATUS: CONNECTING...")
        self.status_label.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: bold;")
        self.connect_btn.setEnabled(False)

        # Use a QTimer to simulate the delay without blocking the UI
        QTimer.singleShot(2000, self.finish_connection)

    def finish_connection(self):
        """Finalizes the connection after a delay."""
        self.is_connected = True
        self.log_message("CONNECTION SUCCESSFUL!", "#22C55E")
        self.status_label.setText("STATUS: CONNECTED")
        self.status_label.setStyleSheet("color: #22C55E; font-size: 14px; font-weight: bold;")
        self.connect_btn.hide()
        self.takeoff_btn.setEnabled(True)
        self.land_btn.setEnabled(True)

    def log_takeoff(self):
        self.log_message("DRONE TAKING OFF.", "#10B981")

    def log_land(self):
        self.log_message("INITIATING LANDING SEQUENCE.", "#F59E0B")

    def log_emergency_land(self):
        self.log_message("EMERGENCY LANDING INITIATED!", "#EF4444")

    # ⭐ REMOVED: The original connect_to_pi method that used webbrowser is no longer needed.


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DroneControlApp()
    window.show()
    sys.exit(app.exec())