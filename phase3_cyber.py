import cv2
import numpy as np
import hashlib
import hmac
import os
from pathlib import Path
import json

# --- 1. LSB Watermarking ---
def embed_watermark(image_path, out_path, watermark_text="SurgeGuard_Authentic"):
    """Embeds a watermark text into the Least Significant Bits of an image."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read {image_path}")
        return False

    # Convert text to binary string
    binary_text = ''.join([format(ord(char), "08b") for char in watermark_text])
    # Add a delimiter so we know where to stop reading
    binary_text += '1111111111111110' 

    data_len = len(binary_text)
    max_bytes = img.shape[0] * img.shape[1] * 3 // 8

    if data_len > max_bytes:
        print("Error: Image is too small for this watermark.")
        return False

    data_idx = 0
    # Flatten the image to 1D to make iteration easier
    img_1d = img.flatten()

    for i in range(len(img_1d)):
        if data_idx < data_len:
            # Change the least significant bit of the pixel to the watermark bit
            # Clear LSB, then set it to the binary text bit
            img_1d[i] = (img_1d[i] & 254) | int(binary_text[data_idx])
            data_idx += 1
        else:
            break

    # Reshape back to original shape
    watermarked_img = img_1d.reshape(img.shape)
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, watermarked_img)
    return True

def extract_watermark(image_path):
    """Extracts watermark text from the Least Significant Bits of an image."""
    img = cv2.imread(image_path)
    if img is None:
        return None

    img_1d = img.flatten()
    binary_data = ""
    
    for pixel in img_1d:
        binary_data += str(pixel & 1)

    # Split by 8-bits
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        # Check for delimiter '1111111111111110' -> wait, the char is 254
        if decoded_data[-2:] == chr(255) + chr(254): 
            break

    # We manually search for the delimiter pattern in bits instead to be safe
    delimiter = '1111111111111110'
    idx = binary_data.find(delimiter)
    if idx != -1:
        valid_bits = binary_data[:idx]
        extracted = ""
        for i in range(0, len(valid_bits), 8):
            extracted += chr(int(valid_bits[i:i+8], 2))
        return extracted
        
    return "No watermark found or image corrupted."

# --- 2. Cryptographic Signatures (HMAC-SHA256 for Hackathon compatibility) ---
# Note: Using HMAC as a lightweight asymmetric alternative for standard signing
def get_secret_key():
    key_path = "models/secret.key"
    if os.path.exists(key_path):
        with open(key_path, 'rb') as f:
            return f.read()
    else:
        key = os.urandom(32)
        Path(key_path).parent.mkdir(parents=True, exist_ok=True)
        with open(key_path, 'wb') as f:
            f.write(key)
        return key

def generate_secret_key():
    return get_secret_key()

def compute_frame_hash(img_path):
    sha256 = hashlib.sha256()
    with open(img_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def sign_hash(secret_key, frame_hash):
    """Signs a frame hash using HMAC-SHA256."""
    signature = hmac.new(secret_key, frame_hash.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

def verify_signature(secret_key, frame_hash, signature):
    """Verifies the HMAC-SHA256 signature."""
    expected_sig = sign_hash(secret_key, frame_hash)
    return hmac.compare_digest(expected_sig, signature)

# --- Full Pipeline Execution ---
if __name__ == "__main__":
    print("--- Starting Phase 3: Cybersecurity Framework ---")
    
    input_image = "output/images/twin_0000.png"
    watermarked_image = "output/cybersecurity/watermarked_twin_0000.png"
    
    # 1. Embed LSB Watermark
    print("\n[1] LSB Watermarking")
    watermark_msg = "SURGEGUARD_SECURE_AUTH"
    success = embed_watermark(input_image, watermarked_image, watermark_text=watermark_msg)
    if success:
        print(f"[*] Successfully embedded watermark: '{watermark_msg}'")
        print(f"[*] Watermarked image saved to: {watermarked_image}")
        
    # 2. Extract LSB Watermark to prove it works
    extracted = extract_watermark(watermarked_image)
    print(f"[*] Extracted watermark from image: '{extracted}'")
    print(f"[*] Watermark Match: {extracted == watermark_msg}")
    
    # 3. Cryptographic Signatures & Hashing
    print("\n[2] Cryptographic Hashing & Signatures")
    secret_key = generate_secret_key()
    
    # Hash the original vs watermarked
    orig_hash = compute_frame_hash(input_image)
    watermarked_hash = compute_frame_hash(watermarked_image)
    
    print(f"[*] Original Frame Hash:    {orig_hash}")
    print(f"[*] Watermarked Frame Hash: {watermarked_hash}")
    
    # Sign the watermarked frame
    signature = sign_hash(secret_key, watermarked_hash)
    print(f"[*] Generated Cryptographic Signature: {signature}")
    
    # Verify the signature
    is_valid = verify_signature(secret_key, watermarked_hash, signature)
    print(f"[*] Signature Verification Status: {'VALID' if is_valid else 'INVALID'}")
    
    # Simulate a tampering attempt (change the hash slightly)
    print("\n[3] Simulating Tampering Attack")
    fake_hash = watermarked_hash[:-1] + ('a' if watermarked_hash[-1] != 'a' else 'b')
    is_fake_valid = verify_signature(secret_key, fake_hash, signature)
    print(f"[*] Fake/Tampered Hash: {fake_hash}")
    print(f"[*] Tampered Signature Verification Status: {'VALID' if is_fake_valid else 'FAILED (Attack Detected!)'}")
    
    print("\n--- Phase 3 Framework Complete ---")
