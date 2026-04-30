#!/usr/bin/env python3
"""
相机进程清理工具
用于清理卡住的相机进程，解决"相机已被占用"的问题
"""

import subprocess
import sys

def cleanup_camera_processes():
    """清理所有占用相机的Python进程"""
    try:
        # 查找所有Python进程
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ 无法查询进程列表")
            return False

        # 解析进程ID
        lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
        pids = []
        for line in lines:
            if line:
                parts = line.split(',')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    pids.append(pid)

        if not pids:
            print("✅ 没有发现Python进程")
            return True

        print(f"🔍 发现 {len(pids)} 个Python进程")

        # 终止所有Python进程
        killed = 0
        for pid in pids:
            try:
                subprocess.run(['taskkill', '/F', '/PID', pid],
                             capture_output=True, check=True)
                killed += 1
                print(f"  ✓ 已终止进程 PID={pid}")
            except subprocess.CalledProcessError:
                print(f"  ✗ 无法终止进程 PID={pid}")

        print(f"\n✅ 成功清理 {killed}/{len(pids)} 个进程")
        return True

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("相机进程清理工具")
    print("=" * 50)
    print()

    success = cleanup_camera_processes()

    print()
    print("=" * 50)
    if success:
        print("✅ 清理完成，现在可以重新运行程序")
    else:
        print("❌ 清理失败，请手动检查任务管理器")
    print("=" * 50)

    sys.exit(0 if success else 1)
