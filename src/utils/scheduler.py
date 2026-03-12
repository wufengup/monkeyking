import json
import threading
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.config import LLMConfig

class SchedulerManager:
    """
    大圣的时空管理器：
    负责定时任务的持久化存储、后台轮询与执行。
    """
    @property
    def tasks_path(self) -> Path:
        return LLMConfig.CONFIG_DIR / "tasks.json"
    
    def __init__(self, capability_manager=None):
        self.tasks: List[Dict[str, Any]] = []
        self.capability_manager = capability_manager
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        
        self._load_tasks()
        self.start()

    def _load_tasks(self):
        """从磁盘加载任务"""
        if self.tasks_path.exists():
            try:
                with open(self.tasks_path, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print(f"加载任务列表失败: {e}")
                self.tasks = []

    def _save_tasks(self):
        """将任务保存到磁盘"""
        try:
            with self._lock:
                with open(self.tasks_path, "w", encoding="utf-8") as f:
                    json.dump(self.tasks, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存任务列表失败: {e}")

    def start(self):
        """启动后台轮询线程"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台轮询线程"""
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        """后台轮询主循环"""
        while not self._stop_event.is_set():
            now = datetime.now()
            tasks_to_run = []
            
            with self._lock:
                for task in self.tasks:
                    if not task.get("enabled", True):
                        continue
                    
                    try:
                        exec_time = datetime.fromisoformat(task["execute_at"])
                        if now >= exec_time and not task.get("executed", False):
                            tasks_to_run.append(task)
                    except Exception:
                        continue

            for task in tasks_to_run:
                self._execute_task(task)
                task["executed"] = True
                # 如果不是周期性任务，执行完就标记
                # 目前暂只支持单次执行，后续可扩展 cron 表达式
            
            if tasks_to_run:
                self._save_tasks()
                
            time.sleep(10) # 每 10 秒检查一次

    def _execute_task(self, task: Dict[str, Any]):
        """执行具体任务逻辑"""
        task_type = task.get("type")
        content = task.get("content", "")
        
        if task_type == "reminder":
            # 发送系统通知
            title = task.get("title", "大圣定时提醒")
            cmd = [
                "osascript",
                "-e",
                f'display notification "{content}" with title "{title}" sound name "glass"'
            ]
            subprocess.run(cmd)
        
        elif task_type == "tool":
            # 执行法宝方法
            tool_name = task.get("tool_name")
            tool_args = task.get("tool_args", {})
            if self.capability_manager:
                # 在后台异步执行法宝，避免阻塞轮询
                threading.Thread(
                    target=self._run_tool_async,
                    args=(tool_name, tool_args),
                    daemon=True
                ).start()

    def _run_tool_async(self, tool_name: str, tool_args: Dict[str, Any]):
        """异步执行法宝逻辑"""
        try:
            # 找到对应的法宝并运行
            selected_tool = next((t for t in self.capability_manager.tools if t.name == tool_name), None)
            if selected_tool:
                selected_tool.run(tool_args)
        except Exception as e:
            print(f"后台执行法宝 {tool_name} 失败: {e}")

    def add_task(self, task_type: str, execute_at: str, content: str = "", **kwargs) -> str:
        """新增任务"""
        task_id = f"task_{int(time.time())}"
        new_task = {
            "id": task_id,
            "type": task_type,
            "execute_at": execute_at,
            "content": content,
            "enabled": True,
            "executed": False,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }
        with self._lock:
            self.tasks.append(new_task)
        self._save_tasks()
        return task_id

    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        with self._lock:
            return list(self.tasks)

    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        """开启或关闭任务"""
        with self._lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["enabled"] = enabled
                    self._save_tasks()
                    return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            original_len = len(self.tasks)
            self.tasks = [t for t in self.tasks if t["id"] != task_id]
            if len(self.tasks) < original_len:
                self._save_tasks()
                return True
        return False
