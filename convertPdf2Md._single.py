#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Marker PDF 批量转换工具 - 使用 marker_single 逐个转换 (支持缩短文件名)
功能：
1. 扫描输入文件夹中的所有 PDF 文件
2. 使用 shorten_filename 缩短文件名以避免长文件名/路径问题
3. 复制 PDF 到临时文件夹，逐次调用 marker_single 命令行进行转换
4. 输出到指定文件夹，保留原文件名映射记录
"""

import os
import sys
import hashlib
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 解决 Windows 控制台输出中文时的编码问题
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def shorten_filename(original_name: str, max_len: int = 80) -> str:
    """缩短文件名，保留可读性 + 唯一性"""
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix.lower()

    if len(stem) <= max_len:
        return original_name

    prefix = stem[:max_len].strip()
    shortened = f"{prefix}{suffix}"
    return shortened


# ==================== 配置区域 ====================
# 输入 PDF 文件夹路径
INPUT_DIR = r"D:\yongjun\article"
# 输出 Markdown 文件夹路径
OUTPUT_DIR = r"D:\yongjun\article-md-marker"
# ==================================================


def main():
    input_dir = Path(INPUT_DIR).resolve()
    output_dir = Path(OUTPUT_DIR).resolve()

    if not input_dir.exists():
        print(f"错误：输入文件夹不存在 -> {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有 PDF
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("未在输入文件夹中找到 PDF 文件")
        sys.exit(0)

    print(f"找到 {len(pdf_files)} 个 PDF 文件，开始处理...")

    # 自动定位当前虚拟环境下的 marker_single 可执行文件
    marker_single_bin = "marker_single"
    venv_bin_dir = Path(sys.executable).parent
    # Windows 下通常是 Scripts/marker_single.exe 或 Scripts/marker_single
    for name in ["marker_single.exe", "marker_single"]:
        candidate = venv_bin_dir / name
        if candidate.exists():
            marker_single_bin = str(candidate)
            break

    print(f"使用 marker_single 路径: {marker_single_bin}\n")

    mapping = {}  # 原始文件名 -> 缩短后文件名
    temp_dir = output_dir / "_temp_shortened"
    temp_dir.mkdir(exist_ok=True)

    try:
        for i, pdf_path in enumerate(pdf_files, 1):
            original_name = pdf_path.name
            shortened_name = shorten_filename(original_name)
            temp_pdf = temp_dir / shortened_name

            print(f"[{i}/{len(pdf_files)}] 准备转换: {original_name} -> {shortened_name}")

            # 复制并改名到临时目录
            shutil.copy2(pdf_path, temp_pdf)
            mapping[original_name] = shortened_name

            # 构造命令行参数
            # marker_single "<temp_pdf>" --output_dir "<output_dir>" --output_format markdown
            cmd = [
                marker_single_bin,
                str(temp_pdf),
                "--output_dir", str(output_dir),
                "--output_format", "markdown"
            ]

            # 打印友好输出，如果参数中有空格，则加上双引号展示，方便调试
            cmd_str_for_display = ' '.join([f'"{c}"' if ' ' in c else c for c in cmd])
            print(f"执行命令: {cmd_str_for_display}")

            try:
                # shell=True 在 Windows 下有助于正确调用环境中的 command/exe
                result = subprocess.run(cmd, timeout=3600, shell=sys.platform.startswith('win'))
                if result.returncode == 0:
                    print(f"[{i}/{len(pdf_files)}] ✅ 成功转换: {shortened_name}")
                else:
                    print(f"[{i}/{len(pdf_files)}] ❌ 转换失败: {shortened_name}，返回码: {result.returncode}")
            except Exception as e:
                print(f"[{i}/{len(pdf_files)}] ❌ 执行命令时出错: {shortened_name}\n错误信息: {e}")
            print("-" * 50)

        # 保存映射记录
        mapping_file = output_dir / "filename_mapping.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "input_dir": str(input_dir),
                "mapping": mapping
            }, f, ensure_ascii=False, indent=2)
        print(f"\n文件名映射记录已保存: {mapping_file}")

    finally:
        # 可选：清理临时文件目录中的临时 PDF（注释掉下面一行可保留）
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n所有 PDF 转换任务处理完毕！")


if __name__ == "__main__":
    main()

