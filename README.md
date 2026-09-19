# 🕶️ Scribe — Gemini Smart Glasses I/O Module

> **Hackathon Theme: Gemini as an I/O Module**  
> Turning Google Gemini into the sensory cortex and conversational engine for wearable smart glasses.

Scribe transforms camera and microphone sensors into a seamless, **mode-free** smart glasses assistant. There are **no manual modes to switch between**—you simply press a single button (or tap Spacebar) and tell Gemini what to do:
- *"Translate this for me"* → Gemini looks at the camera snapshot, reads foreign signs or menus, translates them, and explains them aloud.
- *"Tell me what's in front of me"* → Gemini scans the room for obstacles, safety hazards, and people, providing concise spoken navigation guidance for visually impaired users.
- *"Are there any steps or obstacles in my path?"* → Immediate hazard detection.
- *"Translate what this person is saying"* → Listens to foreign speech, transcribes, and translates into English audio.
- *"Where is my coffee mug?"* → Direct visual Q&A.

---

## ⚡ How It Works (Simultaneous Vision + Voice)

```
 Wearer Interaction (Single Action Button / Spacebar)
+--------------------------------------------------------+
| 📷 Camera captures snapshot of what you're looking at  |
| 🎙️ Mic records what you ask ("Translate this", etc.)   |
+--------------------------------------------------------+
                           │
                           ▼ HTTP POST /api/interact
+--------------------------------------------------------+
| 🧠 Google Gemini 3.8 Flash (Multimodal Cortex)         |
|    - Understands voice intent & question               |
|    - Analyzes camera frame context                     |
|    - Formulates natural 1-2 sentence answer            |
+--------------------------------------------------------+
                           │
                           ▼ Text-to-Speech
+--------------------------------------------------------+
| 🔊 Gemini 3.1 Flash TTS (Neural Voice)                 |
|    - Speaks answer directly into wearer's earpiece     |
| 🔲 AR Heads-Up Display (HUD) shows live transcript     |
+--------------------------------------------------------+
```

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- Google Gemini API Key ([Get one at Google AI Studio](https://aistudio.google.com/))

### 2. Launch
```bash
# Run the startup script (activates venv & launches server)
./run.sh
```

Or manually:
```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 3. Open the Glasses Simulator
Open **[http://localhost:8000](http://localhost:8000)** in Chrome, Safari, or Edge.
- Allow **Camera** and **Microphone** access.
- Click **⚙ Settings** to enter your `GEMINI_API_KEY` (or set `GEMINI_API_KEY=...` in `.env`).

---

## 🎮 How to Demo & Interact

### 🎙️ Option A: Push-to-Talk (Hold or Tap Spacebar)
1. Point your camera at a room, sign, or person.
2. Hold or tap the **Action Button** (or press **Spacebar**).
3. Speak naturally:
   - *"Translate this for me"*
   - *"Tell me what's in front of me"*
   - *"Is the path ahead clear?"*
   - *"What does that sign say?"*
4. Release or tap again. Gemini immediately speaks the answer into your earpiece while updating the HUD.

### ⚡ Option B: One-Click Demo Scenarios (For Stage Presentations)
If you don't want to speak or don't have physical props on stage, tap any of the built-in preset chips or cards:
- **"Translate this for me"** (Tokyo subway sign in Japanese)
- **"What's in front of me?"** (Living room with coffee table obstacle & cables)
- **"Read this menu"** (French bistro menu with Plat du Jour)
- **"Translate conversation"** (Mandarin audio asking for directions)

---

## � Keyboard Shortcuts

| Key | Action |
|---|---|
| `Spacebar` | **Hold or Tap to Speak** / Send command |
| `R` | **Replay** last spoken audio |
| `1` | Trigger Demo: "Translate this for me" (Japanese Sign) |
| `2` | Trigger Demo: "What's in front of me?" (Obstacle Course) |
| `3` | Trigger Demo: "Read this menu" (French Menu) |
| `4` | Trigger Demo: "Translate conversation" (Mandarin Audio) |

---

## 📁 Project Architecture

```
scribe/
├── main.py                  # FastAPI server (/api/interact endpoint)
├── config.py                # Model configurations (gemini-3.8-flash, gemini-3.1-flash-tts)
├── requirements.txt         # Dependencies
├── run.sh                   # Startup script
├── generate_presets.py      # Sample media generator
├── services/
│   ├── __init__.py
│   └── gemini_service.py    # Multimodal vision + audio cortex & TTS
├── static/
│   ├── index.html           # Smart Glasses AR HUD Interface
│   ├── css/
│   │   └── styles.css       # Neon glassmorphism HUD styles
│   ├── js/
│   │   └── app.js           # Push-to-talk controller & audio visualizer
│   └── presets/             # High-res demo images and audio clips
└── tests/
    └── test_api.py          # Automated test suite
```