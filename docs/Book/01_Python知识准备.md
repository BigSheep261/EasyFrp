# 第 1 章：先补齐写界面需要的 Python

> 前置知识：变量、字符串、列表、条件、循环和普通函数。目标：看懂窗口类中的 `self`、`super()`、回调和导入，并能把一小段业务规则从界面中取出来。

写 PyQt6 不需要先学完 Python 的所有高级特性，但必须理解“对象”和“把函数交给别人调用”。很多初学者并不是被 Qt 难住，而是还没理解这两点就开始复制窗口代码。

## 1.1 从变量走到对象

下面是普通 Python，可以直接保存为临时练习脚本运行：

```python
class Learner:
    def __init__(self, name: str) -> None:
        self.name = name
        self.finished_count = 0

    def finish_one(self) -> str:
        self.finished_count += 1
        return f"{self.name} 已完成 {self.finished_count} 节"


alice = Learner("小林")
bob = Learner("小周")
print(alice.finish_one())
print(alice.finish_one())
print(bob.finish_one())
```

`class Learner` 定义一种对象的结构。`Learner("小林")` 创建一个实例，也就是一个具体对象；`alice` 是指向它的变量。类像一份设计，实例是按设计创建出来的一个东西。

`__init__` 在实例创建后初始化它。`self` 表示这次调用对应的实例。调用 `alice.finish_one()` 时，Python 会把 `alice` 对应的对象传给 `self`，不用手动再写一遍。`self.name`、`self.finished_count` 是对象属性，会在方法调用结束后继续存在。

输出中小林完成两节，小周只完成一节，因为两个实例各有自己的 `finished_count`。以后每个窗口对象也有自己的输入框、按钮和状态。

在类里定义、通过对象调用的函数通常叫**方法**。`print()` 是函数；`alice.finish_one()` 是方法调用。它们都可执行代码，但方法天然关联一个对象。

## 1.2 局部变量与 self 属性

```python
def describe(self) -> str:
    prefix = "学习者："       # 本次调用中的局部变量
    return prefix + self.name  # 对象已经保存的属性
```

这段是 `Learner` 类内的方法片段，不能作为完整脚本直接运行。方法结束后，局部名字 `prefix` 不再可用。只要对象仍然存在，别的方法仍可以读取 `self.name`。

写界面时，如果按钮回调稍后需要读取输入框，就保存为 `self.name_edit`。如果某个布局只在构建界面时使用，通常写局部变量 `layout` 即可。不要为了省略 `self` 把所有控件变成全局变量，也不要误认为“局部名字消失”总是等于“Qt 控件立刻销毁”；Qt 还有父子对象的所有权关系，第 4、10 章会解释。

一个常见坑是把每个实例独有的可变数据写成类属性：

```python
class Notebook:
    def __init__(self) -> None:
        self.notes = []  # 每个实例新建一份列表
```

如果在类体直接写 `notes = []`，这个列表会被实例共享。普通窗口状态先放在 `__init__` 中。后面 `pyqtSignal(...)` 反而要放在类体，那是 Qt 绑定约定的特殊声明，不要混为一谈。

## 1.3 继承、super 与组合

PyQt6 中经常出现下面的结构。这是结构说明，尚不是完整程序：

```python
from PyQt6.QtWidgets import QWidget


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("学习窗口")
```

`MainWindow(QWidget)` 表示新类继承 `QWidget`。它因此获得窗口显示、大小调整等能力。`super().__init__()` 调用继承链上的初始化方法，在这里完成 `QWidget` 必要的初始化，必须在使用这个 Qt 对象之前执行。

继承表达“它是一种什么”。主窗口是一种窗口，所以可以继承窗口类。组合表达“它里面有什么”。主窗口里面有输入框，应当创建一个 `QLineEdit` 放进去，而不是为了拥有输入框能力而同时继承很多控件类。

你了解的 MFC 中也有派生窗口类的写法，可以借此理解继承。但 Qt 的父窗口关系和 Python 的继承关系是两回事：`MainWindow(QWidget)` 是类与类的关系；`QPushButton("保存", parent_widget)` 是对象与对象的关系。

## 1.4 回调：交出函数，不是立刻执行函数

```python
def say_hello() -> None:
    print("你好")


callback = say_hello
callback()
```

第一行赋值把函数对象交给 `callback`，没有运行函数。第二行加上括号才调用它。下面两行含义完全不同：

```python
callback = say_hello     # 保存函数，稍后可执行
result = say_hello()     # 现在执行；函数无 return，所以结果是 None
```

