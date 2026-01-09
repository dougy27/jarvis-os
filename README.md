# 🤵 Jarvis: The Executive OS

**Persistent State • Forensic Logic • Local Sovereignty**

> Jarvis is not a chatbot; it is a **Cognitive Architecture** designed to function as a long-term executive assistant. Built for those who require **privacy and continuity**, Jarvis utilizes a custom **Forensic Probability Model (FPM)** to validate intent and a **Persistent JSON State** to maintain a continuous thread of your life across sessions.

![Jarvis Operational Logic](Test%20Run.gif)

---

## ⚡ Core Pillars

| Feature                     | Description                                                                                                                                              |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧠 **Forensic Logic Gate**  | A weighted sigmoid-based reasoner (`fpm_engine.py`) that calculates "Engineered Intent." It intercepts high-risk or anomalous commands before execution. |
| 💾 **Persistent Memory**    | Structured `jarvis_state.json` tracks your schedule, tasks, and history. It survives resets and bootstraps every session with your "Ground Truth."       |
| 🎯 **Skill Routing**        | A modular router dispatches intents to specific deterministic skills (Scheduler, Tasks, Weather) only after FPM clearance.                               |
| 📡 **Background Executive** | A dedicated thread monitors your life-state in real-time, triggering notifications (via `ntfy.sh`) and local alerts.                                     |
| 🤵 **Polite Protocol**      | A refined, formal personality that prioritizes utility over conversational fluff. `"Standing by. Good evening, Master."`                                 |

---

## 🛡️ The FPM (Forensic Probability Model) Layer

The FPM is the **digital conscience** of Jarvis. It evaluates six key variables to determine if a request is **Routine**, **Anomalous**, or **High-Risk** before it is ever processed by the LLM:

| Variable               | Purpose                                                   |
| ---------------------- | --------------------------------------------------------- |
| **I — Intelligence**   | Complexity and depth of the request split.                |
| **A — Access**         | Proximity to system-critical commands (e.g., Wipe, Root). |
| **M — Material Yield** | Potential for unauthorized data/resource transfer.        |
| **T — Time Pressure**  | Evaluation of urgency or emergency overrides.             |
| **Δ — Dissonance**     | Logical consistency with the established user state.      |
| **D — Detectability**  | Assessment of stealth in the intent.                      |

---

## 📂 Project Structure

```
jarvis-os/
├── jarvis_main.py      # The Kernel: I/O loop & Background Monitor
├── jarvis_core.py      # The Nervous System: State & Routing
├── fpm_engine.py       # The Conscience: Forensic Logic
├── jarvis_ui.py        # The Interface: ANSI Formatting & UI
├── jarvis_state.json   # The Memory: Auto-generated Life Archive (Git Ignored)
└── skills/             # The Muscles: Modular Capability Directory
    ├── briefing.py     # Executive summaries
    ├── conversation.py # Cognitive core (Ollama/Llama)
    └── ...             # Other modular skills
```

---

## 🚀 Installation

### 1. Prerequisites

* Python 3.10+
* Ollama (running `llama3.1:8b`)

### 2. Setup

```bash
# Clone the repository
git clone https://github.com/dougy27/jarvis-os.git
cd jarvis-os

# Install dependencies
python -m pip install -r requirements.txt

# Create your config
# (Ensure config.yaml contains your ntfy_topic and preferred location)
```

### 3. Boot

```bash
python jarvis_main.py
```

---

## 🛡️ Privacy & Sovereignty

Jarvis is **Local-First**. Your state files, conversation history, and logic gates live **on your hardware**.

No telemetry. No cloud-bound memory. You **own the weights, and you own the data**.

---

## ❤️ Support the Development

Building a cognitive architecture from scratch takes **time, coffee, and focus**.
If Jarvis has improved your workflow or provided a safer way to interact with AI, consider supporting the project.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/dougy27)

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---
