import cv2
import hashlib
import numpy as np


def spatial_frequency_denoise(frame, low_pass_radius=30, gaussian_ksize=(3, 3)):
    """Denoise an incoming frame using spatial blur and frequency low-pass filtering."""
    blurred = cv2.GaussianBlur(frame, gaussian_ksize, 0)
    yuv = cv2.cvtColor(blurred, cv2.COLOR_BGR2YCrCb)
    channels = cv2.split(yuv)
    denoised_channels = []

    for ch in channels:
        f = np.float32(ch) / 255.0
        dft = cv2.dft(f, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)

        rows, cols = f.shape
        crow, ccol = rows // 2, cols // 2
        mask = np.zeros((rows, cols, 2), np.float32)
        cv2.circle(mask, (ccol, crow), low_pass_radius, (1.0, 1.0), thickness=-1)

        dft_shift_filtered = dft_shift * mask
        idft_shift = np.fft.ifftshift(dft_shift_filtered)
        img_back = cv2.idft(idft_shift)
        img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])
        img_back = np.clip(img_back * 255.0, 0, 255).astype(np.uint8)
        denoised_channels.append(img_back)

    denoised = cv2.merge(denoised_channels)
    denoised_bgr = cv2.cvtColor(denoised, cv2.COLOR_YCrCb2BGR)
    return denoised_bgr


def hash_frame(frame):
    """Generate a SHA-256 hash for a frame to detect tampering."""
    frame_bytes = frame.tobytes()
    shape_bytes = f"{frame.shape}".encode("utf-8")
    digest = hashlib.sha256(frame_bytes + shape_bytes).hexdigest()
    return digest


def compute_chained_hash(frame, previous_hash=None):
    """Create a chained frame hash so the stream integrity can be audited."""
    frame_bytes = frame.tobytes()
    if previous_hash is None:
        return hashlib.sha256(frame_bytes).hexdigest()
    return hashlib.sha256(previous_hash.encode("utf-8") + frame_bytes).hexdigest()


def verify_frame_hash(frame, expected_hash):
    """Verify the provided frame against an expected SHA-256 hash."""
    return hash_frame(frame) == expected_hash


class FrameIntegrityMonitor:
    """Monitor video integrity using hashes and chained hash state."""
    def __init__(self):
        self.previous_chain_hash = None

    def update(self, frame, expected_hash=None):
        frame_hash = hash_frame(frame)
        chain_hash = compute_chained_hash(frame, self.previous_chain_hash)
        tampered = False

        if expected_hash is not None:
            tampered = not verify_frame_hash(frame, expected_hash)

        self.previous_chain_hash = chain_hash
        return {
            "frame_hash": frame_hash,
            "chain_hash": chain_hash,
            "tampered": bool(tampered),
        }
