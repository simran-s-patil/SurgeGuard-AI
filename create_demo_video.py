import cv2
import os
from pathlib import Path
from tqdm import tqdm

def create_demo_video(img_dir="output/images", out_path="output/demo_surgery.mp4", fps=10, limit=300):
    img_dir = Path(img_dir)
    images = sorted(list(img_dir.glob("twin_*.png")))
    
    if not images:
        print(f"No images found in {img_dir}")
        return
    
    if limit:
        images = images[:limit]
        
    print(f"Creating video from {len(images)} frames...")
    
    # Read first image to get dimensions
    first_img = cv2.imread(str(images[0]))
    height, width, layers = first_img.shape
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    video = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
    
    for img_path in tqdm(images):
        img = cv2.imread(str(img_path))
        video.write(img)
        
    video.release()
    print(f"Video saved to {out_path}")

if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    create_demo_video()
