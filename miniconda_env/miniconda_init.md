
## 本文件提供了miniconda环境的创建流程以及使用说明

### 0. 查看本地环境

```bash
    conda env list
```

### 1 初始化环境

```bash
    conda create -n EasyFrp_Env python=3.11
```

### 2 激活环境

```bash
    conda activate EasyFrp_Env
```

### 3 安装依赖

#### 安装单个依赖
```bash
conda install PyQt6==6.11.0
conda install PyInstaller==6.21.0
pip install qt-material==2.14
pip install tomlkit==0.15.0
```

#### 安装文件内所有依赖
```bash
pip install -r requirements.txt
```

### 4 导出依赖
```bash
conda env export --no-builds > environment.yml
```

### 5 导入依赖
```bash
conda env create -f environment.yml
```
