# NPM AutoCode AI

## 🚀 Quick Start
Install the app:  
[Download Latest Release](https://github.com/sonuramashishnpm/NPM-AutoCode-AI/releases/download/v2.0/NPM_AutoCode_AI.zip)

1. Unzip the file.
2. Run `NPM_AutoCode_AI.exe` (Windows) or `python main.py` (Python 3.12+).
3. Enter your task in the input box (e.g., "Plot a sine wave").
4. Click **Generate & Execute**.
5. Watch logs and progress bar – AI generates, checks safety, executes, and fixes errors if needed.

**Note:** Requires Ollama with models `codellama:7b-instruct` and `qwen2.5-coder:7b`. Run `ollama pull` for them.

## Workflow:-

![Workflow](https://ibb.co/nMSPNJ5h)

## 📖 Project Overview
NPM AutoCode AI is a Python desktop app for automatic code generation and execution using AI. Describe tasks in plain English, and it uses NPMAI (custom LLM tools) to create, validate, and run Python scripts safely.

Built for non-technical users – turns ideas into working code without manual editing.

## ✨ Features
- **Natural Language to Code**: AI generates Python scripts from your description.
- **Safety Check**: Scans code for risks (e.g., file deletions, remote access) before running.
- **Auto-Debug**: If errors happen, AI fixes and retries using error logs.
- **Live Logs & Progress**: See real-time updates in GUI.
- **Dependency Handling**: Installs libraries via `subprocess` in code.
- **Isolated Execution**: Runs in safe namespace to protect your system.
- **Memory Chains**: Remembers task history for better fixes.

## 🔄 How It Works
1. Enter task → AI (`codellama:7b-instruct`) generates code via NPMAI Ollama.
2. Safety AI (`qwen2.5-coder:7b`) reviews: If risky, stops with warning.
3. Execute code in thread → If error, feed back to AI for fix → Retry loop.
4. Success: Logs "Task Completed Successfully".

All in background (QThread) so UI stays responsive. Uses LangChain for prompts.

## 🛠️ Tech Details
- **Language**: Python 3.12+
- **GUI**: PySide6 (QWidget, QThread, etc.)
- **AI**: npmai.Ollama + Memory; LangChain Core for prompts/parsers.
- **Execution**: `exec()` in custom globals dict with error capture.

## 👨‍💻 Developer
**Sonu Kumar Ramashish** (a.k.a. Bihar Viral Boy)  
- Age: 14 | Student | TEDx Speaker | AI & Software Developer | DevOps Enthusiast  
- Reach: 410K+ Facebook followers  
- Location: Kota, Rajasthan  

Part of NPMAI ecosystem for AI automation tools.

## 🤝 Contributing
Fork, add features (e.g., more models), and PR. License: MIT.

Star if useful! 🚀
