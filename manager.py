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

#file是需要操作的文件的绝对地址
#destination是文件移动到的目标目录,但是history里的destination都存的是具体路径

def Unique_File(file, destination):#防止重复文件覆盖

    num = 1#不一样就往文件名后加（1）（2）

    while(1):
        if (destination / f"{file.stem} ({num}){file.suffix}").exists():
            num += 1 
        else:
            return (destination / f"{file.stem} ({num}){file.suffix}")
 
def Cancel_MoveFile(base_dir, on_prgress = None):#撤销移动的操作
    error_save = {"成功": 0,
                  "失败": []}
    total = len(history)
    for index,(destination, file, status) in enumerate(reversed(history), total): #把目标位置和原文件反过来，从而进行回溯操作
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
        if on_prgress:
            on_prgress(index, total)
    history.clear()
    for category in FILE:
        try:
            (base_dir / category).rmdir()
        except OSError as e:
            pass
    if error_save:
        return error_save
def Plan_Moves(base_dir) -> list:#计划移动文件
    Plan_File = []                        #file,destination,status
    if base_dir.is_dir():
        try:
            for file in base_dir.iterdir():
                if file.is_file():

                    file_extension = file.suffix.lower()

                    for category, extensions in FILE.items():
                        if file_extension in extensions:
                            category_dir = base_dir / category  #创建的目标类型文件夹路径
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

def organize_files(base_dir):#对文件进行分类
    moves = Plan_Moves(base_dir)
    if moves == -1:
        return
    if not moves:
        print("没有需要整理的文件")
        return
    for src, dst, status in moves:
        print(f"准备移动{src} -> {dst.name}\\{src.name},状态:{status}")

    f = input("是否确认移动(Y/N):")
    if f.lower() == 'y':
        STATUS = execute_Move(moves)
        print(f"成功移动次数:{STATUS['success']}")
        print(f"失败移动:{STATUS['failed']}")

if __name__ == "__main__":
    while True:
        base_dir = Path('C:/Users/accte/Desktop/test')
        print(f"正在整理文件夹: {base_dir}")
        organize_files(base_dir)
        if history:
            flag = input("是否确认撤回(Y/N):")
            if flag.lower() == 'y':
                Cancel_MoveFile(base_dir)
        input("按任意键继续下一次整理")
        