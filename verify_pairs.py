import os
import cv2
from pathlib import Path

def verify_pairs(dir_a, dir_b, report_path="mismatch_report.txt"):
    path_a = Path(dir_a)
    path_b = Path(dir_b)

    if not path_a.exists() or not path_b.exists():
        print(f"Error: One or both directories do not exist: {path_a}, {path_b}")
        return

    files_a = set([f.name for f in path_a.iterdir() if f.is_file()])
    files_b = set([f.name for f in path_b.iterdir() if f.is_file()])

    only_in_a = files_a - files_b
    only_in_b = files_b - files_a
    common_files = files_a.intersection(files_b)

    mismatches = []

    print(f"Found {len(common_files)} common files.")
    if only_in_a:
        print(f"Warning: {len(only_in_a)} files only in {dir_a}")
    if only_in_b:
        print(f"Warning: {len(only_in_b)} files only in {dir_b}")

    for filename in common_files:
        img_a_path = str(path_a / filename)
        img_b_path = str(path_b / filename)

        img_a = cv2.imread(img_a_path)
        img_b = cv2.imread(img_b_path)

        if img_a is None:
            mismatches.append(f"Cannot read image: {img_a_path}")
            continue
        if img_b is None:
            mismatches.append(f"Cannot read image: {img_b_path}")
            continue

        if img_a.shape != img_b.shape:
            mismatches.append(f"Dimension mismatch for {filename}: {dir_a} shape {img_a.shape} vs {dir_b} shape {img_b.shape}")

    with open(report_path, "w") as f:
        f.write("=== Data Verification Report ===\n\n")
        f.write(f"Total files in {dir_a}: {len(files_a)}\n")
        f.write(f"Total files in {dir_b}: {len(files_b)}\n")
        f.write(f"Common files: {len(common_files)}\n\n")
        
        if only_in_a:
            f.write("Files only in A:\n")
            for name in only_in_a:
                f.write(f" - {name}\n")
            f.write("\n")
            
        if only_in_b:
            f.write("Files only in B:\n")
            for name in only_in_b:
                f.write(f" - {name}\n")
            f.write("\n")
            
        f.write("Dimension Mismatches or Read Errors:\n")
        if not mismatches:
            f.write(" - None detected. All common files match perfectly.\n")
        else:
            for m in mismatches:
                f.write(f" - {m}\n")

    print(f"Verification complete. Report saved to {report_path}")

if __name__ == "__main__":
    trainA_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainA"
    trainB_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainB"
    verify_pairs(trainA_dir, trainB_dir)
