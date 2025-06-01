import sys
import json
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QFrame, QLineEdit, QDialog, QComboBox
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPainterPath, QIcon
from PyQt6.QtCore import Qt, QTimer

DATA_FILE = "user_data.json"
BALANCE_FILE = "balances.json"
DEFAULT_APP_ICON = "app_icon.png"
DEFAULT_AVATAR = "ava.png"

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if not data.get("avatar_path"):
                data["avatar_path"] = DEFAULT_AVATAR
            return data
    return {"name": "User", "handle": "@User", "avatar_path": DEFAULT_AVATAR, "app_icon_path": DEFAULT_APP_ICON}

def save_user_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_balances():
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, "r") as f:
                data = json.load(f)
                return {k: float(v) for k, v in data.items()}
        except Exception:
            pass
    return {
        'Bitcoin': 0,
        'Ethereum': 0,
        'USDT': 0,
        'Solana': 0
    }

def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4)

def make_round_pixmap(pixmap, size):
    pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    rounded = QPixmap(size, size)
    rounded.fill(Qt.GlobalColor.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return rounded

class SettingsWindow(QDialog):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(350, 320)
        self.setStyleSheet("""
            background-color: #1a1a1a;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        """)
        self.user_data = user_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Account Name:"))
        self.name_input = QLineEdit(self.user_data["name"])
        self.name_input.setStyleSheet("""
            background-color: #2a2a2a;
            border: none;
            border-radius: 8px;
            padding: 8px;
            color: white;
            font-size: 16px;
        """)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Your ID:"))
        self.handle_input = QLineEdit(self.user_data["handle"])
        self.handle_input.setStyleSheet("""
            background-color: #2a2a2a;
            border: none;
            border-radius: 8px;
            padding: 8px;
            color: white;
            font-size: 16px;
        """)
        layout.addWidget(self.handle_input)

        layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
        """)
        layout.addWidget(self.save_btn)

        self.save_btn.clicked.connect(self.save_and_close)

    def save_and_close(self):
        self.user_data["name"] = self.name_input.text()
        self.user_data["handle"] = self.handle_input.text()
        save_user_data(self.user_data)
        self.accept()

class OperationDialog(QDialog):
    def __init__(self, parent, title, balances, require_address=False, is_swap=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(350, 400)
        self.balances = balances
        self.require_address = require_address
        self.is_swap = is_swap
        self.result = None

        self.setStyleSheet("""
            background-color: #1a1a1a;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        if require_address:
            layout.addWidget(QLabel("Address:"))
            self.address_input = QLineEdit()
            self.address_input.setStyleSheet("""
                background-color: #2a2a2a;
                border: none;
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 16px;
            """)
            layout.addWidget(self.address_input)

        if is_swap:
            layout.addWidget(QLabel("From Currency:"))
            self.from_currency_cb = QComboBox()
            self.from_currency_cb.addItems(balances.keys())
            layout.addWidget(self.from_currency_cb)

            layout.addWidget(QLabel("To Currency:"))
            self.to_currency_cb = QComboBox()
            self.to_currency_cb.addItems(balances.keys())
            layout.addWidget(self.to_currency_cb)
        else:
            layout.addWidget(QLabel("Currency:"))
            self.currency_cb = QComboBox()
            self.currency_cb.addItems(balances.keys())
            layout.addWidget(self.currency_cb)

        layout.addWidget(QLabel("Amount:"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.0")
        self.amount_input.setStyleSheet("""
            background-color: #2a2a2a;
            border: none;
            border-radius: 8px;
            padding: 8px;
            color: white;
            font-size: 16px;
        """)
        layout.addWidget(self.amount_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
        """)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
        """)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.on_ok)
        self.cancel_btn.clicked.connect(self.reject)

    def on_ok(self):
        try:
            amount = float(self.amount_input.text())
            if amount <= 0:
                self.error_label.setText("Amount must be positive")
                return
        except ValueError:
            self.error_label.setText("Invalid amount")
            return

        if self.is_swap:
            from_currency = self.from_currency_cb.currentText()
            to_currency = self.to_currency_cb.currentText()
            if from_currency == to_currency:
                self.error_label.setText("Choose different currencies")
                return
            if amount > self.balances.get(from_currency, 0):
                self.error_label.setText(f"Not enough {from_currency}")
                return
            self.result = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount
            }
        else:
            currency = self.currency_cb.currentText()
            if self.require_address:
                address = self.address_input.text().strip()
                if not address:
                    self.error_label.setText("Address cannot be empty")
                    return
                if self.windowTitle() == "Send Crypto":
                    if amount > self.balances.get(currency, 0):
                        self.error_label.setText(f"Not enough {currency}")
                        return
                self.result = {
                    "address": address,
                    "currency": currency,
                    "amount": amount
                }
            else:
                self.result = {
                    "currency": currency,
                    "amount": amount
                }

        self.accept()

class FakeWallet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shade")
        self.setFixedSize(375, 600)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        self.user_data = load_user_data()
        self.balances = load_balances()

        if os.path.exists(DEFAULT_APP_ICON):
            self.setWindowIcon(QIcon(DEFAULT_APP_ICON))

        self.usd_prices = {
            'Bitcoin': 103996,
            'Ethereum': 2485,
            'USDT': 1,
            'Solana': 152
        }

        self.init_ui()
        self.start_timer()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()

        self.avatar = QLabel()
        self.avatar.setFixedSize(72, 72)
        self.update_avatar()

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        self.handle_label = QLabel(self.user_data["handle"])
        self.handle_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.handle_label.setStyleSheet("color: #888888;")

        self.name_label = QLabel(self.user_data["name"])
        self.name_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        name_layout.addWidget(self.handle_label)
        name_layout.addWidget(self.name_label)

        settings = QPushButton("\u22ee")
        settings.setFixedSize(60, 60)
        settings.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 40px;
                color: #888888;
                font-weight: bold;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #cccccc;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        settings.clicked.connect(self.open_settings)

        top_bar.addWidget(self.avatar)
        top_bar.addLayout(name_layout)
        top_bar.addStretch()
        top_bar.addWidget(settings)

        layout.addLayout(top_bar)

        self.balance_label = QLabel()
        font = QFont("Segoe UI", 42, QFont.Weight.Bold)
        self.balance_label.setFont(font)
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_label.setStyleSheet("font-weight: bold;")
        self.update_total_balance()

        layout.addWidget(self.balance_label)

        self.delta_label = QLabel()
        self.delta_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.delta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delta_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.delta_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.buttons = {}

        for text in ["Receive", "Send", "Swap", "Buy"]:
            btn = QPushButton(text)
            btn.setFixedSize(80, 80)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: white;
                    border-radius: 12px;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
            """)
            btn_row.addWidget(btn)
            self.buttons[text] = btn

        layout.addLayout(btn_row)

        self.crypto_labels = {}
        crypto_col = QVBoxLayout()
        crypto_col.setSpacing(10)

        icon_files = {
            'Bitcoin': 'bitcoin.png',
            'Ethereum': 'ethereum.png',
            'USDT': 'usdt.png',
            'Solana': 'solana.png'
        }

        for coin in self.balances:
            frame = QFrame()
            frame.setStyleSheet("background-color: #2a2a2a; border-radius: 10px;")
            frame.setFixedHeight(70)
            row = QHBoxLayout()
            row.setContentsMargins(10, 5, 10, 5)

            icon_label = QLabel()
            icon_path = icon_files.get(coin, None)
            size_icon = 32
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                rounded_pixmap = make_round_pixmap(pixmap, size_icon)
                icon_label.setPixmap(rounded_pixmap)
            else:
                icon_pixmap = QPixmap(size_icon, size_icon)
                icon_pixmap.fill(Qt.GlobalColor.darkGray)
                icon_label.setPixmap(icon_pixmap)

            icon_label.setFixedSize(size_icon, size_icon)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)

            coin_label = QLabel(coin)
            coin_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

            amount_label = QLabel(f"{self.balances[coin]:.4f}")
            amount_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

            text_layout.addWidget(coin_label)
            text_layout.addWidget(amount_label)

            price = self.usd_prices[coin]
            usd_value = self.balances[coin] * price

            price_label = QLabel(f"${price:,.2f}")
            price_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            price_label.setStyleSheet("color: #aaaaaa;")

            usd_label = QLabel(f"${usd_value:,.2f}")
            usd_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            usd_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            value_layout = QVBoxLayout()
            value_layout.addWidget(price_label)
            value_layout.addWidget(usd_label)

            row.addWidget(icon_label)
            row.addLayout(text_layout)
            row.addStretch()
            row.addLayout(value_layout)

            frame.setLayout(row)
            crypto_col.addWidget(frame)
            self.crypto_labels[coin] = amount_label

        layout.addLayout(crypto_col)

        self.update_delta_label()

        self.buttons["Receive"].clicked.connect(self.receive_crypto)
        self.buttons["Send"].clicked.connect(self.send_crypto)
        self.buttons["Buy"].clicked.connect(self.buy_crypto)
        self.buttons["Swap"].clicked.connect(self.swap_crypto)

    def update_avatar(self):
        size = 72
        avatar_path = self.user_data.get("avatar_path", DEFAULT_AVATAR)
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
        else:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.darkGray)

        rounded_pixmap = make_round_pixmap(pixmap, size)
        self.avatar.setPixmap(rounded_pixmap)

    def update_total_balance(self):
        total = 0
        for coin, amount in self.balances.items():
            total += amount * self.usd_prices[coin]
        self.balance_label.setText(f"${total:,.2f}")

    def update_delta_label(self):
        delta_value = random.uniform(20, 60)
        delta_percent = random.uniform(-5, 5)
        sign = "+" if delta_value >= 0 else "-"
        sign_percent = "+" if delta_percent >= 0 else "-"
        self.delta_label.setText(
            f"{sign}${delta_value:.2f} ({sign_percent}{abs(delta_percent):.2f}%)"
        )

    def refresh_ui(self):
        for coin, label in self.crypto_labels.items():
            label.setText(f"{self.balances[coin]:.4f}")
        self.update_total_balance()
        self.update_delta_label()

    def open_settings(self):
        settings = SettingsWindow(self, self.user_data)
        if settings.exec():
            self.name_label.setText(self.user_data["name"])
            self.handle_label.setText(self.user_data["handle"])
            save_user_data(self.user_data)

    def receive_crypto(self):
        dialog = OperationDialog(self, "Receive Crypto", self.balances, require_address=True)
        if dialog.exec():
            res = dialog.result
            currency = res["currency"]
            amount = res["amount"]
            self.balances[currency] += amount
            save_balances(self.balances)
            self.refresh_ui()

    def send_crypto(self):
        dialog = OperationDialog(self, "Send Crypto", self.balances, require_address=True)
        if dialog.exec():
            res = dialog.result
            currency = res["currency"]
            amount = res["amount"]
            if amount <= self.balances.get(currency, 0):
                self.balances[currency] -= amount
                save_balances(self.balances)
                self.refresh_ui()

    def buy_crypto(self):
        dialog = OperationDialog(self, "Buy Crypto", self.balances, require_address=False)
        if dialog.exec():
            res = dialog.result
            currency = res["currency"]
            amount = res["amount"]
            self.balances[currency] += amount
            save_balances(self.balances)
            self.refresh_ui()

    def swap_crypto(self):
        dialog = OperationDialog(self, "Swap Crypto", self.balances, is_swap=True)
        if dialog.exec():
            res = dialog.result
            from_currency = res["from_currency"]
            to_currency = res["to_currency"]
            amount = res["amount"]
            if amount <= self.balances.get(from_currency, 0):
                self.balances[from_currency] -= amount
                self.balances[to_currency] += amount
                save_balances(self.balances)
                self.refresh_ui()

    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_delta_label)
        self.timer.start(5000)

def main():
    app = QApplication(sys.argv)
    wallet = FakeWallet()
    wallet.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
