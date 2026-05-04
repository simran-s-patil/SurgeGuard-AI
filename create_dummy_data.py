import cv2
import numpy as np
import os
from pathlib import Path

def create_dummy_dataset():
    base_dir = Path("SurgicalBlender/DeBlood_DeSmoke/data")
    trainA = base_dir / "trainA"
    trainB = base_dir / "trainB"
    
    trainA.mkdir(parents=True, exist_ok=True)
    trainB.mkdir(parents=True, exist_ok=True)
    
    # Image 1
    img1_clear = np.ones((256, 256, 3), dtype=np.uint8) * 150 # Grayish tissue
    img1_bloody = img1_clear.copy()
    cv2.circle(img1_bloody, (128, 128), 50, (0, 0, 200), -1) # Bloody spot
    
    # Image 2
    img2_clear = np.ones((256, 256, 3), dtype=np.uint8) * 180 # Lighter tissue
    img2_bloody = img2_clear.copy()
    cv2.rectangle(img2_bloody, (50, 50), (200, 100), (0, 0, 150), -1) # Bloody streak
    
    cv2.imwrite(str(trainA / "img_001.png"), img1_clear)
    cv2.imwrite(str(trainB / "img_001.png"), img1_bloody)
    
    cv2.imwrite(str(trainA / "img_002.png"), img2_clear)
    cv2.imwrite(str(trainB / "img_002.png"), img2_bloody)
    
    # Create healthy background for Member 2
    bg_img = np.ones((512, 512, 3), dtype=np.uint8) * 200
    cv2.putText(bg_img, "Healthy Tissue", (150, 256), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite("healthy_bg.png", bg_img)

    print("Dummy dataset created.")

if __name__ == "__main__":
    create_dummy_dataset()