PyQt6 的 `button.clicked.connect(self.save)` 使用第一种思想：先登记一个方法，用户点击时框架再调用它。误写成 `connect(self.save())`，会在搭建界面时立刻保存，并把返回值传给 `connect`，常见结果是报“参数不是可调用对象”。

`lambda` 可以临时创建短函数：`lambda: print("你好")`。先掌握普通 `def` 方法，等到第 7 章再学习如何用 `lambda` 给回调附加参数。复杂校验和多步操作应写成有名字的方法，便于断点调试。

## 1.5 导入与程序入口

`import sys` 引入一个模块；`from pathlib import Path` 从模块取出一个名字；`from PyQt6.QtWidgets import QWidget` 从 PyQt6 的控件模块导入一个类。导入名称不等于创建对象，`QWidget` 是类，`QWidget()` 才创建实例。

Python 会执行被导入模块的顶层语句。假设某个模块顶层直接打开窗口，其他文件一导入它也会弹窗。因此程序入口通常写成：

```python
def main() -> int:
    print("这里将来启动程序")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

直接运行本文件时，`__name__` 为 `"__main__"`，执行入口；作为模块被导入时，不执行这个入口。这让类和函数能够被其他文件、测试代码复用。

不要把练习文件命名为 `PyQt6.py`、`sys.py`、`json.py` 或 `pathlib.py`，它们可能遮住你真正想导入的库。

## 1.6 异常与校验不是同一件事

用户还没输入年龄属于正常输入状态；读取一个不存在的文件会触发异常。两者都应处理，但不要用一个覆盖整个程序的 `except: pass` 隐藏错误。

```python
def parse_age(text: str) -> int:
    try:
        age = int(text)
    except ValueError as exc:
        raise ValueError("年龄必须是整数") from exc
    if not 0 <= age <= 120:
        raise ValueError("年龄必须在 0 到 120 之间")
    return age
```

这段纯函数不依赖任何窗口。它接收字符串，成功时返回整数，失败时抛出有意义的异常。未来界面层负责取输入框文本、调用它、把错误显示给用户。业务规则因此能单独验证和复用。

`try` 放可能失败的操作；`except ValueError` 只处理预期的类型；`raise` 抛出异常；`from exc` 保存原始错误的因果关系。遇到未知异常，要看终端中的 traceback，找到最后几行的异常类型，再向上找到自己的文件与行号。

## 1.7 类型提示和文件路径

`name: str` 表示预期传字符串，`-> int` 表示预期返回整数，`-> None` 表示没有有用返回值。类型提示帮助 IDE 和阅读者理解接口，默认不会在运行时替你强制检查类型。Python 3.12 中可以直接写 `list[str]`；`QObject | None` 表示 QObject 或空值。

处理文件路径优先用 `Path`：

```python
from pathlib import Path

script_dir = Path(__file__).resolve().parent
data_path = script_dir / "练习数据.txt"
print(data_path)
```

`Path` 表达路径；`/` 在这里连接路径片段。`__file__` 是当前脚本路径，`resolve()` 转为绝对路径，`.parent` 取父目录。这里没有创建任何文件。`Path.cwd()` 则是程序启动时的工作目录，可能和脚本目录不同。在 IDE 中换一种启动方式就找不到文件，通常就是混淆了这两个目录。实际用户数据应放在合适的数据目录，第 13 章再展开。

## 1.8 本章练习与自检

1. 模仿 `Learner`，写一个 `BookProgress`，保存书名和已读页数，让两个实例互不影响。
2. 在不运行代码前预测 `callback = say_hello` 与 `callback = say_hello()` 各会打印几次、变量里各是什么，再实际验证。
3. 给 `parse_age` 输入 `"18"`、`"abc"`、`"-2"`，观察返回值和异常。另写一个调用方，只捕获 `ValueError` 并打印说明。
4. 把 `BookProgress` 放到一个模块，通过另一个文件导入它，确认导入本身不会执行演示入口。
5. 独立写一个“判断昵称是否有效”的纯函数，约定长度 2～20、去掉两侧空白；先写明输入、输出和失败规则，再写实现。

自检：能否不看原文解释 `self` 是谁、为什么初始化 Qt 基类、为什么回调不带括号、为什么业务规则不一定要写在窗口里？如果只能照抄类的格式，应先完成前两项再进入窗口编程。

下一章将认识 Qt 的整体结构，此时无需背任何控件方法。

---

[返回总目录](00_阅读地图与学习方法.md) · [下一章：认识 Qt 与 PyQt6](02_认识Qt与PyQt6.md)
