# SurgeGuard-AI: Silent Bleed Detection System
**Project Status & Development Pipeline**

---

## ✅ Phase 1: Synthetic Data Generation (Completed)
**Goal:** Create a dataset for the AI model without needing real patient data.
* **What we did:** Generated 1000 synthetic surgical frames (`output/images/`) and matching ground-truth masks (`output/ground_truth/`).
* **Why it matters:** It simulates healthy tissue vs. bleeding tissue, allowing us to train and prove the AI works during the hackathon.

## ✅ Phase 2: AI / ML Detection Engine (Completed)
**Goal:** Build the brain of the system to detect occult (hidden) bleeding.
* **Segmentation Model:** Implemented a PyTorch **U-Net** architecture to analyze surgical frames and map out regions of blood.
* **Temporal Logic (`BleedMonitor`):** Created a sliding-window algorithm that analyzes 30 frames at a time. If the red pixel area grows by >15%, it dynamically triggers an `OCCULT_BLEED_ALERT`. 
* **Explainable AI (XAI):** Integrated **Grad-CAM** to generate visual heatmaps. This shows surgeons exactly *where* the AI is looking, building trust in the algorithm's decisions.

## ✅ Phase 3: Cybersecurity & Tamper Prevention (Completed)
**Goal:** Secure the video stream against malicious attacks or interception.
* **LSB Watermarking:** Embedded an invisible, secure text signature (`SURGEGUARD_SECURE_AUTH`) inside the least significant bits of the image pixels to prove the video frame is authentic.
* **Cryptographic Signatures:** Added an `HMAC-SHA256` hash verifier. If an attacker alters even a single pixel of the video, the signature breaks and the system instantly flags `Attack Detected!`.

---

## 🚀 Phase 4: Dashboard & Web Integration (Pending / Next Step)
**Goal:** Tie all the backend engines into a usable product.
* **What we need to do:** Build a UI/API (using Flask, Streamlit, etc.) where a user can stream a surgical video.
* **Features:** The dashboard will run the Phase 2 AI and Phase 3 Security checks in real-time, displaying the alerts, heatmaps, and security status on a single screen for the hackathon judges.
