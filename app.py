import os
import sys

# Redirect workspace root launcher to bis-compliance-agent/app.py
agent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis-compliance-agent")
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

os.chdir(agent_dir)

# Execute bis-compliance-agent/app.py
with open(os.path.join(agent_dir, "app.py"), encoding="utf-8") as f:
    code = compile(f.read(), os.path.join(agent_dir, "app.py"), "exec")
    exec(code, globals())
