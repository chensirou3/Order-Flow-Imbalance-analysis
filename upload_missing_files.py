#!/usr/bin/env python3
"""
智能上传脚本 - 只上传服务器上缺失的文件
"""
import subprocess
import os
import sys

def get_server_files():
    """获取服务器上已有的文件列表"""
    print("正在获取服务器文件列表...")
    cmd = [
        "ssh", "-i", "mishi/lianxi.pem",
        "ubuntu@49.51.244.154",
        "cd Order-Flow-Imbalance-analysis/data/ticks && find . -name '*.parquet' -type f"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return set()
    
    # 处理文件路径，移除开头的 ./
    files = set()
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            files.add(line.strip().lstrip('./'))
    
    print(f"服务器上已有 {len(files)} 个文件")
    return files

def get_local_files():
    """获取本地所有文件列表"""
    print("正在扫描本地文件...")
    files = []
    base_path = "data/ticks"
    
    for root, dirs, filenames in os.walk(base_path):
        for filename in filenames:
            if filename.endswith('.parquet'):
                # 获取相对路径
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, base_path)
                # 转换Windows路径分隔符为Unix格式
                rel_path = rel_path.replace('\\', '/')
                files.append((rel_path, full_path))
    
    print(f"本地共有 {len(files)} 个文件")
    return files

def upload_file(local_path, remote_rel_path):
    """上传单个文件"""
    # 构建远程目录路径
    remote_dir = os.path.dirname(remote_rel_path)
    remote_path = f"~/Order-Flow-Imbalance-analysis/data/ticks/{remote_rel_path}"
    
    # 先创建远程目录
    if remote_dir:
        mkdir_cmd = [
            "ssh", "-i", "mishi/lianxi.pem",
            "ubuntu@49.51.244.154",
            f"mkdir -p ~/Order-Flow-Imbalance-analysis/data/ticks/{remote_dir}"
        ]
        subprocess.run(mkdir_cmd, capture_output=True)
    
    # 上传文件
    scp_cmd = [
        "scp", "-i", "mishi/lianxi.pem",
        local_path,
        f"ubuntu@49.51.244.154:{remote_path}"
    ]
    
    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("智能上传脚本 - 只上传缺失的文件")
    print("=" * 60)
    print()
    
    # 获取服务器和本地文件列表
    server_files = get_server_files()
    local_files = get_local_files()
    
    # 找出缺失的文件
    missing_files = []
    for rel_path, full_path in local_files:
        if rel_path not in server_files:
            missing_files.append((rel_path, full_path))
    
    print()
    print("=" * 60)
    print(f"需要上传 {len(missing_files)} 个文件")
    print(f"已存在 {len(server_files)} 个文件")
    print(f"总共 {len(local_files)} 个文件")
    print("=" * 60)
    print()
    
    if not missing_files:
        print("✅ 所有文件都已上传！")
        return
    
    # 确认上传
    response = input(f"是否开始上传这 {len(missing_files)} 个文件? (y/n): ")
    if response.lower() != 'y':
        print("已取消上传")
        return
    
    # 开始上传
    print()
    print("开始上传...")
    success_count = 0
    fail_count = 0
    
    for i, (rel_path, full_path) in enumerate(missing_files, 1):
        print(f"[{i}/{len(missing_files)}] 上传: {rel_path}...", end=' ')
        
        if upload_file(full_path, rel_path):
            print("✅")
            success_count += 1
        else:
            print("❌")
            fail_count += 1
        
        # 每10个文件显示一次进度
        if i % 10 == 0:
            progress = (i / len(missing_files)) * 100
            print(f"进度: {progress:.1f}% ({success_count} 成功, {fail_count} 失败)")
    
    print()
    print("=" * 60)
    print("上传完成！")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()

