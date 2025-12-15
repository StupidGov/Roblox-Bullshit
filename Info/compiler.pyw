# ============================================================================
#                       ViewFinder Compiler Tool (Enhanced)
# ============================================================================
"""
Enhanced compiler for ViewFinder project with auto-detection.
Creates standalone executables with all dependencies bundled.
Searches for files in subdirectories automatically.
"""

import sys
import os
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox, QGroupBox, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont


def find_file(filename, search_depth=3, custom_path=None):
    """
    Search for a file in current directory and subdirectories.
    If custom_path is provided, search there instead.
    Returns the full path if found, None otherwise.
    """
    # If custom path is provided, search only there
    if custom_path:
        search_root = Path(custom_path)
        # Check root directory
        target = search_root / filename
        if target.is_file():
            return str(target.absolute())
        
        # Search subdirectories
        for depth in range(1, search_depth + 1):
            pattern = "/".join(["*"] * depth) + f"/{filename}"
            matches = list(search_root.glob(pattern))
            if matches:
                return str(matches[0].absolute())
        return None
    
    # Original behavior - search from current directory
    # First check current directory
    if os.path.isfile(filename):
        return os.path.abspath(filename)
    
    # Search in subdirectories
    current_dir = Path.cwd()
    for depth in range(1, search_depth + 1):
        pattern = "/".join(["*"] * depth) + f"/{filename}"
        matches = list(current_dir.glob(pattern))
        if matches:
            return str(matches[0].absolute())
    
    return None


class CompileThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, targets, custom_path=None):
        super().__init__()
        self.targets = targets  # List of (file, name, description) tuples
        self.custom_path = custom_path

    def compile_single(self, target_file, output_name, description):
        """Compile a single file"""
        self.log_signal.emit("\n" + "=" * 60)
        self.log_signal.emit(f"Compiling: {description}")
        self.log_signal.emit("=" * 60)

        # Find the file (may be in subdirectory or custom path)
        found_path = find_file(target_file, custom_path=self.custom_path)
        if not found_path:
            self.log_signal.emit(f"✗ ERROR: File not found: {target_file}")
            if self.custom_path:
                self.log_signal.emit(f"  Searched in: {self.custom_path}")
            else:
                self.log_signal.emit(f"  Searched in current directory and subdirectories (depth 3)")
            return False
        
        self.log_signal.emit(f"✓ Found: {found_path}")
        self.log_signal.emit(f"📦 Output: {output_name}.exe\n")

        # Build PyInstaller command
        cmd = [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--clean",
            f"--name={output_name}",
            found_path
        ]

        self.log_signal.emit("Command: " + " ".join(cmd))
        self.log_signal.emit("-" * 60)

        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=creationflags
            )

            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.log_signal.emit(line.rstrip())

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                output_path = os.path.join("dist", f"{output_name}.exe")
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    self.log_signal.emit(f"\n✓ SUCCESS: {description}")
                    self.log_signal.emit(f"✓ Created: {output_path}")
                    self.log_signal.emit(f"✓ Size: {file_size:.2f} MB")
                    return True
                else:
                    self.log_signal.emit(f"\n✗ FAILED: Executable not found")
                    return False
            else:
                self.log_signal.emit(f"\n✗ FAILED: Compilation error (code {return_code})")
                return False

        except Exception as e:
            self.log_signal.emit(f"\n✗ ERROR: {str(e)}")
            return False

    def run(self):
        self.log_signal.emit("=" * 60)
        self.log_signal.emit("ViewFinder Compilation Started")
        self.log_signal.emit("=" * 60)

        # Check PyInstaller
        try:
            result = subprocess.run(
                ["pyinstaller", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.log_signal.emit(f"✓ PyInstaller: {result.stdout.strip()}\n")
        except FileNotFoundError:
            self.log_signal.emit("✗ ERROR: PyInstaller not found!")
            self.log_signal.emit("Install with: pip install pyinstaller")
            self.finished_signal.emit(False, "PyInstaller not installed")
            return

        # Compile each target
        all_success = True
        successful_files = []
        
        for target_file, output_name, description in self.targets:
            success = self.compile_single(target_file, output_name, description)
            if success:
                successful_files.append(f"{output_name}.exe")
            else:
                all_success = False

        # Final summary
        self.log_signal.emit("\n" + "=" * 60)
        self.log_signal.emit("COMPILATION SUMMARY")
        self.log_signal.emit("=" * 60)
        
        if all_success:
            self.log_signal.emit("🎉 All files compiled successfully!")
            self.log_signal.emit("\nGenerated files in 'dist' folder:")
            for file in successful_files:
                self.log_signal.emit(f"  ✓ {file}")
            
            if len(successful_files) == 3:
                self.log_signal.emit("\n📌 USAGE INSTRUCTIONS:")
                self.log_signal.emit("  1. Run ViewFinder.exe (the launcher)")
                self.log_signal.emit("  2. It will open the config menu first")
                self.log_signal.emit("  3. Then automatically start the main app")
                self.log_signal.emit("\n  OR distribute all 3 .exe files together!")
            
            self.finished_signal.emit(True, "All compilations successful!")
        else:
            self.log_signal.emit("⚠ Some compilations failed. Check log above.")
            if successful_files:
                self.log_signal.emit("\nSuccessful files:")
                for file in successful_files:
                    self.log_signal.emit(f"  ✓ {file}")
            self.finished_signal.emit(False, "Some compilations failed")


class CompilerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ViewFinder Compiler")
        self.setGeometry(200, 200, 900, 700)
        self.compile_thread = None
        self.custom_search_path = None  # Store custom folder path
        self.init_ui()
        self.apply_dark_theme()
        self.check_files_on_startup()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("ViewFinder Compiler")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Create standalone executables with all dependencies bundled")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Folder selection section
        folder_group = QGroupBox("Source Folder Selection")
        folder_layout = QVBoxLayout()
        
        folder_info = QLabel(
            "By default, files are searched in the current directory and subdirectories.\n"
            "You can specify a custom folder to search instead:"
        )
        folder_info.setWordWrap(True)
        folder_layout.addWidget(folder_info)
        
        folder_btn_layout = QHBoxLayout()
        
        self.browse_folder_btn = QPushButton("📁 Browse for Project Folder")
        self.browse_folder_btn.clicked.connect(self.browse_folder)
        folder_btn_layout.addWidget(self.browse_folder_btn)
        
        self.clear_folder_btn = QPushButton("Clear Custom Folder")
        self.clear_folder_btn.clicked.connect(self.clear_custom_folder)
        self.clear_folder_btn.setEnabled(False)
        folder_btn_layout.addWidget(self.clear_folder_btn)
        
        folder_layout.addLayout(folder_btn_layout)
        
        self.current_folder_label = QLabel("Current search location: <b>Current directory</b>")
        self.current_folder_label.setWordWrap(True)
        folder_layout.addWidget(self.current_folder_label)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # File detection status
        self.status_label = QLabel("Detecting project files...")
        self.status_label.setStyleSheet("color: #14ffec; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        options_group = QGroupBox("Compilation Options")
        options_layout = QVBoxLayout()
        
        info_label = QLabel(
            "Choose your compilation strategy:\n\n"
            "• Compile All (Recommended): Creates 3 standalone .exe files\n"
            "  - ViewFinder.exe (launcher)\n"
            "  - ViewFinder_Config.exe (config menu)\n"
            "  - ViewFinder_Main.exe (main overlay app)\n\n"
            "• Individual Compilation: Compile each component separately\n\n"
            "Note: Files are automatically detected in current directory and subdirectories"
        )
        info_label.setWordWrap(True)
        options_layout.addWidget(info_label)

        # Main button - Compile All
        self.compile_all_btn = QPushButton("🚀 Compile All Components\n(Recommended - Creates 3 .exe files)")
        self.compile_all_btn.clicked.connect(self.compile_all)
        self.compile_all_btn.setMinimumHeight(70)
        self.compile_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7377;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #14ffec;
                color: #000000;
            }
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #666666;
            }
        """)
        options_layout.addWidget(self.compile_all_btn)

        options_layout.addWidget(QLabel("\n--- OR Compile Individually ---\n"))

        # Individual buttons
        button_row = QHBoxLayout()

        self.compile_launcher_btn = QPushButton("Compile Launcher")
        self.compile_launcher_btn.clicked.connect(lambda: self.compile_single(
            "ViewFinder_Launcher.pyw", "ViewFinder", "Launcher"
        ))
        self.compile_launcher_btn.setMinimumHeight(50)
        button_row.addWidget(self.compile_launcher_btn)

        self.compile_config_btn = QPushButton("Compile Config")
        self.compile_config_btn.clicked.connect(lambda: self.compile_single(
            "ViewFinder_Config_Menu.pyw", "ViewFinder_Config", "Config Menu"
        ))
        self.compile_config_btn.setMinimumHeight(50)
        button_row.addWidget(self.compile_config_btn)

        self.compile_main_btn = QPushButton("Compile Main App")
        self.compile_main_btn.clicked.connect(lambda: self.compile_single(
            "ViewFinder_0.9.pyw", "ViewFinder_Main", "Main App"
        ))
        self.compile_main_btn.setMinimumHeight(50)
        button_row.addWidget(self.compile_main_btn)

        options_layout.addLayout(button_row)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Log output
        log_label = QLabel("Compilation Log:")
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 9))
        layout.addWidget(self.log_output)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.log_output.clear)
        bottom_layout.addWidget(self.clear_btn)

        self.open_dist_btn = QPushButton("Open Output Folder")
        self.open_dist_btn.clicked.connect(self.open_dist_folder)
        self.open_dist_btn.setEnabled(False)
        bottom_layout.addWidget(self.open_dist_btn)

        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def check_files_on_startup(self):
        """Check if project files are accessible on startup"""
        files_to_check = [
            "ViewFinder_Config_Menu.pyw",
            "ViewFinder_0.9.pyw",
            "ViewFinder_Launcher.pyw"
        ]
        
        found_files = []
        missing_files = []
        
        for file in files_to_check:
            path = find_file(file, custom_path=self.custom_search_path)
            if path:
                found_files.append(f"{file} ✓")
            else:
                missing_files.append(file)
        
        if not missing_files:
            self.status_label.setText(f"✓ All project files detected ({len(found_files)}/3)")
            self.status_label.setStyleSheet("color: #14ffec; padding: 5px;")
        else:
            self.status_label.setText(f"⚠ {len(missing_files)} file(s) not found - Individual compile may fail")
            self.status_label.setStyleSheet("color: #ff9800; padding: 5px;")

    def browse_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.custom_search_path = folder
            self.current_folder_label.setText(f"Current search location: <b>{folder}</b>")
            self.clear_folder_btn.setEnabled(True)
            
            # Re-check files with new path
            self.check_files_on_startup()
            
            self.log_output.append(f"Custom folder set: {folder}\n")

    def clear_custom_folder(self):
        """Clear custom folder and use default search"""
        self.custom_search_path = None
        self.current_folder_label.setText("Current search location: <b>Current directory</b>")
        self.clear_folder_btn.setEnabled(False)
        
        # Re-check files with default path
        self.check_files_on_startup()
        
        self.log_output.append("Custom folder cleared. Using current directory.\n")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d7377;
                border: 1px solid #14ffec;
            }
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #666666;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #14ffec;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
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
        """)

    def compile_all(self):
        """Compile all three components"""
        targets = [
            ("ViewFinder_Config_Menu.pyw", "ViewFinder_Config", "Config Menu"),
            ("ViewFinder_0.9.pyw", "ViewFinder_Main", "Main App"),
            ("ViewFinder_Launcher.pyw", "ViewFinder", "Launcher")
        ]
        
        # Check if all files can be found
        missing = []
        for file, _, _ in targets:
            if not find_file(file, custom_path=self.custom_search_path):
                missing.append(file)
        
        if missing:
            search_location = self.custom_search_path if self.custom_search_path else "current directory and subdirectories"
            QMessageBox.critical(
                self,
                "Files Not Found",
                f"Cannot find required files:\n\n" + "\n".join(missing) +
                f"\n\nSearched in: {search_location}\n"
                "Try using 'Browse for Project Folder' to specify the correct location."
            )
            return
        
        self.start_compilation(targets)

    def compile_single(self, target_file, output_name, description):
        """Compile a single component"""
        if not find_file(target_file, custom_path=self.custom_search_path):
            search_location = self.custom_search_path if self.custom_search_path else "current directory and subdirectories"
            QMessageBox.critical(
                self,
                "File Not Found",
                f"Cannot find {target_file}\n\n"
                f"Searched in: {search_location}\n"
                "Try using 'Browse for Project Folder' to specify the correct location."
            )
            return
        
        targets = [(target_file, output_name, description)]
        self.start_compilation(targets)

    def start_compilation(self, targets):
        """Start the compilation thread"""
        # Disable buttons
        self.compile_all_btn.setEnabled(False)
        self.compile_launcher_btn.setEnabled(False)
        self.compile_config_btn.setEnabled(False)
        self.compile_main_btn.setEnabled(False)
        self.open_dist_btn.setEnabled(False)
        self.browse_folder_btn.setEnabled(False)
        self.clear_folder_btn.setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)
        
        self.log_output.clear()
        
        # Start thread with custom path if set
        self.compile_thread = CompileThread(targets, self.custom_search_path)
        self.compile_thread.log_signal.connect(self.append_log)
        self.compile_thread.finished_signal.connect(self.compilation_finished)
        self.compile_thread.start()

    def append_log(self, text):
        self.log_output.append(text)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def compilation_finished(self, success, message):
        # Re-enable buttons
        self.compile_all_btn.setEnabled(True)
        self.compile_launcher_btn.setEnabled(True)
        self.compile_config_btn.setEnabled(True)
        self.compile_main_btn.setEnabled(True)
        self.browse_folder_btn.setEnabled(True)
        if self.custom_search_path:
            self.clear_folder_btn.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        if success:
            self.open_dist_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Success!",
                f"{message}\n\nYou can find the executables in the 'dist' folder."
            )
        else:
            QMessageBox.warning(
                self,
                "Compilation Issue",
                f"{message}\n\nCheck the log for details."
            )

    def open_dist_folder(self):
        dist_path = os.path.join(os.getcwd(), "dist")
        if os.path.exists(dist_path):
            if os.name == 'nt':
                os.startfile(dist_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', dist_path])
            else:
                subprocess.run(['xdg-open', dist_path])
        else:
            QMessageBox.information(self, "Folder Not Found", "The 'dist' folder doesn't exist yet.")


def main():
    app = QApplication(sys.argv)
    window = CompilerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()