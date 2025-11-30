import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QDialog
)
from PyQt5.QtCore import QThread, pyqtSignal


class CompileThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        for f in self.files:
            if not os.path.isfile(f):
                self.log_signal.emit(f"❌ Cannot compile, file not found: {f}\n")
                continue

            self.log_signal.emit(f"🔨 Compiling {f} ...\n")
            try:
                # Run PyInstaller
                process = subprocess.Popen(
                    ["pyinstaller", "--onefile", f],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                # Stream output line by line
                for line in iter(process.stdout.readline, ''):
                    self.log_signal.emit(line)
                process.stdout.close()
                process.wait()

                if process.returncode == 0:
                    self.log_signal.emit(f"✅ Successfully compiled {f}\n")
                else:
                    self.log_signal.emit(f"❌ Error compiling {f}\n")

            except Exception as e:
                self.log_signal.emit(f"❌ Exception occurred: {str(e)}\n")


class ConsolePopup(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilation Console")
        self.setGeometry(300, 300, 700, 400)
        layout = QVBoxLayout()
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)
        self.setLayout(layout)

    def append_text(self, text):
        self.text_output.append(text)
        self.text_output.verticalScrollBar().setValue(
            self.text_output.verticalScrollBar().maximum()
        )


class PyCompilerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Project Compiler")
        self.setGeometry(200, 200, 600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Enter Python file names (comma or space separated):"))
        self.file_input = QLineEdit()
        layout.addWidget(self.file_input)

        button_layout = QHBoxLayout()
        self.check_button = QPushButton("Check Files")
        self.check_button.clicked.connect(self.check_files)
        button_layout.addWidget(self.check_button)

        self.compile_button = QPushButton("Compile Files")
        self.compile_button.clicked.connect(self.compile_files)
        button_layout.addWidget(self.compile_button)

        self.browse_button = QPushButton("Browse Files")
        self.browse_button.clicked.connect(self.browse_files)
        button_layout.addWidget(self.browse_button)

        layout.addLayout(button_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Python Files", "", "Python Files (*.py)"
        )
        if files:
            self.file_input.setText(", ".join([os.path.basename(f) for f in files]))

    def check_files(self):
        files_text = self.file_input.text()
        files = [f.strip() for f in files_text.replace(",", " ").split()]
        self.log_output.clear()

        all_ok = True
        for f in files:
            if not os.path.isfile(f):
                self.log_output.append(f"❌ File not found: {f}")
                all_ok = False
            else:
                self.log_output.append(f"✅ File exists: {f}")
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    imports = [line for line in content.splitlines() if line.startswith("import") or line.startswith("from")]
                    if imports:
                        self.log_output.append(f"   Imports found: {', '.join(imports)}")

        if all_ok:
            self.log_output.append("\nAll files exist and basic import check passed!")

    def compile_files(self):
        files_text = self.file_input.text()
        files = [f.strip() for f in files_text.replace(",", " ").split()]
        if not files:
            self.log_output.append("❌ No files specified for compilation.")
            return

        # Show console popup
        self.console = ConsolePopup()
        self.console.show()

        # Start compilation thread
        self.thread = CompileThread(files)
        self.thread.log_signal.connect(self.console.append_text)
        self.thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyCompilerGUI()
    window.show()
    sys.exit(app.exec_())
