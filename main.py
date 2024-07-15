import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel, QLineEdit, QComboBox
from PyQt6.QtCore import QTimer
import mysql.connector

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repeater Radio GPS")
        self.setGeometry(100, 100, 600, 300)
        
        self.layout = QVBoxLayout()
        
        # Label nama port
        self.port_name_label = QLabel("Port Name:", self)
        self.layout.addWidget(self.port_name_label)
        self.port_name_input = QLineEdit(self)
        self.layout.addWidget(self.port_name_input)
        
        # Label baud rate
        self.rate_label = QLabel("Baud Rate:", self)
        self.layout.addWidget(self.rate_label)
        self.rate_dropdown = QComboBox(self)
        baud_rates = ["1200", "2400", "4800", "9600", "14400", "19200", "28800", "56000", "57600", "115200"]
        self.rate_dropdown.addItems(baud_rates)
        self.layout.addWidget(self.rate_dropdown)

        # Label speed
        self.speed_label = QLabel("Speed:", self)
        self.layout.addWidget(self.speed_label)
        self.speed_dropdown = QComboBox(self)
        speeds = ["0.1x", "0.2x", "0.5x", "1x", "2x", "3x", "4x"]
        self.speed_dropdown.addItems(speeds)
        self.layout.addWidget(self.speed_dropdown) 

        # Label server URL
        self.server_label = QLabel("Server URL:", self)
        self.layout.addWidget(self.server_label)
        self.server_input = QLineEdit(self)
        self.layout.addWidget(self.server_input)
        
        # Button Start dan Stop
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_loop)
        self.layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_loop)
        self.layout.addWidget(self.stop_button)
                
        self.setLayout(self.layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.submit_data)
        
        # Koneksi MySQL
        self.connection = mysql.connector.connect(
            host='127.0.0.1', 
            user='root', 
            password='Cilacap123', 
            database='radio-gps' 
        )
        self.cursor = self.connection.cursor()
        
        self.data_index = 0
        self.data_list = self.load_data()

    def load_data(self):
        try:
            with open('data.txt', 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "File data (data.txt) tidak ditemukan.")
            return []

    def start_loop(self):
        # Memuat data.txt
        self.data_list = self.load_data()

        # Memeriksa apakah data tersedia
        if not self.data_list:
            QMessageBox.critical(self, "Error", "File data (data.txt) kosong atau tidak ditemukan.")
            return

        # Memeriksa apakah port_name_input, server_input, rate_dropdown, dan speed_dropdown ada di data_list
        port_name = self.port_name_input.text().strip()
        server_url = self.server_input.text().strip()
        baud_rate = self.rate_dropdown.currentText().strip()
        insert_speed = self.speed_dropdown.currentText().strip()
        
        port_name_found = any(port_name in line for line in self.data_list)
        server_url_found = any(server_url in line for line in self.data_list)
        baud_rate_found = any(baud_rate in line for line in self.data_list)
        insert_speed_found = any(insert_speed in line for line in self.data_list)

        if not port_name_found or not server_url_found or not baud_rate_found:
            QMessageBox.critical(self, "Error", "Data tidak ditemukan, mohon periksa kembali data Anda.")
            return

        # Menonaktifkan input teks saat aplikasi sedang berjalan
        self.port_name_input.setEnabled(False)
        self.server_input.setEnabled(False)
        self.rate_dropdown.setEnabled(False)
        self.speed_dropdown.setEnabled(False)

        speed_multiplier = float(insert_speed.replace('x', ''))
        interval = int(1000 / speed_multiplier)
        self.timer.start(interval)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_loop(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Mengaktifkan kembali input teks setelah aplikasi dihentikan
        self.port_name_input.setEnabled(True)
        self.server_input.setEnabled(True)
        self.rate_dropdown.setEnabled(True)
        self.speed_dropdown.setEnabled(True)

    def submit_data(self):
        if self.data_index < len(self.data_list):
            row = self.data_list[self.data_index].strip()
            self.data_index += 1
            columns = row.split(',')
            if len(columns) == 4:
                id_radio, lat, lon, speed = columns
                try:
                    self.cursor.execute(
                        "INSERT INTO positions (id_radio, lat, lon, speed) VALUES (%s, %s, %s, %s)",
                        (id_radio, lat, lon, speed)
                    )
                    self.connection.commit()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Gagal menambahkan data: {e}")
        else:
            self.data_index = 0  # Mengatur ulang data_index ke nol untuk mengulang data dari awal

    def closeEvent(self, event):
        self.cursor.close()
        self.connection.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
