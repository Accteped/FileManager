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
        self.current_moves = []

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
        move_btn = QPushButton("移动文件")
        reverse_btn = QPushButton("撤销移动操作")
        start_btn.clicked.connect(self.list_files)
        move_btn.clicked.connect(self.execute)
        reverse_btn.clicked.connect(self.reverse_move)
        row = QHBoxLayout()
        row.addWidget(start_btn)
        row.addWidget(move_btn)
        row.addWidget(reverse_btn)
        main_layout.addLayout(row)
        # ---- 列表 ----
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # ---- 状态标签 ----
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

    def choose_folder(self): #选择文件夹的组件
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "C:/Users/accte/Desktop"
        )
        if folder:                                  # 取消时返回 ""
            self.path_input.setText(folder)

    def list_files(self):  #列出文件的函数
        manager.history.clear()#把全局变量history清空
        path_text = self.path_input.text().strip()
        if not path_text:
            QMessageBox.warning(self, "提示", "请先选择文件夹")
            return

        folder = Path(path_text)
        if not folder.is_dir():
            QMessageBox.warning(self, "错误", f"不是有效文件夹：{folder}")
            return

        self.list_widget.clear()  #清空显示文件的列表
        try:
            files = manager.Plan_Moves(folder)#调用计划移动函数
            if files == -1:
                QMessageBox.warning(self, "错误", "访问文件夹失败")
                self.status_label.setText("访问失败")
                return
            
            total = len([p for p in folder.iterdir() if p.is_file()]) #统计文件总数
            skipped = total - len(files) #统计被跳过的文件
            if not files and skipped == 0:
                self.status_label.setText("没有需要整理的文件")
                return
            
        except OSError as e:
            QMessageBox.warning(self, "错误", f"读取失败：{e}")
            return
        failed_file = 0#统计无法移动文件
        for src, dst, status in files:
            if status == 'OK':
                self.list_widget.addItem(f"[准备移动]:{src.name} --> {dst.name}\\{src.name}")#列出每个文件的移动计划
            else:
                failed_file += 1
        if skipped:
            self.status_label.setText(f"共 {len(files)} 个将移动，{skipped} 个未匹配规则")
        elif failed_file:
            self.status_label.setText(f"共 {len(files)-failed_file} 个将移动，{failed_file} 个失败")
        else:
            self.status_label.setText(f"共 {len(files)} 个文件")
        self.current_moves = files

    def execute(self):
        if not self.current_moves:
            QMessageBox.warning(self,"提示","请先预览")
            return
        count = len([m for m in self.current_moves if m[2] == "OK"])
        ans = QMessageBox.question(self,
                          "确认", f"确定要移动{count}个文件吗",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return

        result = manager.execute_Move(self.current_moves)
        QMessageBox.information(
            self, "完成",
            f"成功 {result['success']} 个，失败 {len(result['failed'])} 个"
        )
        #更新状态栏
        self.status_label.setText(f"共成功移动 {result['success']} 个，失败移动 {len(result['failed'])} 个")
        
        #输出移动成功的文件
        self.list_widget.clear()
        for src, dst, status in self.current_moves:
            if status == 'OK':
                self.list_widget.addItem(f"[移动成功]:{src.name} --> {dst.name}\\{src.name}")#列出移动成功的每个文件
        self.current_moves = []

    def reverse_move(self):
        if not manager.history:
            QMessageBox.warning(self,"提示","请先进行移动操作")
            return
        #先判断有没有历史操作
        ans = QMessageBox.question(self,
                                  "确认", f"确定要撤回移动{len(manager.history)}个文件吗",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
                    return
        path_text = self.path_input.text().strip()
        result = manager.Cancel_MoveFile(Path(path_text))
        #弹窗显示结果
        QMessageBox.information(
                    self, "完成",
                    f"成功 {result['成功']} 个，失败 {len(result['失败'])} 个"
                )
        #显示失败信息
        self.list_widget.clear()
        if len(result['失败']):
            for text in result['失败']:
                self.list_widget.addItem(f"[失败信息]:f{text}")
        #更新状态栏
        self.status_label.setText(f"共成功撤销移动 {result['成功']} 个，失败撤销移动 {len(result['失败'])} 个")
        manager.history.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)
    window = FileLister()
    window.show()
    sys.exit(app.exec())