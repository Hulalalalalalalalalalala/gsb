import os
import requests
import zipfile
import gzip
import shutil
from tqdm import tqdm

def download_file(url, save_path, description="Downloading"):
    """下载文件并显示进度条"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, 'wb') as file, tqdm(
        desc=description,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            pbar.update(size)

def extract_zip(zip_path, extract_dir):
    """解压ZIP文件"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def extract_gz(gz_path, extract_path):
    """解压GZ文件"""
    with gzip.open(gz_path, 'rb') as f_in:
        with open(extract_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

def download_bitcoin_dataset():
    """下载Bitcoin地址风险识别数据集"""
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    # 备选数据源列表 - 使用直接可访问的数据源
    data_sources = [
        {
            "name": "Elliptic Dataset (Direct)",
            "url": "https://raw.githubusercontent.com/ellipticforsch/elliptic-data-set/master/elliptic_bitcoin_dataset.zip",
            "save_path": os.path.join(data_dir, "elliptic_bitcoin_dataset.zip"),
            "extract_dir": os.path.join(data_dir, "elliptic"),
            "description": "Elliptic Bitcoin 风险地址数据集 (直接下载)"
        },
        {
            "name": "Elliptic Dataset (Mirror)",
            "url": "https://www.dropbox.com/s/89e89x3s7c8y2z8/elliptic_bitcoin_dataset.zip?dl=1",
            "save_path": os.path.join(data_dir, "elliptic_bitcoin_dataset.zip"),
            "extract_dir": os.path.join(data_dir, "elliptic"),
            "description": "Elliptic Bitcoin 风险地址数据集 (镜像)"
        }
    ]
    
    download_success = False
    
    for source in data_sources:
        print(f"\n开始下载 {source['description']}...")
        try:
            # 先检查文件是否已存在且大小合理
            if os.path.exists(source['save_path']):
                file_size = os.path.getsize(source['save_path'])
                if file_size > 1000000:  # >1MB，可能是有效数据
                    print(f"文件已存在且大小合理: {file_size} bytes")
                    try:
                        extract_zip(source['save_path'], source['extract_dir'])
                        print(f"解压完成: {source['extract_dir']}")
                        os.remove(source['save_path'])
                        print(f"删除临时文件: {source['save_path']}")
                        download_success = True
                        break
                    except:
                        print(f"文件已损坏，重新下载")
            
            download_file(source['url'], source['save_path'], f"下载 {source['name']}")
            print(f"下载完成: {source['save_path']}")
            
            # 验证下载的文件
            file_size = os.path.getsize(source['save_path'])
            print(f"下载文件大小: {file_size} bytes")
            
            if file_size < 100000:  # <100KB，可能是HTML错误页面
                print(f"文件过小，可能不是有效数据文件")
                os.remove(source['save_path'])
                continue
            
            print(f"解压 {source['name']}...")
            extract_zip(source['save_path'], source['extract_dir'])
            print(f"解压完成: {source['extract_dir']}")
            
            os.remove(source['save_path'])
            print(f"删除临时文件: {source['save_path']}")
            
            download_success = True
            break
            
        except Exception as e:
            print(f"下载失败: {e}")
            if os.path.exists(source['save_path']):
                os.remove(source['save_path'])
            continue
    
    if not download_success:
        print("\n自动下载失败，请手动下载数据:")
        print("1. 访问: https://www.kaggle.com/ellipticco/elliptic-data-set")
        print("2. 下载数据集并解压到 ./data/elliptic 目录")
        print("3. 确保目录包含以下文件:")
        print("   - elliptic_txs_features.csv")
        print("   - elliptic_txs_classes.csv")
        print("   - elliptic_txs_edgelist.csv")
    
    print("\n数据下载和准备完成!")
    print("数据目录结构:")
    for root, dirs, files in os.walk(data_dir):
        level = root.replace(data_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    download_bitcoin_dataset()
