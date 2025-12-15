import sys
import subprocess
import os

# Check for PyQt6 before importing
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                 QPushButton, QTextEdit, QLabel, QMessageBox, QProgressBar)
    from PyQt6.QtCore import QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as e:
    print("=" * 60)
    print("ERROR: PyQt6 is not installed!")
    print("=" * 60)
    print("\nWould you like to install PyQt6 automatically?")
    choice = input("Install PyQt6? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("\nInstalling PyQt6...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "PyQt6"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ PyQt6 installed successfully!")
                print("Please run this script again.")
            else:
                print("✗ Installation failed:")
                print(result.stderr)
        except Exception as install_error:
            print(f"✗ Installation error: {install_error}")
    else:
        print("\nPlease install it manually by running:")
        print("  pip install PyQt6")
        print("\nOr:")
        print("  python -m pip install PyQt6")
        print("\nOr:")
        print("  py -m pip install PyQt6")
    
    print("=" * 60)
    input("\nPress Enter to exit...")
    sys.exit(1)


DARK_THEME = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}
QPushButton {
    background-color: #3d3d3d;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 5px 10px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #4d4d4d;
}
QPushButton:pressed {
    background-color: #555555;
}
QLabel {
    color: #ffffff;
}
QTextEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 5px;
    font-family: Consolas, Courier, monospace;
}
QProgressBar {
    border: 1px solid #555555;
    border-radius: 3px;
    text-align: center;
    background-color: #1e1e1e;
}
QProgressBar::chunk {
    background-color: #0d7377;
}
"""


class UninstallThread(QThread):
    """Thread to handle package uninstallation without freezing the GUI"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int, int)  # current, total
    
    def run(self):
        try:
            # Get list of installed packages
            self.output_signal.emit("Fetching list of installed packages...\n")
            self.progress_signal.emit(0, 0)  # Indeterminate progress
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.finished_signal.emit(False, "Failed to get package list")
                return
            
            # Parse package names (exclude pip, setuptools, and wheel to avoid issues)
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line and '==' in line:
                    pkg_name = line.split('==')[0]
                    # Skip critical packages
                    if pkg_name.lower() not in ['pip', 'setuptools', 'wheel']:
                        packages.append(pkg_name)
            
            if not packages:
                self.finished_signal.emit(True, "No packages to uninstall")
                return
            
            total_packages = len(packages)
            self.output_signal.emit(f"Found {total_packages} packages to uninstall\n")
            self.output_signal.emit(f"Packages: {', '.join(packages)}\n\n")
            
            # Uninstall packages one by one to show progress
            self.output_signal.emit("Uninstalling packages...\n")
            self.output_signal.emit("-" * 60 + "\n")
            
            failed_packages = []
            
            for i, pkg_name in enumerate(packages, 1):
                self.progress_signal.emit(i, total_packages)
                self.output_signal.emit(f"[{i}/{total_packages}] Uninstalling {pkg_name}...")
                
                uninstall_result = subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", pkg_name],
                    capture_output=True,
                    text=True
                )
                
                if uninstall_result.returncode == 0:
                    self.output_signal.emit(" ✓ Success\n")
                else:
                    self.output_signal.emit(f" ✗ Failed\n")
                    failed_packages.append(pkg_name)
                    if uninstall_result.stderr:
                        self.output_signal.emit(f"   Error: {uninstall_result.stderr}\n")
            
            self.output_signal.emit("\n" + "-" * 60 + "\n")
            
            if not failed_packages:
                self.finished_signal.emit(True, f"Successfully uninstalled {total_packages} packages!")
            else:
                self.output_signal.emit(f"\n⚠ Failed to uninstall {len(failed_packages)} packages:\n")
                for pkg in failed_packages:
                    self.output_signal.emit(f"  - {pkg}\n")
                self.finished_signal.emit(False, f"Failed to uninstall {len(failed_packages)} packages")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")


class PackageUninstallerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uninstall_thread = None
        self.init_ui()
        self.apply_theme()
        
    def init_ui(self):
        self.setWindowTitle("Python Package Uninstaller")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Warning label
        warning_label = QLabel(
            "⚠️ WARNING: This will uninstall ALL pip packages (except pip, setuptools, wheel)\n"
            "This action cannot be undone easily!"
        )
        warning_label.setStyleSheet("color: #ff4444; font-weight: bold; padding: 10px; font-size: 13px;")
        main_layout.addWidget(warning_label)
        
        # Info button
        self.info_button = QPushButton("Show Installed Packages")
        self.info_button.clicked.connect(self.show_packages)
        main_layout.addWidget(self.info_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 9))
        main_layout.addWidget(self.output_text)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Clear log button
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.output_text.clear)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # Uninstall button
        self.uninstall_button = QPushButton("🗑️ UNINSTALL ALL PACKAGES")
        self.uninstall_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #b71c1c;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #a01c1c;
            }
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #666666;
            }
        """)
        self.uninstall_button.clicked.connect(self.confirm_uninstall)
        button_layout.addWidget(self.uninstall_button)
        
        main_layout.addLayout(button_layout)
        
    def show_packages(self):
        """Display currently installed packages"""
        self.output_text.clear()
        self.output_text.append("Fetching installed packages...\n")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True
            )
            self.output_text.append(result.stdout)
        except Exception as e:
            self.output_text.append(f"Error: {str(e)}")
    
    def confirm_uninstall(self):
        """Show confirmation dialog before uninstalling"""
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            "Are you ABSOLUTELY SURE you want to uninstall ALL Python packages?\n\n"
            "This will remove:\n"
            "- PyQt6 (this application won't run afterward)\n"
            "- All other installed packages\n"
            "- You'll need to reinstall everything manually\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_uninstall()
    
    def start_uninstall(self):
        """Start the uninstallation process in a separate thread"""
        self.output_text.clear()
        self.uninstall_button.setEnabled(False)
        self.info_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # Show and reset progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)  # Indeterminate mode initially
        self.progress_bar.setValue(0)
        
        self.uninstall_thread = UninstallThread()
        self.uninstall_thread.output_signal.connect(self.update_output)
        self.uninstall_thread.progress_signal.connect(self.update_progress)
        self.uninstall_thread.finished_signal.connect(self.uninstall_finished)
        self.uninstall_thread.start()
    
    def update_output(self, text):
        """Update the output text area"""
        self.output_text.append(text)
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, current, total):
        """Update the progress bar"""
        if total == 0:
            # Indeterminate progress
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
    
    def uninstall_finished(self, success, message):
        """Handle completion of uninstallation"""
        self.uninstall_button.setEnabled(True)
        self.info_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Complete", message)
        else:
            QMessageBox.warning(self, "Error", message)
    
    def apply_theme(self):
        """Apply the dark theme matching your ViewFinder style"""
        self.setStyleSheet(DARK_THEME)


def main():
    try:
        app = QApplication(sys.argv)
        window = PackageUninstallerGUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("=" * 60)
        print("ERROR OCCURRED:")
        print("=" * 60)
        print(str(e))
        print("=" * 60)
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()