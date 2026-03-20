import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class MessageLogger:
    """消息日志记录器，用于保存和对比 Agent 对话的每一步"""

    def __init__(self, log_dir: str = ".logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.step_count = 0

    def start_session(self, task_name: str = None) -> str:
        """开始一个新的会话"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{timestamp}_{task_name}" if task_name else timestamp
        self.current_session = self.log_dir / session_name
        self.current_session.mkdir(exist_ok=True)
        self.step_count = 0

        # 创建会话元数据
        meta = {
            "session_id": session_name,
            "started_at": datetime.now().isoformat(),
            "task": task_name or "untitled"
        }
        (self.current_session / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

        return session_name

    def log_step(self, role: str, content: Any, step_type: str = "message") -> None:
        """
        记录单步消息

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容（可能是字符串、列表或对象）
            step_type: 步骤类型 (message/tool_result/model_response)
        """
        if not self.current_session:
            self.start_session()

        self.step_count += 1
        timestamp = datetime.now().isoformat()

        # 序列化 content
        if isinstance(content, str):
            serialized_content = content
        else:
            # 处理 ContentBlock 对象列表
            serialized_content = self._serialize_content(content)

        step_data = {
            "step": self.step_count,
            "timestamp": timestamp,
            "role": role,
            "type": step_type,
            "content": serialized_content
        }

        # 保存步骤文件
        step_file = self.current_session / f"step_{self.step_count:03d}_{role}.json"
        step_file.write_text(json.dumps(step_data, indent=2, ensure_ascii=False))

        # 同时保存易读的文本版本
        self._save_readable_step(step_data)

    def _serialize_content(self, content: Any) -> Any:
        """序列化复杂内容对象"""
        if hasattr(content, '__iter__') and not isinstance(content, (str, dict)):
            # 处理 ContentBlock 列表
            result = []
            for block in content:
                if hasattr(block, 'model_dump'):
                    result.append(block.model_dump())
                elif hasattr(block, '__dict__'):
                    result.append(vars(block))
                else:
                    result.append(str(block))
            return result
        return str(content)

    def _save_readable_step(self, step_data: Dict) -> None:
        """保存易读的文本格式"""
        readable_file = self.current_session / f"step_{self.step_count:03d}_{step_data['role']}.txt"

        lines = [
            f"{'='*60}",
            f"Step: {step_data['step']} | Role: {step_data['role']} | Type: {step_data['type']}",
            f"Time: {step_data['timestamp']}",
            f"{'='*60}\n",
        ]

        content = step_data['content']
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        lines.append(f"[Text]\n{item.get('text', '')}\n")
                    elif item.get('type') == 'tool_use':
                        lines.append(f"[Tool Use: {item.get('name', 'unknown')}]")
                        lines.append(f"Input: {json.dumps(item.get('input', {}), indent=2)}\n")
                    elif item.get('type') == 'tool_result':
                        lines.append(f"[Tool Result]")
                        lines.append(f"Content: {str(item.get('content', ''))[:500]}\n")
                    else:
                        lines.append(f"[{item.get('type', 'unknown')}]\n{json.dumps(item, indent=2)}\n")
                else:
                    lines.append(str(item))
        else:
            lines.append(str(content))

        readable_file.write_text("\n".join(lines), encoding='utf-8')

    def save_full_conversation(self, messages: List[Dict]) -> None:
        """保存完整的对话历史"""
        if not self.current_session:
            self.start_session()

        full_file = self.current_session / "_full_conversation.json"
        serialized_messages = []

        for msg in messages:
            serialized_messages.append({
                "role": msg["role"],
                "content": self._serialize_content(msg["content"])
            })

        full_file.write_text(
            json.dumps(serialized_messages, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def get_session_path(self) -> Path:
        """获取当前会话路径"""
        return self.current_session


# 全局单例
LOGGER = MessageLogger()


def log_message(role: str, content: Any, step_type: str = "message") -> None:
    """便捷函数：记录单条消息"""
    LOGGER.log_step(role, content, step_type)


def start_logging(task_name: str = None) -> str:
    """便捷函数：开始新会话"""
    return LOGGER.start_session(task_name)


def save_conversation(messages: List[Dict]) -> None:
    """便捷函数：保存完整对话"""
    LOGGER.save_full_conversation(messages)
