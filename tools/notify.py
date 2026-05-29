"""
notify.py — Windows 任务完成弹窗通知

用法:
  python tools/notify.py "Agent 完成"
  python tools/notify.py "Agent 完成" "风云项目"

技术:mshta vbscript popup,5 秒自动消失,不阻塞主流程
"""
import subprocess
import sys


def notify(msg: str, title: str = "风云 ai-wechat-pipeline", timeout: int = 5):
    msg = msg.replace('"', "'").replace("\n", " ")
    title = title.replace('"', "'")
    cmd = (
        f'mshta vbscript:Execute('
        f'"CreateObject(""WScript.Shell"").Popup ""{msg}"", {timeout}, ""{title}"", 64:close"'
        f')'
    )
    subprocess.Popen(cmd, shell=True)


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "任务完成"
    title = sys.argv[2] if len(sys.argv) > 2 else "风云 ai-wechat-pipeline"
    notify(msg, title)
    print(f"通知已弹出: {msg}")
