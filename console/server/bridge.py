"""Claude Code CLI bridge — spawn `claude --print` and stream JSON events."""
import json
import os
import shutil
import subprocess
from typing import Iterator

from config import PROJECT_ROOT
from sessions import mark_initialized


def _is_ask_user_question(event: dict) -> bool:
    """Detect an AskUserQuestion tool_use in an assistant event.

    When the dnd skill calls this tool in CLI --print mode, the tool returns a
    non-interactive placeholder ("Answer questions?"). The DM then assumes the
    user declined the menu and rambles on with a text fallback in the same
    turn. We avoid that by killing the subprocess the moment we see the
    question — the user answers via the rendered card on the frontend, which
    sends the chosen label as the next prompt.
    """
    if event.get("type") != "assistant":
        return False
    content = event.get("message", {}).get("content")
    if not isinstance(content, list):
        return False
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use" \
                and block.get("name") == "AskUserQuestion":
            return True
    return False


def _resolve_claude() -> str:
    """Find a launchable claude binary.

    On Windows the npm shim is `claude.cmd`; plain `claude` (a shell script
    without extension) is what subprocess tries by default and fails on. We
    prefer .cmd on Windows, else fall back to shutil.which.
    """
    if os.name == "nt":
        cmd_path = shutil.which("claude.cmd")
        if cmd_path:
            return cmd_path
    resolved = shutil.which("claude")
    if resolved:
        return resolved
    raise FileNotFoundError("claude CLI not found on PATH")


def stream_claude(prompt: str, session_id: str, is_new: bool) -> Iterator[dict]:
    """Spawn claude in print mode with stream-json output; yield each event as dict.

    Args:
        prompt: user message to send.
        session_id: UUID for session continuity.
        is_new: True → create session via --session-id. False → resume via --resume.

    Yields:
        dicts parsed from JSONL stdout, plus our own {type: "error"} or
        {type: "done", returncode: int} sentinels.
    """
    claude_bin = _resolve_claude()
    session_flag = "--session-id" if is_new else "--resume"
    cmd = [
        claude_bin,
        "--print",
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "bypassPermissions",
        session_flag, session_id,
        prompt,
    ]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        shell=False,
    )

    assert proc.stdout is not None
    killed_for_question = False
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                yield {"type": "raw", "text": line}
                continue
            yield event
            if _is_ask_user_question(event):
                killed_for_question = True
                proc.kill()
                break
    finally:
        proc.wait()
        if (proc.returncode == 0 or killed_for_question) and is_new:
            mark_initialized()
        if proc.returncode != 0 and not killed_for_question:
            stderr = ""
            if proc.stderr:
                stderr = proc.stderr.read() or ""
            yield {
                "type": "error",
                "returncode": proc.returncode,
                "text": stderr.strip() or f"claude exited with code {proc.returncode}",
            }
        yield {"type": "done", "returncode": proc.returncode}
