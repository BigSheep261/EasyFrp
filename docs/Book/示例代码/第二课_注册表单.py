"""第二课：控件、表单布局、取值与简单校验。

这是练习用的本地表单，不创建真实账户，不保存或发送密码。
"""

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class RegistrationWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("第二课：学习登记表")
        self.resize(520, 430)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("填写你的昵称")
        self.name_edit.setMaxLength(30)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("练习用密码，至少 6 个字符")

        self.age_spin = QSpinBox()
        self.age_spin.setRange(13, 120)
        self.age_spin.setValue(18)
        self.age_spin.setSuffix(" 岁")

        self.level_combo = QComboBox()
        self.level_combo.addItem("刚开始学习", "beginner")
        self.level_combo.addItem("可以写 Python 小脚本", "python")
        self.level_combo.addItem("有其他 GUI 经验", "gui")

        self.intro_edit = QPlainTextEdit()
        self.intro_edit.setPlaceholderText("你希望做出什么桌面工具？")
        self.intro_edit.setMaximumHeight(100)

        self.agree_check = QCheckBox("我知道这是练习表单，不会创建真实账户")
        self.result_label = QLabel("请填写资料。")
        self.result_label.setWordWrap(True)

        self.submit_button = QPushButton("检查并提交")
        self.reset_button = QPushButton("重置")

        form = QFormLayout()
        form.addRow("昵称：", self.name_edit)
        form.addRow("练习密码：", self.password_edit)
        form.addRow("年龄：", self.age_spin)
        form.addRow("学习基础：", self.level_combo)
        form.addRow("学习目标：", self.intro_edit)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.submit_button)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(self.agree_check)
        root.addWidget(self.result_label)
        root.addLayout(buttons)

        self.submit_button.clicked.connect(self.submit_form)
        self.reset_button.clicked.connect(self.reset_form)
        self.name_edit.textChanged.connect(self.update_submit_state)
        self.agree_check.toggled.connect(self.update_submit_state)
        self.update_submit_state()

    def update_submit_state(self) -> None:
        has_name = bool(self.name_edit.text().strip())
        self.submit_button.setEnabled(has_name and self.agree_check.isChecked())

    def submit_form(self) -> None:
        name = self.name_edit.text().strip()
        password = self.password_edit.text()
        if not name:
            self.result_label.setText("请先填写昵称。")
            self.name_edit.setFocus()
            return
        if not self.agree_check.isChecked():
            self.result_label.setText("请先勾选练习说明。")
            return
        if len(password) < 6:
            self.result_label.setText("练习密码至少需要 6 个字符。")
            self.password_edit.setFocus()
            return

        age = self.age_spin.value()
        level_text = self.level_combo.currentText()
        level_code = self.level_combo.currentData()
        goal = self.intro_edit.toPlainText().strip() or "暂未填写"
        # 密码只用于本次校验，不回显、不记录、不写入文件。
        self.result_label.setText(
            f"已通过本地检查：{name}，{age} 岁，{level_text}（{level_code}）。\n"
            f"学习目标：{goal}"
        )

    def reset_form(self) -> None:
        self.name_edit.clear()
        self.password_edit.clear()
        self.age_spin.setValue(18)
        self.level_combo.setCurrentIndex(0)
        self.intro_edit.clear()
        self.agree_check.setChecked(False)
        self.result_label.setText("已重置，请重新填写。")
        self.name_edit.setFocus()


def main() -> int:
    app = QApplication(sys.argv)
    window = RegistrationWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
