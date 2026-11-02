from pathlib import Path
import sys
import shutil
from datetime import datetime
import config

DEFAULT_RULES = {"文本文件": [".txt", ".md"],
         "图片": [".jpg", ".png"],
         "文档": [".pdf", ".xlsx", ".ppt", ".pptx", ".doc", ".docx"],
         "视频&音频": [".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac"],
         "压缩文件": [".zip", ".rar", ".7z"],
         "代码文件": [".py", ".js", ".html", ".css", ".c", ".cpp", ".php"]}

if getattr(sys,'frozen',False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent

data = config.load()
profile = config.get_profile(data)
active_profile_name = config.get_active_profile(data)

history = []

#file是需要操作的文件的绝对地址
#destination是文件移动到的目标目录,但是history里的destination都存的是具体路径

def Unique_File(file, destination):#防止重复文件覆盖

    num = 1#不一样就往文件名后加（1）（2）

    while(1):
        if (destination / f"{file.stem} ({num}){file.suffix}").exists():
            num += 1 
        else:
            return (destination / f"{file.stem} ({num}){file.suffix}")
 
def Cancel_MoveFile(base_dir, on_progress = None):#撤销移动的操作
    error_save = {"成功": 0,
                  "失败": []}
    total = len(history)
    for index,(destination, file, status) in enumerate(reversed(history), start=1): #把目标位置和原文件反过来，从而进行回溯操作
        if status == 'OK' and file.exists():
            bak = destination
            if destination.exists():
                bak = Unique_File(destination, destination.parent) #destination存储的是回溯回去的目标路径
            try:
                shutil.move(str(file), str(bak))#file存储的是回溯的目标文件
            except OSError as e:
                error_save["失败"].append(f"还原文件失败！ {file} -> {bak}: {e}")
                continue
            error_save["成功"] += 1
        if on_progress:
            on_progress(index, total)
    history.clear()
    ROOT = Path(base_dir / "========= 整理后的文件夹 =========")
    for category in ROOT.iterdir():
        try:
            Path(ROOT / category).rmdir()
        except OSError as e:
            pass
    try:
        Path(ROOT).rmdir()
    except OSError as e:
        pass
    if error_save:
        return error_save
#判断分类模式并返回category
def Judge_Mode(file):
    mode = profile.get("mode", "type")
    size_small = profile.get("size_small", 1024)
    size_large = profile.get("size_large", 10485760)
    date = profile.get("date_format", "%Y-%m-%d")
    if mode == 'type':
        file_extension = file.suffix.lower()
        FILE = profile.get("type_rules", DEFAULT_RULES)
        for category, extensions in FILE.items():
            if file_extension in extensions:
                return category
        return None
    elif mode == 'date':
        file_date = datetime.fromtimestamp(file.stat().st_mtime).strftime(date)
        return file_date
    else:
        file_size = file.stat().st_size
        if file_size < size_small:
            category = "Small_Size_File"
        elif file_size > size_large:
            category = "Large_Size_File"
        else:
            category = "Medium_Size_File"
        return category
#计划移动文件
def Plan_Moves(base_dir) -> list:
    Plan_File = []                        #file,destination,status  
    if base_dir.is_dir():
        try:
            for file in base_dir.iterdir():
                if file.is_file():
                    mode = Judge_Mode(file)
                    if not mode:
                        continue
                    category = Path(mode)
                    category_dir = Path(base_dir/ "========= 整理后的文件夹 =========" / category)  #创建的目标类型文件夹路径
                    #记录移动文件
                    destination = category_dir #文件移动的目标目录
                    Plan_File.append((file, destination, "OK")) #移动文件并记录移动过程
            return Plan_File
        except OSError as e:
            raise
    else:
        print(f"访问{base_dir}失败")
        return -1

    
def execute_Move(moves,on_progress = None) -> dict: #实际操作移动文件
    temp_dict = {"success": 0,
                 "failed": []}
    total = len(moves)
    for index, (file, destination, status) in enumerate(moves, start=1):
        if status == "OK":
            category_dir = destination  #创建的目标类型文件夹路径
            #尝试创建文件夹
            try:
                category_dir.mkdir(parents=True,exist_ok=True)
            except OSError as e:
                print(f"创建目录失败！ {category_dir}: {e}")
            #尝试移动文件
            try:
                MoveFile(file, destination) #移动文件并记录移动过程
                temp_dict["success"] += 1
            except OSError as e:
                temp_dict["failed"].append((file, destination))
        else:
            temp_dict["failed"].append((file, destination))
        if on_progress:
            on_progress(index,total)
    return temp_dict

def MoveFile(file, destination):#移动文件
    
    if (destination / file.name).exists():  #如果目标文件已经存在了
        destination_file = Unique_File(file, destination)
    else:
        destination_file = destination / file.name
    try:
        shutil.move(str(file), str(destination_file))
        history.append(( file, destination_file, "OK"))
    except OSError as e:
        history.append(( file, destination_file, "NO"))
        raise
    return
        