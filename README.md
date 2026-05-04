# SurgeGuard-AI: Silent Bleed Detection System

SurgeGuard-AI is a secure, AI-powered system designed to detect occult (hidden) internal bleeding during laparoscopic surgery. By combining real-time computer vision, explainable AI, and robust cybersecurity measures, it aims to provide surgeons with a reliable and tamper-proof alerting system.

## Project Phases & Status

### ✅ Phase 1: Synthetic Data Generation
**Goal:** Create a dataset for the AI model without needing real patient data.
* **Implementation:** Generated 100 synthetic surgical frames (`output/images/`) and matching ground-truth masks (`output/ground_truth/`).
* **Purpose:** Simulates healthy tissue vs. bleeding tissue, allowing us to train and prove the AI works during the hackathon.

### ✅ Phase 2: AI / ML Detection Engine (Deep Dive)
**Goal:** Build the core intelligence of the system to detect occult (hidden) bleeding in real-time.

1. **The Brain: PyTorch U-Net Segmentation (`UNet`)**
   * **Architecture:** Uses a U-Net model, the industry standard for medical imaging, which compresses images to understand context and expands them to localize features.
   * **Function:** Takes a raw RGB surgical frame and outputs a binary mask. Predictions > 0.5 flag a pixel as "Bleeding/Red".
2. **The Temporal Logic: `BleedMonitor`**
   * **Sliding Window:** Real surgery is noisy. To prevent false positives from flashes or shadows, this module uses a `collections.deque` buffer to track the "Red Pixel" area over the last 30 frames.
   * **Trigger:** It calculates percentage growth between the oldest and newest frame in the buffer. If the suspected bleed area grows by >15% over ~1 second, it triggers an `OCCULT_BLEED_ALERT`.
3. **Building Trust: Explainable AI (`UNetGradCAM`)**
   * **Transparency:** "Black box" AI is dangerous in medicine. Grad-CAM creates a heatmap of the AI's "thoughts."
   * **Mechanism:** It uses PyTorch hooks on the final convolutional layer (`u3`) to perform backpropagation. This calculates which specific pixels mathematically influenced the "bleed" decision the most.
   * **Visualization:** OpenCV colorizes this data (red for high attention) and alpha-blends it directly over the live video so surgeons know exactly *why* the alert fired.

### ✅ Phase 3: Cybersecurity & Tamper Prevention
**Goal:** Secure the video stream against malicious attacks or interception.
* **LSB Watermarking:** Embedded an invisible, secure text signature (`SURGEGUARD_SECURE_AUTH`) inside the least significant bits of the image pixels to prove the video frame is authentic.
* **Cryptographic Signatures:** Added an `HMAC-SHA256` hash verifier. If an attacker alters even a single pixel of the video, the signature breaks and the system instantly flags `Attack Detected!`.

### 🚀 Phase 4: Dashboard & Web Integration (Pending)
**Goal:** Tie all the backend engines into a usable product.
* **Plan:** Build a UI/API (using Flask, Streamlit, etc.) where a user can stream a surgical video.
* **Features:** The dashboard will run Phase 2 AI and Phase 3 Security checks in real-time, displaying alerts, heatmaps, and security status on a single screen for the hackathon judges.

## Technologies Used

* **AI & Machine Learning:** PyTorch (`torch`), U-Net, Grad-CAM
* **Computer Vision:** OpenCV (`cv2`), NumPy (`np`)
* **Cybersecurity:** `hashlib`, `hmac` (SHA-256), LSB Watermarking
* **Data Management:** Python `collections.deque`

## Installation and Setup

1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install torch torchvision opencv-python numpy
   ```
3. Run the individual phase test scripts to verify functionality:
   * `python phase2_aiml.py`
   * `python test_phase2_visual.py`
   * `python phase3_cyber.py`

## License
[Add License Here]
