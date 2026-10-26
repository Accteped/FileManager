import sys,time
from pathlib import Path
import manager

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QFileDialog, QMessageBox,QProgressBar,QDialog,QFormLayout,QPlainTextEdit
)

class MoveWorker(QThread):
    result_ready = Signal(dict)#结束信号
    progress = Signal(int, int)#过程的进程信号

    def __init__(self, moves):
        super().__init__()
        self.moves = moves

    def run(self):
        #传入on_progress而发送当前进度
        result = manager.execute_Move(
            self.moves,
            on_progress=lambda cur,total: self.progress.emit(cur,total))
        #发送结束信号
        self.result_ready.emit(result)

class ReverseMoveWorker(QThread):
    result_ready = Signal(dict)#结束信号
    progress = Signal(int, int)#过程的进程信号

    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir

    def run(self):
        result = manager.Cancel_MoveFile(
            self.base_dir,
            on_progress = lambda cur,total: self.progress.emit(cur,total))
        self.result_ready.emit(result)

class FileLister(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件夹内容列表")
        self.resize(500, 400)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        self.current_moves = []
        self.ismove = False

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
        self.start_btn = QPushButton("列出文件")
        self.move_btn = QPushButton("移动文件")
        self.reverse_btn = QPushButton("撤销移动操作")
        self.start_btn.clicked.connect(self.list_files)
        self.move_btn.clicked.connect(self.execute)
        self.reverse_btn.clicked.connect(self.reverse_move)
        row = QHBoxLayout()
        row.addWidget(self.start_btn)
        row.addWidget(self.move_btn)
        row.addWidget(self.reverse_btn)
        main_layout.addLayout(row)

        # ---- 进度条 ----    
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
    
        # ---- 列表 ----
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # ---- 最后一栏 ----
        self.edit_btn = QPushButton("编辑文件分类规则")
        self.edit_btn.clicked.connect(self.OpenEditor)
        rows = QHBoxLayout()
        rows.addWidget(self.edit_btn)
        main_layout.addLayout(rows)

        # ---- 状态标签 ----
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

    def choose_folder(self): #选择文件夹的组件
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "C:/Users/accte/Desktop"
        )
        if folder:                                  # 取消时返回 ""
            self.path_input.setText(folder)
    #列出文件的函数
    def list_files(self):  
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
    #移动文件
    def execute(self):
        if not self.current_moves:
            QMessageBox.warning(self,"提示","请先预览")
            return
        count = len([m for m in self.current_moves if m[2] == "OK"])
        ans = QMessageBox.question(self,
                          "确认", f"确定要移动{count}个文件吗",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return
        #准备进度条
        self.progress_bar.setMaximum(len(self.current_moves))
        self.progress_bar.setValue(0)
        #禁用按键并更新状态栏
        self.move_btn.setEnabled(False)
        self.status_label.setText("正在移动...")
        #新开一个线程开始工作
        self.worker = MoveWorker(self.current_moves)
        self.worker.progress.connect(self.on_progress)
        self.worker.result_ready.connect(self.move_finished)
        self.worker.start()
    #恢复文件
    def reverse_move(self):
        if not manager.history or not self.ismove:
            QMessageBox.warning(self,"提示","请先进行移动操作")
            return
        #先判断有没有历史操作
        ans = QMessageBox.question(self,
                                    "确认", f"确定要撤回移动{len(manager.history)}个文件吗",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
                    return
        path_text = self.path_input.text().strip()

        #准备进度条
        self.progress_bar.setMaximum(len(manager.history))
        self.progress_bar.setValue(0)
        #禁用按键并更新状态栏
        self.reverse_btn.setEnabled(False)
        self.status_label.setText("正在还原...")

        self.worker = ReverseMoveWorker(Path(path_text))
        self.worker.progress.connect(self.on_progress)
        self.worker.result_ready.connect(self.reverse_finished)
        self.worker.start()
    #汇报进程实时修改进度条
    def on_progress(self, cur, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(cur)
        self.status_label.setText(f"处理中{cur}/{total}")
    #收到移动文件的结束信号
    def move_finished(self,result):
        self.move_btn.setEnabled(True)
        self.ismove = True
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
    #收到恢复文件的结束信号  
    def reverse_finished(self,result):
        self.reverse_btn.setEnabled(True)
        #弹窗显示结果
        QMessageBox.information(
                    self, "完成",
                    f"成功 {result['成功']} 个，失败 {len(result['失败'])} 个"
                )
        #显示失败信息
        self.list_widget.clear()
        if len(result['失败']):
            for text in result['失败']:
                self.list_widget.addItem(f"[失败信息]:{text}")
        #更新状态栏
        self.status_label.setText(f"共成功撤销移动 {result['成功']} 个，失败撤销移动 {len(result['失败'])} 个")
        manager.history.clear()
        self.ismove = False
    #打开分类规则设置的子窗口
    def OpenEditor(self):
        Dialog = RulesEditor(manager.FILE, parent=self)
        if Dialog.exec() == QDialog.DialogCode.Accepted:      # 用户点了保存
            manager.FILE = Dialog.result_rules                 # 更新全局规则
            manager.save_rules(Dialog.result_rules)            # 写回 json
            QMessageBox.information(self, "完成", "规则已保存")
    
    
class RulesEditor(QDialog):
    def __init__(self, rules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分类规则设置")
        self.resize(500, 400)

        self.rules = dict(rules)
        self.result_rules = self.rules
        self.current_item = None
        self.current_category = None
        # ========== 中间水平分左右 =========
        middle = QHBoxLayout()
        # ========== 最外层垂直 ========
        main_layout = QVBoxLayout(self)
        # ========== 左边 ==========
        left = QVBoxLayout()
        left.addWidget(QLabel("类别"))
        self.list_widget = QListWidget()

        self.list_widget.itemClicked.connect(self.on_category_selected)

        left.addWidget(self.list_widget)
        # 左边底部的两个按钮
        left_btns = QHBoxLayout()
        self.add_btn = QPushButton("新增")
        self.del_btn = QPushButton("删除")

        self.add_btn.clicked.connect(self.addRules)
        self.del_btn.clicked.connect(self.delRules)

        left_btns.addWidget(self.add_btn)
        left_btns.addWidget(self.del_btn)
        left.addLayout(left_btns)            # 注意：addLayout 不是 addWidget

        # ===========右边============
        right = QVBoxLayout()
        # 用 QFormLayout 让"标签 + 输入框"自动成对排列
        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("类别名称:", self.name_edit)
        right.addLayout(form)

        right.addWidget(QLabel("扩展名（每行一个）:"))
        self.ext_edit = QPlainTextEdit()
        self.ext_edit.setPlaceholderText(".jpg\n.png\n.gif")
        right.addWidget(self.ext_edit)

        self.name_edit.textChanged.connect(self.on_name_changed)
        # ---------- 把左右装进中间 ----------
        middle.addLayout(left, 1)            # 1 = 拉伸系数，占 1 份宽
        middle.addLayout(right, 2)           # 2 = 占 2 份宽（右边更宽）

        main_layout.addLayout(middle, 1)     # 中间区域占 1 份高（会拉伸）

        # ========== 底部按钮行 ==========
        bottom = QHBoxLayout()
        bottom.addStretch()                  # 弹簧：把后面的按钮推到右边
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        bottom.addWidget(self.save_btn)
        bottom.addWidget(self.cancel_btn)
        main_layout.addLayout(bottom)

        # ========== 填数据 ==========
        for cat in self.rules:
            self.list_widget.addItem(cat)

    def on_name_changed(self, text):
        if not self.current_item:
            return
        new_name = text.strip()
        if new_name:
            self.current_item.setText(new_name)
    def accept(self):                    # QDialog 自带的方法
        self.save_current_to_rules()     # 保存最后编辑的
        self.result_rules = self.rules   # 暴露出去
        super().accept()                 # 关闭对话框，返回 Accepted
    #新增类别
    def addRules(self):
        new_name = "新类别"
        base, i = new_name, 1
        while new_name in self.rules:
            new_name = f"{base}{i}"
            i += 1
        self.rules[new_name] = []
        print(new_name)
        self.list_widget.addItem(new_name)
    #删除类别名
    def delRules(self):
        item = self.list_widget.currentItem()
        self.current_item = None
        self.current_category = None
        self.UpdateExtlist()
        if not item:
            return
        print(f"删除{item.text()}")
        self.rules.pop(item.text(), None)
        self.list_widget.takeItem(self.list_widget.row(item))
    #在切换类别时实时保存规则
    def save_current_to_rules(self):
        name = self.name_edit.text().strip()#获取修改的类型名
        if not name:
            return
        exts = [line.strip() for line in self.ext_edit.toPlainText().splitlines() if(line.strip() and line.strip()[0] == '.')]#把后缀名按行分割,自动删掉不合法的后缀
        #---- 处理用户修改了类名的情况 ----
        olds = self.current_category
        if olds and olds != name:
            self.rules.pop(olds,None)
        self.rules[name] = exts
        print(f"name = {name}")
        print(f"self.rules[{name}] = {exts}")

    def UpdateExtlist(self):
        item = self.current_item
        if not item:
            self.ext_edit.setPlaceholderText(".jpg\n.png\n.gif")
            return
        name = item.text() # 类别名
        self.current_category = name
        if name not in self.rules:
            self.name_edit.setText(None)
            self.ext_edit.setPlaceholderText(".jpg\n.png\n.gif")
            return
        exts = self.rules[name]# 扩展名列表
        self.name_edit.setText(name)
        self.ext_edit.setPlainText("\n".join(exts))
    #选中类别表中的类别
    def on_category_selected(self, item):
        self.save_current_to_rules()
        self.current_item = item
        self.UpdateExtlist()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)
    window = FileLister()
    window.show()
    sys.exit(app.exec())