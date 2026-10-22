from pathlib import Path
import shutil

FILE = {"文本文件": [".txt", ".md"],
         "图片": [".jpg", ".png"],
         "文档": [".pdf", ".xlsx", ".ppt", ".pptx", ".doc", ".docx"],
         "视频&音频": [".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac"],
         "压缩文件": [".zip", ".rar", ".7z"],
         "代码文件": [".py", ".js", ".html", ".css", ".c", ".cpp", ".php"]}


def organize_files(base_dir):

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

                            if(category_dir / file.name).exists():  #如果目标文件已经存在了
                                if(file.stat().st_size == (destination).stat().st_size):#判断两个文件是不是一样的
                                    print(f"文件已存在且大小相同，跳过移动: {file} -> {destination}")
                                else:
                                    num = 1#不一样就往文件名后加（1）（2）
                                    while(1):
                                        if (category_dir / file.stem + f"({num})" + file.suffix).exists():
                                            num += 1
                                            continue
                                        else:
                                            destination = category_dir / (file.stem + f"({num})" + file.suffix)
                                    print(f"文件已存在但大小不同，移动文件: {file} -> {destination}")
                                    shutil.move(str(file), str(destination))
                            else:
                                shutil.move(str(file), str(destination))
                        except OSError as e:
                            print(f"移动文件失败！ {file} -> {destination}: {e}")
    except OSError as e:
        print("目标文件夹读取失败！", e)

if __name__ == "__main__":

    base_dir = Path('C:/Users/accte/Desktop/CTF')
    print(f"正在整理文件夹: {base_dir}")
    organize_files(base_dir)
    #print(temp)