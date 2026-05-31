# SurgeGuard AI: Real-time Occult Bleed Detection & Cyber-Defense

SurgeGuard AI is a medical-grade computer vision system designed to detect **Occult (Hidden) Internal Bleeding** during laparoscopic surgery. By combining Deep Learning, Explainable AI (XAI), and Cryptographic Cybersecurity, it provides a secure and transparent safety layer for the operating room.

---

## 🛠 Tools & Technologies

SurgeGuard AI utilizes a robust, full-stack architecture to ensure real-time performance and clinical security.

### 🧠 Artificial Intelligence & Vision
*   **PyTorch:** The engine behind our **U-Net** architecture. It handles the complex math of pixel-wise segmentation, allowing the AI to "learn" the visual signature of occult bleeding.
*   **OpenCV (cv2):** The workhorse for real-time video processing. It captures frames, applies the AI's predictions as a HUD overlay, and handles all coordinate-based visual analysis.
*   **NumPy:** Essential for high-speed matrix operations. Every video frame is treated as a 3D matrix where NumPy calculates risk densities and centroid coordinates.
*   **Grad-CAM:** Our "Explainability" tool. It works by back-propagating gradients to the final convolutional layer, creating a heatmap that shows exactly where the AI is focusing its "attention."

### 🔌 Backend & Infrastructure
*   **FastAPI:** A modern, high-speed Python framework. It serves as the gateway for the frontend to upload videos and receive live AI results.
*   **WebSockets:** Instead of slow HTTP requests, we use WebSockets to create a **persistent, bi-directional tunnel**. This allows 30+ frames per second to stream with zero lag.
*   **Uvicorn:** A lightning-fast ASGI server that enables the backend to handle multiple concurrent tasks (Inference, Hashing, and Streaming) without slowing down.

### 💻 Frontend & UI/UX
*   **React + Vite:** A powerful combination for the UI. Vite ensures the dashboard loads instantly, while React manages the complex state of the live HUD and graphs.
*   **Framer Motion:** This library brings the dashboard to life. It handles the "heartbeat" pulse effects, smooth transitions, and the sliding cyber-security alerts.
*   **TailwindCSS:** Provides the "Glassmorphism" design system, creating a premium, state-of-the-art look inspired by high-end surgical equipment.
*   **Lucide React:** A set of pixel-perfect medical and security icons that give the UI its professional clinical aesthetic.

### 🔐 Cybersecurity & Alarms
*   **HMAC-SHA256:** A cryptographic tool that "signs" every frame. It acts like a digital wax seal; if an attacker modifies the video, the signature breaks immediately.
*   **SHA-256:** Used to generate a unique digital fingerprint (Hash) for every frame to ensure 100% data integrity.
*   **Web Audio API:** Used to implement our **Buzzer System**. It generates a synthetic alarm sound directly in the browser, providing an instant auditory warning for the surgeon.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.8+
*   Node.js 16+
*   PyTorch (CUDA recommended but not required)

### 2. Backend Setup
```bash
# Install dependencies
pip install torch torchvision opencv-python numpy fastapi uvicorn websockets

# Start the AI API
python phase4_command_center/backend/main_api.py
```

### 3. Frontend Setup
```bash
cd phase4_command_center/frontend
npm install
npm run dev
```

### 4. Running the Demo
1. Open the dashboard at `http://localhost:5173`.
2. Upload the `output/demo_surgery.mp4` file.
3. Observe the real-time AI segmentation, Grad-CAM heatmaps, and the cryptographic security status.

---

## 🛡 Project Pillars

### ✅ Phase 1: Synthetic Data Generation
Simulates healthy tissue vs. bleeding tissue, allowing us to train and prove the AI works without requiring restricted medical datasets.

### ✅ Phase 2: AI / ML Detection Engine
Uses a **U-Net model** and **Temporal Logic** to monitor cumulative area growth. If suspected bleeding grows by >15% over a 30-frame window, an `OCCULT_BLEED_ALERT` is triggered.

---

## 🧠 Deep Dive: AI/ML Architecture

The core intelligence of SurgeGuard AI is divided into three distinct layers of machine learning logic:

### 1. Semantic Segmentation (The U-Net)
We utilize a **U-Net** architecture, the gold standard for medical image analysis. It uses an **Encoder-Decoder** structure with **Skip Connections**:
*   **Encoder:** Downsamples the surgical frame to capture high-level features (e.g., organ identification).
*   **Decoder:** Upsamples the features to provide pixel-precise localization of bleeding zones.
*   **Skip Connections:** Directly transfer fine-grained spatial information from the encoder to the decoder, ensuring that tiny bleeds are not lost during processing.

### 2. Explainable AI (Grad-CAM)
To ensure clinical trust, we implemented **Grad-CAM (Gradient-weighted Class Activation Mapping)**. 
*   It calculates the importance of each neuron in the final convolutional layer (`u2`) relative to the "Bleeding" prediction.
*   This generates a **Neural Attention Map** (Heatmap) that visually proves to the surgeon why the AI triggered an alert.

### 3. Temporal Intelligence (Sliding Window)
Real-world surgery is dynamic. SurgeGuard uses a **30-frame sliding window** to monitor the **Growth Velocity** of red pixels:
*   **Static Red:** Classified as background tissue/organs.
*   **Expanding Red:** If the pixel count increases by >15% over 1 second, it is classified as an **Active Occult Bleed**.
*   This temporal logic significantly reduces false positives from shadows or smoke.

---

### ✅ Phase 3: Cybersecurity Framework
Protects the video stream using **LSB Watermarking** and **HMAC-SHA256** signatures to detect man-in-the-middle attacks or frame tampering.

### ✅ Phase 4: Command Center Integration
A unified dashboard combining neural streams, biological telemetry, and cyber-defense into a single clinical interface.

---

## 📄 License
This project is for research and hackathon purposes.
