## Unity AR Fighting Game — Setup Guide

### Already done (scripts + editor tool)
- All C# scripts copied to `Assets/Scripts/`
- Editor setup tool: `Assets/Editor/ARFighterSetup.cs`
- No external packages needed — uses built-in .NET WebSocket

### Step 1: Open the project
Open `D:\ARfighter` in Unity. Wait for scripts to compile (watch the progress bar).

### Step 2: Run the auto-setup
Go to menu bar → **ARFighter → Setup All**

This creates:
- `Assets/Prefabs/HitEffect.prefab`
- `Assets/Prefabs/ProjectileEffect.prefab`  
- `Assets/Prefabs/Arena.prefab`
- Wires up AR Session, ARPlaneManager, ARRaycastManager, HUD Canvas, Managers

### Step 3: Manual steps (you must do in Unity)

**3a. Set server IP:**
1. Select the `Managers` GameObject in Hierarchy
2. On the GameClient component, set `_serverIP` to your Python machine's LAN IP

**3b. Add fighter visuals (optional):**
- Replace P1_Fighter / P2_Fighter with actual 3D models (capsules work for prototyping)
- Add an Animator component with Idle/Hit/Attack/Block/Dead trigger parameters

**3c. Tap-to-place prompt (optional):**
- Create a TMP_Text or UI panel as the "tap to place" prompt
- Assign it to ARPlaneSelector's `_tapPromptUI` field on AR Session Origin

### Step 4: API Compatibility Level
1. File → Build Settings → Player Settings → Other Settings
2. Set **API Compatibility Level** to `.NET Framework` (needed for System.Net.WebSockets)

### Step 5: Build to Android
1. File → Build Settings → Android → Switch Platform
2. Player Settings:
   - Minimum API Level: 24
   - Internet Access: Require  
   - Camera Permission: Require
   - XR Plug-in Management → ARCore (enabled)
3. Build and Run

### Step 6: Start the back-end
```bash
# Terminal 1 — Game logic server
cd game_logic
uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 — Inference service
cd inference_service
uvicorn main:app --host 0.0.0.0 --port 8001
```
