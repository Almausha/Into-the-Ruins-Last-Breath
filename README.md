
# 🌆 Into the Ruins: Last Breath

**Group 04 — CSE 423 Computer Graphics Lab**

> “Can you escape the ruins?”

---

## 📌 Project Overview

**Into the Ruins: Last Breath** is a 3D survival-action game developed using **PyOpenGL** as part of the CSE 423 Computer Graphics Lab (Lab Assignment 3 constraints).

The game is set in a post-apocalyptic world destroyed by a nuclear explosion. The player must survive toxic air, defeat mutant creatures, and collect all survival kits before the environment becomes uninhabitable.

---

## 🎮 Game Objective

* Collect **all 6 Survival Kits**
* Avoid mutants and environmental hazards
* Manage rising **Air Pollution (Oxygen depletion system)**
* Reach the **Escape Bunker** to win

⚠️ If pollution reaches 100%, hearts drop to 0, or survival fails → GAME OVER

---

## 🗺️ Game World

* World Size: **1200 x 650 units**
* Divided into:

  * **Exploration Zone (Left 2/3)** → ruins, enemies, hidden kits
  * **Safe Zone (Right 1/3)** → Escape bunker
* Environment includes:

  * Ruined buildings
  * Breakable glowing walls
  * Rope/wire barriers
  * Rocks & debris
  * Toxic fog system

---

## ⚙️ Core Mechanics

### ☠️ Survival System

* Air Pollution increases over time
* Reaching 100% → GAME OVER
* Collecting survival kits reduces pollution

### 🔫 Combat System

* Gun (shoot mutants)
* Hammer (break walls)
* Knife (cut ropes)
* Bullet-based enemy elimination

### 👾 Enemy System

* Mutant AI pursues player
* Collision reduces hearts
* Drops ammo/hearts (40% chance)

### 🧱 Interaction System

* Breakable walls (3-hit system)
* Rope barriers
* Hidden collectibles

---

## 🧭 Controls

| Key         | Action                  |
| ----------- | ----------------------- |
| W / S       | Move forward / backward |
| A / D       | Rotate player           |
| Space       | Jump                    |
| 1           | Hammer                  |
| 2           | Knife                   |
| 3           | Gun                     |
| E           | Interact                |
| Left Click  | Shoot                   |
| Arrow Keys  | Camera control          |
| Right Click | Toggle camera view      |
| R           | Restart                 |

---

## 🧑‍🤝‍🧑 Team Members

* **Tabia Sultana Ritu** — 23201510
* **Alma Usha** — 23201452
* **Maisha Jahan Fatima** — 23201158

---

## 🧩 Technical Details

* Built using **PyOpenGL**
* Only allowed primitives used:

  * `glutSolidCube`
  * `gluSphere`
  * `gluCylinder`
  * `GL_QUADS`
* No external physics engine used
* Collision detection: Euclidean distance-based
* Animation system: time-based (`time.time()`)

---

## 💀 Win / Lose Conditions

### 🏆 Win

* Collect all **6 Survival Kits**
* Reach Escape Bunker

### ☠️ Lose

* Air Pollution = 100%
* Hearts = 0
* Miss limit exceeded (10+ bullets)

---

## 📊 Features Summary

* OpenGL-based 3D world
* Dynamic lighting & glow effects
* Enemy AI with pursuit behavior
* Projectile system
* Jump physics system
* Camera switching (1st & 3rd person)
* HUD system (health, ammo, pollution, score)

---

## 🚀 How to Run

```bash
python Into_the_ruins_Project_Group04.py
```

Make sure you have:

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

---

## 📁 Project Structure

```
Into-the-Ruins-Last-Breath/
│
├── Into_the_ruins_Project_Group04.py
├── 3D_OpenGL_Intro.py
├── Hello_openGL.py
├── task1.py
├── task2.py
└── OpenGL/
```

---

## 🧠 Notes

* Designed strictly under **CSE 423 Lab Assignment constraints**
* No external physics or game engines used
* Entire gameplay built using OpenGL primitives and custom logic

---
