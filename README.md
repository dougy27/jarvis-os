Jarvis: The Executive OS

Persistent State. Forensic Logic. Local Sovereignty.

Jarvis is a local-first cognitive architecture designed to function as a long-term executive assistant. Unlike stateless chatbots, Jarvis utilizes a Forensic Probability Model (FPM) to validate intent and a Persistent JSON State to maintain a continuous thread of your life across sessions.

⚡ Core Pillars

Forensic Logic Gate: Uses a weighted sigmoid-based reasoner (fpm_engine.py) to calculate the "Engineered Intent" of a request. It flags high-risk or anomalous commands before they execute.

Persistent JSON Memory: A structured jarvis_state.json tracks your schedule, tasks, and history. It survives resets and bootstraps every session with your "Ground Truth."

Deterministic Skill Routing: A modular JarvisRouter that dispatches intents to specific Python skills (Scheduler, Tasks, Weather, etc.) only after FPM clearance.

Background Executive: A dedicated thread monitors your state.json in real-time, triggering notifications (via ntfy.sh) and local alerts.

Polite Protocol: A refined, formal personality ("Good evening, Master") that prioritizes utility over conversational fluff.

🧠 The FPM Layer

The Forensic Probability Model (FPM) is the digital conscience of Jarvis. It evaluates six key variables (I, A, M, T, Δ, D) to determine if a request is "Routine," "Anomalous," or "High-Risk" before it is ever processed by the LLM.

🛠️ Project Structure

jarvis_main.py: The kernel. Manages the I/O loop and background monitor thread.

jarvis_core.py: The central nervous system (State management & Routing).

fpm_engine.py: The weighted logic gate for security and consistency.

jarvis_state.json: The "Long-term Memory" (Auto-generated).

skills/: Modular capability directory (Briefing, Weather, Scheduler, etc.).

🚀 Installation & Usage

Install Dependencies:

pip install -r requirements.txt


Setup Config: Create a config.yaml and add your ntfy_topic for remote alerts.

Boot:

python jarvis_main.py


🛡️ Privacy Notice

Jarvis is Local-First. Your state.json and conversation history never leave your machine unless you've configured a remote notification service. Ensure you do not commit your personal state.json to public repositories.

📜 License

Distributed under the MIT License. See LICENSE for more information.