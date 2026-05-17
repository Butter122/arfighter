## Unity AR Fighting Game — Setup Guide

### Prerequisites

- Unity 2022.3 LTS (Android Build Support + ARCore XR Plugin)
- Android device running Android 7.0+ (API 24+) with ARCore support
- Python back-end running on a local machine (see sibling directories)

### Step 1: Create a new Unity project

1. Open Unity Hub → New Project → 3D (URP)
2. Name: `ARFighter`
3. Target platform: Android

### Step 2: Install packages

Open Window → Package Manager, install:

| Package | Version |
|---|---|
| AR Foundation | 5.1.x |
| ARCore XR Plugin | 5.1.x |
| TextMeshPro | (built-in) |
| NativeWebSocket | See below |

**NativeWebSocket** — add via UPM (Window → Package Manager → + → Add from git URL):
```
https://github.com/endel/NativeWebSocket.git#upm
```

### Step 3: Import scripts

Copy all `.cs` files from `UnityARFighter/Assets/Scripts/` into your project's `Assets/Scripts/`, preserving the folder structure:
```
Assets/Scripts/
├── Network/GameClient.cs
├── Game/GameState.cs
├── Game/GameManager.cs
├── Game/FighterController.cs
├── AR/ARPlaneSelector.cs
├── AR/EffectSpawner.cs
└── UI/HUDManager.cs
```

### Step 4: Create Prefabs

**HitEffect.prefab:**
1. Create an empty GameObject
2. Add a ParticleSystem component
3. Set short duration (~0.5s), red/orange color, burst emission
4. Save as `Assets/Prefabs/HitEffect.prefab`

**ProjectileEffect.prefab:**
1. Create an empty GameObject
2. Add a ParticleSystem + TrailRenderer
3. Save as `Assets/Prefabs/ProjectileEffect.prefab`

**Arena.prefab:**
1. Create a plane or flat cube as the arena floor (e.g., 3m × 3m)
2. Add two FighterController GameObjects as children:
   - P1 positioned at (-0.75, 0, 0)
   - P2 positioned at (+0.75, 0, 0)
3. Add two world-space Canvas → Slider health bars above each fighter
4. Save as `Assets/Prefabs/Arena.prefab`

### Step 5: Set up the Main scene

1. Add an **AR Session** and **AR Session Origin** to the hierarchy
2. On AR Session Origin, add:
   - `ARPlaneManager` (Detection Mode: Horizontal)
   - `ARRaycastManager`
   - `ARPlaneSelector` (drag in references)
3. Create a Canvas (Screen Space - Overlay) with:
   - `HUDManager` component
   - `TMP_Text` for winner display (child of a Panel)
   - `TMP_Text` for "Connecting..." overlay
4. Create an empty GameObject, add:
   - `GameClient` (set `_inferenceServerIP` to your Python server's IP)
   - `GameManager`
   - `UnityMainThreadDispatcher`
5. Wire up all `[SerializeField]` references in the Inspector

### Step 6: Build settings

1. File → Build Settings → Android → Switch Platform
2. Player Settings:
   - Minimum API Level: 24
   - Internet Access: Require
   - Camera Permission: Require
   - XR Plug-in Management → ARCore (enabled)
3. Build and Run to your device

### Step 7: Start the back-end

On the server machine (same network):

```bash
# Terminal 1 — Game logic server
cd game_logic
uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 — Inference service
cd inference_service
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Architecture

```
[Android Phone 1]  ──JPEG frames──→  [inference_service:8001]  ──action──→  [game_logic:8000]
[Android Phone 2]  ──JPEG frames──→  [inference_service:8001]  ──action──→  [game_logic:8000]
                                         │                                    │
                                         │                              game state
                                         │                                    │
                                         └──────← broadcast to all ←──────────┘
```
