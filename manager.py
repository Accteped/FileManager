from pathlib import Path
import os 
import shutil

FILE = {"文本文件": [".txt", ".md"],
         "图片": [".jpg", ".png"],
         "文档": [".pdf", ".xlsx", ".ppt", ".pptx", ".doc", ".docx"],
         "视频&音频": [".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac"],
         "压缩文件": [".zip", ".rar", ".7z"],
         "代码文件": [".py", ".js", ".html", ".css", ".c", ".cpp", ".php"]}

history = []

def Unique_File(file, destination):#防止重复文件覆盖

    num = 1#不一样就往文件名后加（1）（2）

    while(1):
        if (destination / f"{file.name} ({num}){file.suffix}").exists():
            num += 1 
        else:
            return (destination / f"{file.name} ({num}){file.suffix}")

def Cancel_MoveFile(base_dir):#撤销移动的操作
    for file, destination, status in reversed(history):
        if status == 'OK':
            if file.exists():
                file = Unique_File(destination, file)
            try:
                shutil.move(str(destination), str(file))
            except OSError as e:
                print(f"还原文件失败！ {destination} -> {file}: {e}")
    history.clear()
    for category in FILE:
        d = base_dir / category
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def MoveFile(file, destination):#移动文件
    try:
        if destination.exists():  #如果目标文件已经存在了
            destination = Unique_File(file, destination)
            shutil.move(str(file), str(destination))
        else:
            shutil.move(str(file), str(destination))
        history.append(( file, destination, "OK"))
    except OSError as e:
        history.append(( file, destination, "OK"))
        raise
    return

def organize_files(base_dir):#对文件进行分类

    if not base_dir.is_dir():
        print("目标文件夹不存在或者不是文件夹")
        return
    try:
        for file in base_dir.iterdir():
            if file.is_file():

                file_extension = file.suffix.lower()

                for category, extensions in FILE.items():
                    if file_extension in extensions:
                        category_dir = base_dir / category  #创建的目标类型文件夹路径
                        #尝试创建文件夹
                        try:
                            category_dir.mkdir(parents=True,exist_ok=True)
                        except OSError as e:
                            print(f"创建目录失败！ {category_dir}: {e}")
                        #尝试移动文件
                        try:
                            destination = category_dir / file.name #文件移动的目标路径
                            MoveFile(file, destination) #移动文件并记录移动过程
                        except OSError as e:
                            print(f"移动文件失败！ {file} -> {destination}: {e}")
    except OSError as e:
        print("目标文件夹读取失败！", e)

if __name__ == "__main__":
    while True:
        base_dir = Path('C:/Users/accte/Desktop/test')
        print(f"正在整理文件夹: {base_dir}")
        organize_files(base_dir)
        Cancel_MoveFile(base_dir)
        