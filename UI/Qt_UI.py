import sys
from pathlib import Path
import manager

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QFileDialog, QMessageBox
)


class FileLister(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件夹内容列表")
        self.resize(500, 400)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---- 第一行：路径输入框 + 浏览按钮 ----
        row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择或输入文件夹路径")
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.choose_folder)     # 信号 → 槽
        row.addWidget(self.path_input)
        row.addWidget(browse_btn)
        main_layout.addLayout(row)

        # ---- 第二行：开始按钮 ----
        start_btn = QPushButton("列出文件")
        start_btn.clicked.connect(self.list_files)
        main_layout.addWidget(start_btn)

        # ---- 列表 ----
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # ---- 状态标签 ----
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "C:/Users/accte"
        )
        if folder:                                  # 取消时返回 ""
            self.path_input.setText(folder)

    def list_files(self):
        path_text = self.path_input.text().strip()
        if not path_text:
            QMessageBox.warning(self, "提示", "请先选择文件夹")
            return

        folder = Path(path_text)
        if not folder.is_dir():
            QMessageBox.warning(self, "错误", f"不是有效文件夹：{folder}")
            return

        self.list_widget.clear()
        try:
            files = [p for p in folder.iterdir() if p.is_file()]
        except OSError as e:
            QMessageBox.warning(self, "错误", f"读取失败：{e}")
            return

        for f in files:
            self.list_widget.addItem(f.name)

        self.status_label.setText(f"共 {len(files)} 个文件")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileLister()
    window.show()
    sys.exit(app.exec())