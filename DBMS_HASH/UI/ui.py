import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QToolBar, QAction, QFileDialog, QMessageBox, QMenu, QInputDialog,
    QDialog, QLineEdit, QFormLayout, QShortcut, QTabWidget, QFrame, QStatusBar, QDockWidget,
    QLineEdit
)
from PyQt5.QtCore import Qt, QSize, QRegExp
from PyQt5.QtGui import QIcon, QFont, QColor, QSyntaxHighlighter, QTextCharFormat
import qtawesome as qta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.dbms import DBMS
from Backend.query_processor import query_processor, process_query
from Backend.transaction import TransactionManager

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setWindowIcon(qta.icon('fa5s.lock'))
        self.setFixedSize(300, 200)
        
        # Hardcoded credentials
        self.correct_username = "admin"
        self.correct_password = "87654321"
        
        # Apply teal and black color scheme
        self.setStyleSheet("""
            QDialog {
                background-color: #2E2E2E;  /* Dark background */
            }
            QLabel {
                color: #26A69A;  /* Teal color for labels */
            }
            QLineEdit {
                background-color: #424242;  /* Dark gray background */
                color: white;  /* White text */
                border: 1px solid #26A69A;  /* Teal border */
            }
            QPushButton {
                background-color: #26A69A;  /* Teal button */
                color: white;  /* White text */
            }
            QPushButton:hover {
                background-color: #00897B;  /* Darker teal on hover */
            }
        """)
        
        layout = QVBoxLayout()
        
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.login_button = QPushButton("Login")
        self.login_button.setIcon(qta.icon('fa5s.sign-in-alt'))
        self.login_button.clicked.connect(self.authenticate)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #EF5350;")  
        
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def authenticate(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if username == self.correct_username and password == self.correct_password:
            self.accept()  # This will close the dialog and return QDialog.Accepted
        else:
            self.status_label.setText("Invalid username or password")


class SQLHighlighter(QSyntaxHighlighter):
    """Basic SQL syntax highlighter for query editor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#26A69A"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'INTO', 'VALUES','COMMIT','ROLLBACK','BEGIN','USE','SHOW']
        for word in keywords:
            pattern = QRegExp(f"\\b{word}\\b", Qt.CaseInsensitive)
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#FFCA28"))
        self.highlighting_rules.append((QRegExp("'[^']*'"), string_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#F06292"))
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class ModernFrame(QFrame):
    """Custom styled frame for a modern look."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ModernFrame {
                background-color: #2E2E2E;
                border-radius: 8px;
                border: 1px solid #CFD8DC;
            }
        """)

class DatabaseGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hash DBMS")
        self.setGeometry(100, 100, 1280, 800)
        self.query_history = []

        self.dbms = DBMS()
        self.transaction_manager = TransactionManager(self.dbms.root_path)
        self.current_open_collection = None

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self._create_toolbar()
        self._create_main_layout()
        self._create_query_history_dock()
        self._populate_database_tree()
        self.db_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.db_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.create_welcome_tab()
        self._apply_theme()

    def _apply_theme(self):
        """Apply modern light theme."""
        stylesheet = """
            QMainWindow {
                background-color: #FAFAFA;
                color: #263238;
            }
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ECEFF1, stop:1 #CFD8DC);
                spacing: 5px;
                border: none;
                padding: 5px;
            }
            QToolBar QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QTableWidget, QTextEdit {
                background-color: #FFFFFF;
                color: #263238;
                alternate-background-color: #F5F5F5;
                gridline-color: #CFD8DC;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                font-size: 12px;
                font-family: 'Consolas';
            }
            QTableWidget::item:selected, QTextEdit::selection {
                background-color: #26A69A;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #ECEFF1;
                color: #455A64;
                padding: 8px;
                border: 1px solid #CFD8DC;
            }
            QTreeWidget {
                background-color: #FFFFFF;
                color: #263238;
                border-radius: 6px;
                border: 1px solid #CFD8DC;
                alternate-background-color: #F5F5F5;
                font-size: 12px;
            }
            QTreeWidget::item:selected {
                background-color: #26A69A;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #CFD8DC;
                background-color: #FFFFFF;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #ECEFF1;
                color: #455A64;
                border: 1px solid #CFD8DC;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #26A69A;
                color: #ffffff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #CFD8DC;
            }
            QTextEdit {
                selection-background-color: #26A69A;
            }
            QPushButton {
                background-color: #26A69A;
                color: #ffffff;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #00897B;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #263238;
                border-radius: 4px;
                border: 1px solid #CFD8DC;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #26A69A;
            }
            QLabel {
                color: #455A64;
                font-size: 14px;
            }
            QDockWidget {
                background-color: #FFFFFF;
                color: #263238;
                border: 1px solid #CFD8DC;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #263238;
                border: 1px solid #CFD8DC;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #26A69A;
                color: #ffffff;
            }
            QDialog {
                background-color: #FAFAFA;
                color: #263238;
            }
        """
        self.setStyleSheet(stylesheet)

    def _create_toolbar(self):
        """Create toolbar with qtawesome icons."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        history_action = QAction(qta.icon('fa5s.history'), "Show History", self)
        history_action.setToolTip("Show/hide query history panel")
        history_action.triggered.connect(self.toggle_history_dock)
        toolbar.addAction(history_action)
        toolbar.addSeparator()

        db_label = QLabel("Database:")
        db_label.setStyleSheet("color: #455A64; font-size: 14px; margin-right: 5px;")
        toolbar.addWidget(db_label)

        new_db_action = QAction(qta.icon('fa5s.database'), "New DB", self)
        new_db_action.setToolTip("Create a new database")
        new_db_action.triggered.connect(self.create_new_database)
        toolbar.addAction(new_db_action)

        new_col_action = QAction(qta.icon('fa5s.folder-plus'), "New Collection", self)
        new_col_action.setToolTip("Create a new collection")
        new_col_action.triggered.connect(self.create_collection)
        toolbar.addAction(new_col_action)

        delete_action = QAction(qta.icon('fa5s.trash'), "Delete", self)
        delete_action.setToolTip("Delete selected database or collection")
        delete_action.triggered.connect(self.handle_delete_action)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()

        query_label = QLabel("Query:")
        query_label.setStyleSheet("color: #455A64; font-size: 14px; margin-right: 5px;")
        toolbar.addWidget(query_label)

        new_query_action = QAction(qta.icon('fa5s.file-code'), "New Query", self)
        new_query_action.setToolTip("Open a new query tab (Ctrl+T)")
        new_query_action.triggered.connect(self.open_new_query_tab)
        toolbar.addAction(new_query_action)

        execute_action = QAction(qta.icon('fa5s.play'), "Execute", self)
        execute_action.setToolTip("Run the current query (F5)")
        execute_action.triggered.connect(self.execute_query)
        toolbar.addAction(execute_action)

        save_action = QAction(qta.icon('fa5s.save'), "Save", self)
        save_action.setToolTip("Save the current query (Ctrl+S)")
        save_action.triggered.connect(self.save_query)
        toolbar.addAction(save_action)

        self.save_shortcut = QShortcut(Qt.CTRL + Qt.Key_S, self)
        self.save_shortcut.activated.connect(self.save_query)
        self.execute_shortcut = QShortcut(Qt.Key_F5, self)
        self.execute_shortcut.activated.connect(self.execute_query)
        self.new_query_shortcut = QShortcut(Qt.CTRL + Qt.Key_T, self)
        self.new_query_shortcut.activated.connect(self.open_new_query_tab)

    def _create_main_layout(self):
        """Create main layout with splitter."""
        main_widget = ModernFrame()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        splitter = QSplitter(Qt.Horizontal)

        left_panel = ModernFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search databases/collections...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_bar)

        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel("Databases")
        self.db_tree.setAlternatingRowColors(True)
        self.db_tree.setAnimated(True)
        self.db_tree.setFont(QFont("Segoe UI", 10))
        left_layout.addWidget(self.db_tree)
        self.db_tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        splitter.addWidget(left_panel)

        right_panel = ModernFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        right_layout.addWidget(self.tabs)

        results_frame = ModernFrame()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(8, 8, 8, 8)

        results_header = QHBoxLayout()
        self.result_label = QLabel("Results")
        self.result_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        results_header.addWidget(self.result_label)
        self.result_status = QLabel("Ready")
        self.result_status.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        self.result_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        results_header.addWidget(self.result_status)
        results_layout.addLayout(results_header)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(QFont("Consolas", 12))
        results_layout.addWidget(self.result_display)
        right_layout.addWidget(results_frame)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 980])
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _create_query_history_dock(self):
        """Create dockable query history panel."""
        self.history_dock = QDockWidget("Query History", self)
        self.history_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        history_widget = ModernFrame()
        history_layout = QVBoxLayout(history_widget)
        history_label = QLabel("Recent Queries:")
        history_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        history_layout.addWidget(history_label)
        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        self.history_list.setFont(QFont("Consolas", 11))
        history_layout.addWidget(self.history_list)
        self.history_dock.setWidget(history_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.history_dock)

    def toggle_history_dock(self):
        """Toggle visibility of query history dock."""
        if self.history_dock.isVisible():
            self.history_dock.hide()
            self.status_bar.showMessage("Query history hidden")
        else:
            self.history_dock.show()
            self.status_bar.showMessage("Query history shown")

    def create_welcome_tab(self):
        """Create a welcome tab with a gradient background."""
        welcome_widget = QWidget()
        welcome_widget.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #26A69A, stop:1 #ECEFF1);")
        welcome_layout = QVBoxLayout(welcome_widget)

        welcome_title = QLabel("Welcome to Hash DBMS")
        welcome_title.setStyleSheet("font-size: 28px; color: #ffffff; font-weight: bold; margin: 20px;")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_title)

        welcome_text = QTextEdit()
        welcome_text.setReadOnly(True)
        welcome_text.setStyleSheet("background: #FFFFFF; color: #263238; border-radius: 6px; padding: 10px;")
        welcome_text.setHtml("""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.6;">
                <h2 style="color: #26A69A;">Get Started</h2>
                <p>Manage your databases with a modern, intuitive interface.</p>
                <h3 style="color: #455A64;">Database Operations</h3>
                <ul>
                    <li><b>New DB</b>: Create a database using the toolbar.</li>
                    <li><b>New Collection</b>: Add collections to organize data.</li>
                    <li>Right-click databases/collections for more options.</li>
                </ul>
                <h3 style="color: #455A64;">Querying</h3>
                <ul>
                    <li><b>New Query</b> (Ctrl+T): Open a query tab.</li>
                    <li><b>Execute</b> (F5): Run queries and view results.</li>
                    <li><b>Save</b> (Ctrl+S): Save queries to .sql or .txt files.</li>
                </ul>
                <h3 style="color: #455A64;">Tips</h3>
                <ul>
                    <li>Double-click collections to view records.</li>
                    <li>Use the search bar to filter the database tree.</li>
                    <li>Toggle the query history panel with the toolbar button.</li>
                </ul>
            </div>
        """)
        welcome_layout.addWidget(welcome_text)
        self.tabs.addTab(welcome_widget, qta.icon('fa5s.home'), "Welcome")

    def _populate_database_tree(self):
        """Populate database tree with qtawesome icons."""
        self.db_tree.clear()
        db_icon = qta.icon('fa5s.database')
        collection_icon = qta.icon('fa5s.folder')
        for db_name, db_obj in self.dbms.databases.items():
            db_item = QTreeWidgetItem([db_name])
            db_item.setIcon(0, db_icon)
            db_item.setFont(0, QFont("Segoe UI", 10, QFont.Bold))
            for collection_name in db_obj.collections.keys():
                collection_item = QTreeWidgetItem([collection_name])
                collection_item.setIcon(0, collection_icon)
                db_item.addChild(collection_item)
            self.db_tree.addTopLevelItem(db_item)
            db_item.setExpanded(True)

    def filter_tree(self, text):
        """Filter database tree based on search input."""
        text = text.lower()
        for i in range(self.db_tree.topLevelItemCount()):
            db_item = self.db_tree.topLevelItem(i)
            db_match = text in db_item.text(0).lower()
            db_item.setHidden(not db_match and not any(text in db_item.child(j).text(0).lower() for j in range(db_item.childCount())))
            for j in range(db_item.childCount()):
                coll_item = db_item.child(j)
                coll_item.setHidden(not db_match and not text in coll_item.text(0).lower())

    def create_new_database(self):
        """Create a new database."""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Create Database")
        dialog.setLabelText("Enter database name:")
        dialog.setWindowIcon(qta.icon('fa5s.database'))
        dialog.resize(400, 100)
        if dialog.exec_() == QDialog.Accepted:
            db_name = dialog.textValue().strip()
            if db_name:
                try:
                    self.dbms.create_database(db_name)
                    self._populate_database_tree()
                    self.status_bar.showMessage(f"Database '{db_name}' created")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
            else:
                QMessageBox.warning(self, "Invalid Name", "Database name cannot be empty.")

    def delete_database(self, item):
        """Delete a database with confirmation."""
        db_name = item.text(0)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Delete Database")
        dialog.setText(f"Are you sure you want to delete '{db_name}'?")
        dialog.setInformativeText("This action cannot be undone.")
        dialog.setIcon(QMessageBox.Warning)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        if dialog.exec_() == QMessageBox.Yes:
            try:
                self.dbms.delete_database(db_name)
                self._populate_database_tree()
                self.status_bar.showMessage(f"Database '{db_name}' deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def handle_delete_action(self):
        """Handle deletion of database or collection."""
        selected_items = self.db_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a database or collection.")
            return
        item = selected_items[0]
        if item.parent() is None:
            self.delete_database(item)
        else:
            self.delete_collection(item)

    def on_tree_item_double_clicked(self, item, column):
        """Display collection data on double-click."""
        if item.parent() is None:
            return
        db_name = item.parent().text(column)
        collection_name = item.text(column)
        collection = self.dbms.databases[db_name].collections.get(collection_name)
        if collection:
            self.current_open_collection = (db_name, collection_name)
            collection_data = [
                {"_id": obj_id, **obj.attributes}
                for record_list in collection.records.table
                for obj_id, obj in record_list
            ]
            if collection_data:
                html_content = """
                    <html>
                    <head>
                        <style>
                            body { font-family: 'Consolas', monospace; font-size: 12px; padding: 10px; color: #263238; }
                            pre { white-space: pre-wrap; background-color: #F5F5F5; padding: 10px; border-radius: 4px; }
                        </style>
                    </head>
                    <body>
                        <h2 style="color: #26A69A;">Collection: %s.%s</h2>
                        <p>%d record(s) found</p>
                        <pre>%s</pre>
                    </body>
                    </html>
                """ % (db_name, collection_name, len(collection_data), json.dumps(collection_data, indent=2))
            else:
                html_content = """
                    <html>
                    <head>
                        <style>
                            body { font-family: 'Consolas', monospace; font-size: 12px; padding: 20px; text-align: center; color: #455A64; }
                        </style>
                    </head>
                    <body>
                        <h2 style="color: #26A69A;">Collection: %s.%s</h2>
                        <p>No records</p>
                    </body>
                    </html>
                """ % (db_name, collection_name)
            tab = QTextEdit()
            tab.setReadOnly(True)
            tab.setHtml(html_content)
            tab.setProperty("is_collection_tab", True)
            self.tabs.addTab(tab, qta.icon('fa5s.table'), f"{db_name}.{collection_name}")
            self.tabs.setCurrentWidget(tab)
            self.status_bar.showMessage(f"Viewing {db_name}.{collection_name}")

    def _validate_keywords(self, query):
        """Validate that all keywords in the query are recognized and follow a valid command structure."""
        tokens = query.split()
        if not tokens:
            QMessageBox.critical(self, "Syntax Error", "Empty query")
            return False, "Empty query"

        # Define valid keywords and additional allowed tokens
        valid_keywords = {'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
                        'INTO', 'VALUES', 'COMMIT', 'ROLLBACK', 'BEGIN', 'USE', 'SHOW'}
        additional_tokens = {'ASC', 'DESC', 'ON', 'TO', 'SET', 'DATABASES', 'COLLECTIONS', 'RECORDS'}
        
        # Check the first token (command) strictly
        cmd = tokens[0].upper()
        if cmd not in valid_keywords:
            QMessageBox.critical(self, "Syntax Error", f"Invalid query: Unrecognized command '{cmd}'")
            return False, f"Invalid query: Unrecognized command '{cmd}'"

        # Validate based on the command structure
        if cmd == 'SHOW':
            if len(tokens) < 2:
                QMessageBox.critical(self, "Syntax Error", "Invalid query: SHOW requires a keyword (e.g., DATABASES, COLLECTIONS, or coll_name RECORDS)")
                return False, "Invalid query: SHOW requires a keyword (e.g., DATABASES, COLLECTIONS, or coll_name RECORDS)"
            sub_cmd = tokens[1].upper()
            if sub_cmd not in {'DATABASES', 'COLLECTIONS'} and (len(tokens) < 3 or tokens[2].upper() != 'RECORDS'):
                QMessageBox.critical(self, "Syntax Error", "Invalid query: Expected SHOW DATABASES, SHOW COLLECTIONS, or SHOW coll_name RECORDS")
                return False, "Invalid query: Expected SHOW DATABASES, SHOW COLLECTIONS, or SHOW coll_name RECORDS"

        # For other commands, check subsequent tokens
        for token in tokens[1:]:
            upper_token = token.upper()
            if (upper_token not in valid_keywords and 
                upper_token not in additional_tokens and 
                not any(c.isdigit() for c in token) and  # Allow numbers
                "'" not in token and                    # Allow quoted strings
                '=' not in token):                     # Allow key=value pairs
                QMessageBox.critical(self, "Syntax Error", f"Invalid query: Unrecognized keyword or token '{token}'")
                return False, f"Invalid query: Unrecognized keyword or token '{token}'"

        return True, ""
        
    def execute_query(self):
        """Execute query and display results in MongoDB-like JSON format."""
        current_tab = self.tabs.currentWidget()
        if not isinstance(current_tab, QTextEdit) or current_tab.property("is_collection_tab"):
            QMessageBox.warning(self, "No Query", "Please open a query tab.")
            return
        query = current_tab.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "No Query", "Please enter a query.")
            return
        is_valid, error_message = self._validate_keywords(query)
        if not is_valid:
            self.result_label.setText("Results (Error)")
            self.result_display.setHtml("""
            <html>
            <body style="font-family: 'Consolas', monospace; font-size: 12px; padding: 10px; color: #455A64;">
                <p>No results</p>
            </body>
            </html>
        """)
            self.status_bar.showMessage("Query execution failed")
            return
        try:
            self.result_label.setText("Results (Loading...)")
            self.result_display.setPlainText("")
            QApplication.processEvents()
            results = process_query(query, self.dbms, self.transaction_manager)
            if isinstance(results, dict) and "message" in results:
                QMessageBox.information(self, "Query Completed", results["message"])
                results = results.get("records", [])
            if results:
                formatted_results = json.dumps(results, indent=2)
                html_content = """
                    <html>
                    <head>
                        <style>
                            body { font-family: 'Consolas', monospace; font-size: 12px; padding: 10px; color: #263238; }
                            pre { white-space: pre-wrap; background-color: #F5F5F5; padding: 10px; border-radius: 4px; }
                        </style>
                    </head>
                    <body>
                        <pre>%s</pre>
                    </body>
                    </html>
                """ % formatted_results
                self.result_display.setHtml(html_content)
                self.result_label.setText(f"Results ({len(results)} documents)")
            else:
                self.result_display.setHtml("""
                    <html>
                    <body style="font-family: 'Consolas', monospace; font-size: 12px; padding: 10px; color: #455A64;">
                        <p>No results</p>
                    </body>
                    </html>
                """)
                self.result_label.setText("Results (0 documents)")
            self._populate_database_tree()
            self.query_history.append(query)
            if len(self.query_history) > 50:
                self.query_history.pop(0)
            self.history_list.setPlainText("\n\n".join(f"[{i+1}] {q}" for i, q in enumerate(self.query_history)))
            self.status_bar.showMessage("Query executed successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.result_label.setText("Results (Error)")
            self.result_display.setPlainText(str(e))
            self.status_bar.showMessage("Query execution failed")

    def save_query(self):
        """Save the current query to a file."""
        current_tab = self.tabs.currentWidget()
        if not isinstance(current_tab, QTextEdit) or current_tab.property("is_collection_tab"):
            QMessageBox.warning(self, "No Query", "Please open a query tab.")
            return
        query = current_tab.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "No Query", "Please enter a query.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Query", "", "SQL Files (*.sql);;Text Files (*.txt)")
        if file_path:
            with open(file_path, 'w') as file:
                file.write(query)
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(file_path))
            self.status_bar.showMessage(f"Query saved to {file_path}")

    def close_tab(self, index):
        """Close tab, prompting for save only for query tabs with content."""
        tab_widget = self.tabs.widget(index)
        if isinstance(tab_widget, QTextEdit) and not tab_widget.property("is_collection_tab"):
            query_content = tab_widget.toPlainText().strip()
            if query_content:
                reply = self._prompt_save_changes()
                if reply == QMessageBox.Yes:
                    self.save_query()
                    self.tabs.removeTab(index)
                elif reply == QMessageBox.No:
                    self.tabs.removeTab(index)
                    self.result_display.setPlainText("")
                    self.result_label.setText("Results")
                # Cancel does nothing
            else:
                self.tabs.removeTab(index)
                self.result_display.setPlainText("")
                self.result_label.setText("Results")
        else:
            self.tabs.removeTab(index)
        self.status_bar.showMessage("Ready")

    def _prompt_save_changes(self):
        """Prompt to save changes for query tabs."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Unsaved Changes")
        dialog.setText("You have unsaved changes in the query.")
        dialog.setInformativeText("Do you want to save them?")
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Cancel)
        dialog.setIcon(QMessageBox.Question)
        return dialog.exec_()

    def show_context_menu(self, position):
        """Show context menu with qtawesome icons."""
        item = self.db_tree.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        parent = item.parent()
        if parent is None:
            menu.addAction(qta.icon('fa5s.folder-plus'), "Create Collection", lambda: self.create_collection(item.text(0)))
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.edit'), "Rename Database", lambda: self.rename_item(item))
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.trash'), "Delete Database", lambda: self.delete_database(item))
        else:
            menu.addAction(qta.icon('fa5s.plus'), "Insert Record", lambda: self.open_insert_dialog(item))
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.edit'), "Rename Collection", lambda: self.rename_item(item))
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.trash'), "Delete Collection", lambda: self.delete_collection(item))
        menu.exec_(self.db_tree.viewport().mapToGlobal(position))

    def rename_item(self, item):
        """Rename a database or collection."""
        old_name = item.text(0)
        parent = item.parent()
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename")
        dialog.setLabelText(f"Enter new name for '{old_name}':")
        dialog.setTextValue(old_name)
        dialog.setWindowIcon(qta.icon('fa5s.edit'))
        dialog.resize(400, 100)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.textValue().strip()
            if new_name:
                try:
                    if parent is None:
                        self.dbms.rename_database(old_name, new_name)
                    else:
                        db_name = parent.text(0)
                        self.dbms.databases[db_name].rename_collection(old_name, new_name)
                    self._populate_database_tree()
                    self.status_bar.showMessage(f"Renamed to '{new_name}'")
                except Exception as e:
                    QMessageBox.critical(self, "Rename Error", str(e))

    def create_collection(self, db_name=None):
        """Create a new collection."""
        if not db_name:
            db_names = list(self.dbms.databases.keys())
            if not db_names:
                QMessageBox.warning(self, "No Databases", "Please create a database first.")
                return
            dialog = QInputDialog(self)
            dialog.setWindowTitle("Select Database")
            dialog.setLabelText("Choose database:")
            dialog.setComboBoxItems(db_names)
            dialog.setWindowIcon(qta.icon('fa5s.database'))
            dialog.resize(400, 100)
            if dialog.exec_() != QDialog.Accepted:
                return
            db_name = dialog.textValue()
        name_dialog = QInputDialog(self)
        name_dialog.setWindowTitle("Create Collection")
        name_dialog.setLabelText("Enter collection name:")
        name_dialog.setWindowIcon(qta.icon('fa5s.folder-plus'))
        name_dialog.resize(400, 100)
        if name_dialog.exec_() == QDialog.Accepted:
            collection_name = name_dialog.textValue().strip()
            if collection_name:
                try:
                    self.dbms.databases[db_name].create_collection(collection_name)
                    self._populate_database_tree()
                    self.status_bar.showMessage(f"Collection '{collection_name}' created in '{db_name}'")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
            else:
                QMessageBox.warning(self, "Invalid Name", "Collection name cannot be empty.")

    def open_insert_dialog(self, item):
        """Open dialog to insert a new record."""
        db_name = item.parent().text(0)
        collection_name = item.text(0)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Insert Record in {db_name}.{collection_name}")
        dialog.setWindowIcon(qta.icon('fa5s.plus'))
        dialog.setMinimumWidth(500)
        layout = QFormLayout()
        attributes_input = QLineEdit()
        attributes_input.setPlaceholderText("key1=value1, key2=value2")
        layout.addRow("Attributes (key=value):", attributes_input)
        help_label = QLabel("Example: name=John, age=30")
        help_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addRow("", help_label)
        buttons_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            background-color: #EF5350;
            color: #ffffff;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            border: none;
        """)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #EF5350;
                color: #ffffff;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #D81B60;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        save_button = QPushButton("Save Record")
        save_button.setIcon(qta.icon('fa5s.save'))
        save_button.clicked.connect(lambda: self.save_record(db_name, collection_name, dialog, attributes_input))
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        layout.addRow("", buttons_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def delete_collection(self, item):
        """Delete a collection with confirmation."""
        db_name = item.parent().text(0)
        collection_name = item.text(0)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Delete Collection")
        dialog.setText(f"Are you sure you want to delete '{collection_name}'?")
        dialog.setInformativeText(f"This will permanently remove the collection from '{db_name}'.")
        dialog.setIcon(QMessageBox.Warning)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        if dialog.exec_() == QMessageBox.Yes:  # Fix: Use QMessageBox.Yes instead of QDialog.Yes
            try:
                self.dbms.databases[db_name].delete_collection(collection_name)
                self._populate_database_tree()
                self.status_bar.showMessage(f"Collection '{collection_name}' deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e)) 

    def save_record(self, db_name, collection_name, dialog, attributes_input):
        """Save a new record to a collection."""
        attributes_str = attributes_input.text().strip()
        if not attributes_str:
            QMessageBox.warning(self, "Invalid Input", "Please enter attribute values.")
            return
        attributes = {}
        try:
            for pair in attributes_str.split(','):
                key, value = pair.split('=')
                attributes[key.strip()] = value.strip()
        except ValueError:
            QMessageBox.warning(self, "Invalid Format", "Use format: key=value, key2=value2")
            return
        collection = self.dbms.databases[db_name].collections.get(collection_name)
        if collection:
            object_id = collection.create_object(**attributes)
            dialog.accept()
            self._populate_database_tree()
            if self.current_open_collection == (db_name, collection_name):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == f"{db_name}.{collection_name}":
                        self.tabs.removeTab(i)
                        for j in range(self.db_tree.topLevelItemCount()):
                            db_item = self.db_tree.topLevelItem(j)
                            if db_item.text(0) == db_name:
                                for k in range(db_item.childCount()):
                                    coll_item = db_item.child(k)
                                    if coll_item.text(0) == collection_name:
                                        self.on_tree_item_double_clicked(coll_item, 0)
                                        break
                                break
            self.status_bar.showMessage(f"Record added with ID: {object_id}")
        else:
            QMessageBox.critical(self, "Error", f"Collection '{collection_name}' not found.")

    def open_new_query_tab(self):
        """Open a new query tab with syntax highlighting."""
        query_editor = QTextEdit()
        query_editor.setPlaceholderText("-- Enter your SQL query here\n-- Press F5 or click Execute to run")
        query_editor.setFont(QFont("Consolas", 12))
        SQLHighlighter(query_editor)
        tab_index = self.tabs.addTab(query_editor, qta.icon('fa5s.file-code'), "New Query")
        self.tabs.setCurrentIndex(tab_index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    
    # Show login dialog first
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        # Only show main window if login was successful
        window = DatabaseGUI()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)