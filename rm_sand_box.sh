#!/bin/bash
# 清空 sand_box 目录

SANDBOX_DIR="sand_box"

# 检查目录是否存在
if [ ! -d "$SANDBOX_DIR" ]; then
    echo "目录 $SANDBOX_DIR 不存在"
    exit 1
fi

# 确认操作
echo "即将清空 $SANDBOX_DIR 目录中的所有文件和文件夹"
read -p "确认继续? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "操作已取消"
    exit 0
fi

# 删除所有文件和子目录，但保留 .git 和目录本身
for item in "$SANDBOX_DIR"/*; do
    if [ "$(basename "$item")" != ".git" ]; then
        rm -rf "$item"
    fi
done

# 同时删除隐藏文件/目录（除了 .git）
for item in "$SANDBOX_DIR"/.*; do
    if [ "$(basename "$item")" != "." ] && [ "$(basename "$item")" != ".." ] && [ "$(basename "$item")" != ".git" ]; then
        rm -rf "$item"
    fi
done

echo "已清空 $SANDBOX_DIR 目录"
