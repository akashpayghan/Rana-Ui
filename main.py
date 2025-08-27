import sys
import time
import webbrowser
import random
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QProgressBar, QLineEdit, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt as QtCore
from PyQt6.QtGui import QColor, QPalette

# Constants for maintainability
COLORS = {
    'gray_950': '#0F172A',
    'gray_900': '#0C121F',
    'gray_700': '#4B5563',
    'gray_600': '#1E293B',
    'gray_500': '#64748B',
    'gray_400': '#94A3B8',
    'gray_200': '#E5E7EB',
    'cyan_500': '#06B6D4',
    'indigo_600': '#4F46E5',
    'indigo_700': '#2338CA',
    'green_500': '#22C55E',
    'green_600': '#10B981',
    'green_700': '#059669',
    'yellow_500': '#F59E0B',
    'yellow_600': '#D97706',
    'red_500': '#EF4444',
    'red_600': '#DC2626',
    'red_400': '#F87171',
    'orange_500': '#F97316',
    'orange_600': '#EA580C',
    'indigo_400': '#818CF8',
    'white': '#FFFFFF',
}

STYLES = {
    'header_frame': f"background-color: {COLORS['gray_900']}; border: 1px solid {COLORS['gray_600']}; border-radius: 10px;",
    'log_frame': f"background-color: {COLORS['gray_900']}; border: 1px solid {COLORS['gray_600']}; border-radius: 10px;",
    'telemetry_frame': f"background-color: {COLORS['gray_900']}; border: 1px solid {COLORS['gray_600']}; border-radius: 10px;",
    'video_frame': f"background-color: {COLORS['gray_950']}; border: 1px solid {COLORS['gray_600']}; border-radius: 15px;",
    'controls_frame': f"background-color: {COLORS['gray_900']}; border: 1px solid {COLORS['gray_600']}; border-radius: 10px;",
    'rpi_frame': f"background-color: {COLORS['gray_900']}; border: 1px solid {COLORS['gray_600']}; border-radius: 10px;",
    'connect_btn': f"""
        QPushButton {{
            background-color: {COLORS['indigo_600']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 10px 20px; 
            border-radius: 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['indigo_700']};
        }}
    """,
    'disconnect_btn': f"""
        QPushButton {{
            background-color: {COLORS['red_500']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 10px 20px; 
            border-radius: 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['red_600']};
        }}
    """,
    'takeoff_btn': f"""
        QPushButton {{
            background-color: {COLORS['green_600']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 12px 24px; 
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['green_700']};
        }}
    """,
    'land_btn': f"""
        QPushButton {{
            background-color: {COLORS['yellow_500']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 12px 24px; 
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['yellow_600']};
        }}
    """,
    'emergency_btn': f"""
        QPushButton {{
            background-color: {COLORS['red_500']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 12px 24px; 
            border-radius: 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['red_600']};
        }}
    """,
    'rpi_connect_btn': f"""
        QPushButton {{
            background-color: {COLORS['orange_500']}; 
            color: {COLORS['white']}; 
            font-weight: bold;
            padding: 10px 20px; 
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['orange_600']};
        }}
    """,
    'battery_bar': f"""
        QProgressBar {{
            height: 15px; 
            border-radius: 7px;
            background-color: {COLORS['gray_700']};
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background-color: {COLORS['green_500']};
            border-radius: 7px;
        }}
    """,
    'signal_bar': f"""
        QProgressBar {{
            height: 15px; 
            border-radius: 7px;
            background-color: {COLORS['gray_700']};
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background-color: {COLORS['indigo_600']};
            border-radius: 7px;
        }}
    """,
}

WINDOW_SIZE = (1200, 800)
MIN_WINDOW_SIZE = (800, 600)
MARGINS = (30, 30, 30, 30)
FONT_SIZES = {
    'logo': 28,
    'title': 18,
    'label': 14,
    'small': 12,
}

class DroneControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RANA")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        self.setPalette(self.get_dark_palette())

        self.is_connected = False
        self.init_ui()

    def get_dark_palette(self):
        """Creates a dark color palette for the application."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(15, 23, 42))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(12, 18, 31))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(12, 18, 31))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(15, 23, 42))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.Text, QColor(226, 232, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(51, 65, 85))
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
        main_layout.setContentsMargins(*MARGINS)

        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setStyleSheet(STYLES['header_frame'])
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # App Logo
        logo_label = QLabel("RANA")
        logo_label.setStyleSheet(f"color: {COLORS['cyan_500']}; font-size: {FONT_SIZES['logo']}px; font-weight: bold; letter-spacing: 2px;")
        header_layout.addWidget(logo_label)
        header_layout.addStretch()

        # Connection Status
        self.status_label = QLabel("STATUS: DISCONNECTED")
        self.status_label.setStyleSheet(f"color: {COLORS['red_400']}; font-size: {FONT_SIZES['label']}px; font-weight: bold;")
        header_layout.addWidget(self.status_label)

        # Connect Button
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setStyleSheet(STYLES['connect_btn'])
        self.connect_btn.clicked.connect(self.connect_drone)
        header_layout.addWidget(self.connect_btn)

        # Disconnect Button
        self.disconnect_btn = QPushButton("DISCONNECT")
        self.disconnect_btn.setStyleSheet(STYLES['disconnect_btn'])
        self.disconnect_btn.clicked.connect(self.disconnect_drone)
        self.disconnect_btn.hide()
        header_layout.addWidget(self.disconnect_btn)

        main_layout.addWidget(header_frame)

        # --- Main Content Section (Horizontal Split) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Side: Log and Telemetry
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setSpacing(20)

        # Flight Log Section
        log_frame = QFrame()
        log_frame.setStyleSheet(STYLES['log_frame'])
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(15, 15, 15, 15)
        log_title = QLabel("FLIGHT LOG")
        log_title.setStyleSheet(f"color: {COLORS['indigo_400']}; font-size: {FONT_SIZES['title']}px; font-weight: bold;")
        log_layout.addWidget(log_title)
        self.log_feed = QTextEdit()
        self.log_feed.setReadOnly(True)
        self.log_feed.setStyleSheet(
            f"background-color: {COLORS['gray_950']}; border: 1px solid {COLORS['gray_600']}; border-radius: 8px; color: {COLORS['gray_400']};")
        self.log_feed.append("Awaiting connection...")
        log_layout.addWidget(self.log_feed)
        left_panel_layout.addWidget(log_frame)

        # Telemetry Section
        telemetry_frame = QFrame()
        telemetry_frame.setStyleSheet(STYLES['telemetry_frame'])
        telemetry_layout = QVBoxLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(15, 15, 15, 15)
        telemetry_title = QLabel("TELEMETRY")
        telemetry_title.setStyleSheet(f"color: {COLORS['cyan_500']}; font-size: {FONT_SIZES['title']}px; font-weight: bold;")
        telemetry_layout.addWidget(telemetry_title)

        # Battery Bar
        battery_label = QLabel("BATTERY")
        battery_label.setStyleSheet(f"color: {COLORS['gray_400']}; font-size: {FONT_SIZES['small']}px;")
        self.battery_bar = QProgressBar()
        self.battery_bar.setValue(75)
        self.battery_bar.setStyleSheet(STYLES['battery_bar'])
        telemetry_layout.addWidget(battery_label)
        telemetry_layout.addWidget(self.battery_bar)

        # Signal Bar
        signal_label = QLabel("SIGNAL")
        signal_label.setStyleSheet(f"color: {COLORS['gray_400']}; font-size: {FONT_SIZES['small']}px;")
        self.signal_bar = QProgressBar()
        self.signal_bar.setValue(90)
        self.signal_bar.setStyleSheet(STYLES['signal_bar'])
        telemetry_layout.addWidget(signal_label)
        telemetry_layout.addWidget(self.signal_bar)

        left_panel_layout.addWidget(telemetry_frame)
        content_layout.addLayout(left_panel_layout, 1)

        # Right Side: Video Feed and Controls
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setSpacing(20)

        # Video Feed Section
        video_frame = QFrame()
        video_frame.setFrameShape(QFrame.Shape.StyledPanel)
        video_frame.setFrameShadow(QFrame.Shadow.Raised)
        video_frame.setStyleSheet(STYLES['video_frame'])
        video_layout = QVBoxLayout(video_frame)
        video_label = QLabel("LIVE VIDEO FEED (Placeholder)")
        video_label.setAlignment(QtCore.AlignmentFlag.AlignCenter)
        video_label.setStyleSheet(f"color: {COLORS['gray_500']}; font-size: {FONT_SIZES['title']}px; font-weight: bold;")
        video_layout.addWidget(video_label)
        right_panel_layout.addWidget(video_frame, 3)

        # Controls Section
        controls_frame = QFrame()
        controls_frame.setStyleSheet(STYLES['controls_frame'])
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(20)

        # Takeoff/Land Buttons
        self.takeoff_btn = QPushButton("TAKEOFF")
        self.takeoff_btn.setStyleSheet(STYLES['takeoff_btn'])
        self.takeoff_btn.setEnabled(False)
        self.takeoff_btn.setToolTip("Connect to the drone to enable takeoff.")
        self.takeoff_btn.setShortcut("Ctrl+T")
        self.takeoff_btn.clicked.connect(self.log_takeoff)
        controls_layout.addWidget(self.takeoff_btn)

        self.land_btn = QPushButton("LAND")
        self.land_btn.setStyleSheet(STYLES['land_btn'])
        self.land_btn.setEnabled(False)
        self.land_btn.setToolTip("Connect to the drone to enable landing.")
        self.land_btn.setShortcut("Ctrl+L")
        self.land_btn.clicked.connect(self.log_land)
        controls_layout.addWidget(self.land_btn)

        # Emergency Land Button
        self.emergency_btn = QPushButton("EMERGENCY LAND")
        self.emergency_btn.setStyleSheet(STYLES['emergency_btn'])
        self.emergency_btn.setToolTip("Initiate emergency landing.")
        self.emergency_btn.setShortcut("Ctrl+E")
        self.emergency_btn.clicked.connect(self.log_emergency_land)
        controls_layout.addWidget(self.emergency_btn)

        right_panel_layout.addWidget(controls_frame)

        # Raspberry Pi Connect Section
        rpi_frame = QFrame()
        rpi_frame.setStyleSheet(STYLES['rpi_frame'])
        rpi_layout = QGridLayout(rpi_frame)
        rpi_layout.setContentsMargins(15, 15, 15, 15)
        rpi_title = QLabel("RASPBERRY PI CONNECT")
        rpi_title.setStyleSheet(f"color: {COLORS['orange_500']}; font-size: {FONT_SIZES['title']}px; font-weight: bold;")
        rpi_layout.addWidget(rpi_title, 0, 0, 1, 2)

        rpi_link_label = QLabel("Link Code:")
        rpi_link_label.setStyleSheet(f"color: {COLORS['gray_400']};")
        self.rpi_link_input = QLineEdit()
        self.rpi_link_input.setPlaceholderText("e.g., a-b-c-d")
        self.rpi_link_input.setStyleSheet(
            f"background-color: #1F2937; border: 1px solid {COLORS['gray_700']}; border-radius: 5px; padding: 5px; color: {COLORS['gray_200']};")
        rpi_layout.addWidget(rpi_link_label, 1, 0)
        rpi_layout.addWidget(self.rpi_link_input, 1, 1)

        self.rpi_connect_btn = QPushButton("Connect to Pi")
        self.rpi_connect_btn.setStyleSheet(STYLES['rpi_connect_btn'])
        self.rpi_connect_btn.clicked.connect(self.connect_to_pi)
        rpi_layout.addWidget(self.rpi_connect_btn, 2, 0, 1, 2)

        right_panel_layout.addWidget(rpi_frame)
        content_layout.addLayout(right_panel_layout, 2)
        main_layout.addLayout(content_layout)

    def log_message(self, message, color=""):
        """Appends a message to the log with optional color formatting, limiting log size."""
        time_str = time.strftime("[%H:%M:%S]")
        colored_message = f"<span style='color: {COLORS['gray_500']};'>{time_str}</span> <span style='color: {color};'>{message}</span>"
        self.log_feed.append(colored_message)
        # Limit to 100 lines
        if self.log_feed.toPlainText().count('\n') > 100:
            cursor = self.log_feed.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()

    def connect_drone(self):
        """Simulates the drone connection process."""
        self.log_message("Attempting connection...", COLORS['yellow_500'])
        self.status_label.setText("STATUS: CONNECTING...")
        self.status_label.setStyleSheet(f"color: {COLORS['yellow_500']}; font-size: {FONT_SIZES['label']}px; font-weight: bold;")
        self.connect_btn.setEnabled(False)
        QTimer.singleShot(2000, self.finish_connection)

    def finish_connection(self):
        """Finalizes the connection after a delay."""
        self.is_connected = True
        self.log_message("CONNECTION SUCCESSFUL!", COLORS['green_500'])
        self.status_label.setText("STATUS: CONNECTED")
        self.status_label.setStyleSheet(f"color: {COLORS['green_500']}; font-size: {FONT_SIZES['label']}px; font-weight: bold;")
        self.connect_btn.hide()
        self.disconnect_btn.show()
        self.takeoff_btn.setEnabled(True)
        self.land_btn.setEnabled(True)
        # Start telemetry updates
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1000)

    def disconnect_drone(self):
        """Disconnects the drone and resets the UI."""
        self.is_connected = False
        self.log_message("Drone disconnected.", COLORS['red_400'])
        self.status_label.setText("STATUS: DISCONNECTED")
        self.status_label.setStyleSheet(f"color: {COLORS['red_400']}; font-size: {FONT_SIZES['label']}px; font-weight: bold;")
        self.connect_btn.show()
        self.disconnect_btn.hide()
        self.takeoff_btn.setEnabled(False)
        self.land_btn.setEnabled(False)
        if hasattr(self, 'telemetry_timer'):
            self.telemetry_timer.stop()

    def update_telemetry(self):
        """Simulates dynamic telemetry updates."""
        self.battery_bar.setValue(random.randint(50, 100))
        self.signal_bar.setValue(random.randint(70, 100))

    def log_takeoff(self):
        self.log_message("DRONE TAKING OFF.", COLORS['green_600'])

    def log_land(self):
        self.log_message("INITIATING LANDING SEQUENCE.", COLORS['yellow_500'])

    def log_emergency_land(self):
        self.log_message("EMERGENCY LANDING INITIATED!", COLORS['red_500'])

    def connect_to_pi(self):
        """Opens the Raspberry Pi Connect remote shell in a web browser."""
        link_code = self.rpi_link_input.text().strip()
        if not link_code or not re.match(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+$', link_code):
            self.log_message("Invalid link code format. Use format like 'a-b-c-d'.", COLORS['red_500'])
            return
        connect_url = f"https://connect.raspberrypi.com/shell/{link_code}"
        self.log_message(f"Opening Raspberry Pi Connect for code '{link_code}'...", COLORS['orange_500'])
        try:
            webbrowser.open(connect_url)
        except Exception as e:
            self.log_message(f"Failed to open browser: {str(e)}", COLORS['red_500'])

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = DroneControlApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to initialize application: {str(e)}")
        sys.exit(1)