"""Codex PreToolUse: route Git calls through the repository commit adapter."""
import json
from pathlib import Path
import re
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKER = '# smilemanager-obsidian-codex-hook'


def response(event):
    if event.get('hook_event_name') != 'PreToolUse':
        return {}
    tool_input = event.get('tool_input', {})
    if not isinstance(tool_input, dict):
        return {}
    command = tool_input.get('command', tool_input.get('cmd', ''))
    if not isinstance(command, str) or MARKER in command:
        return {}
    # Matching quoted text is harmless: the adapter only changes real git commits.
    if not re.search(r'\bgit\b', command) or not re.search(r'\bcommit\b', command):
        return {}
    adapter = shlex.quote(str(ROOT / 'scripts/codex_git.py'))
    prefix = f'{MARKER}\ngit() {{ python3 {adapter} "$@"; }}\n'
    updated = {key: value for key, value in tool_input.items() if key != 'cmd'}
    updated['command'] = prefix + command
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow',
                                   'updatedInput': updated,
                                   'additionalContext': 'Los commits de este repositorio actualizarán el mapa de Obsidian desde el índice de Git.'}}


if __name__ == '__main__':
    print(json.dumps(response(json.load(sys.stdin))))
