import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

class InputSanitizer:
    def __init__(self, noise_threshold=100.0, blur_threshold=50.0):
        """
        Initialize sanitizer with thresholds
        noise_threshold: Laplacian variance threshold for noise detection
        blur_threshold: Threshold for blur detection
        """
        self.noise_threshold = noise_threshold
        self.blur_threshold = blur_threshold

    def detect_high_frequency_noise(self, image):
        """
        Detect high-frequency noise using Laplacian variance
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var, laplacian_var > self.noise_threshold

    def detect_blur(self, image):
        """
        Detect blur using Laplacian variance (lower variance = more blur)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var, laplacian_var < self.blur_threshold

    def detect_artifacts(self, image):
        """
        Detect various image artifacts that might indicate tampering
        """
        artifacts = {}

        # Check for unusual color distributions
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])

        # Check for saturated colors (potential adversarial patterns)
        artifacts['high_saturation'] = np.max(hist_s) > 10000

        # Check for unusual brightness patterns
        artifacts['extreme_brightness'] = np.mean(hist_v) > 200 or np.mean(hist_v) < 50

        return artifacts

    def sanitize_image(self, image_path):
        """
        Sanitize a single image and return security assessment
        """
        image = cv2.imread(str(image_path))
        if image is None:
            return {"valid": False, "reason": "Cannot load image"}

        # Detect noise
        noise_var, has_noise = self.detect_high_frequency_noise(image)

        # Detect blur
        blur_var, is_blur = self.detect_blur(image)

        # Detect artifacts
        artifacts = self.detect_artifacts(image)

        # Overall assessment
        security_score = 1.0
        issues = []

        if has_noise:
            security_score -= 0.3
            issues.append("High-frequency noise detected")

        if is_blur:
            security_score -= 0.2
            issues.append("Image appears blurred")

        if any(artifacts.values()):
            security_score -= 0.2
            issues.extend([k for k, v in artifacts.items() if v])

        security_score = max(0.0, security_score)

        result = {
            "valid": security_score > 0.5,
            "security_score": security_score,
            "issues": issues,
            "noise_variance": noise_var,
            "blur_variance": blur_var,
            "artifacts": artifacts
        }

        return result

    def sanitize_batch(self, image_dir, output_report="sanitization_report.json"):
        """
        Sanitize a batch of images
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            print(f"Image directory {image_dir} not found.")
            return

        image_files = list(image_dir.glob("*.png"))
        results = {}

        for img_path in image_files:
            result = self.sanitize_image(img_path)
            results[img_path.name] = result

        # Save report
        import json
        with open(output_report, 'w') as f:
            json.dump(results, f, indent=2)

        # Summary
        valid_count = sum(1 for r in results.values() if r['valid'])
        total_count = len(results)

        print(f"Sanitization complete: {valid_count}/{total_count} images passed security checks")
        print(f"Report saved to {output_report}")

        return results

def visualize_sanitization(image_path):
    """
    Visualize sanitization analysis
    """
    sanitizer = InputSanitizer()

    image = cv2.imread(str(image_path))
    if image is None:
        print("Cannot load image")
        return

    result = sanitizer.sanitize_image(image_path)

    # Create visualization
    plt.figure(figsize=(12, 4))

    plt.subplot(1, 3, 1)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title('Original Image')
    plt.axis('off')

    # Show Laplacian for noise detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    plt.subplot(1, 3, 2)
    plt.imshow(np.abs(laplacian), cmap='gray')
    plt.title('.2f')
    plt.axis('off')

    # Show HSV analysis
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    plt.subplot(1, 3, 3)
    plt.imshow(hsv[:, :, 1], cmap='plasma')  # Saturation channel
    plt.title('Saturation Channel')
    plt.axis('off')

    plt.tight_layout()
    plt.savefig('sanitization_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("Security Assessment:")
    print(f"Valid: {result['valid']}")
    print(".4f")
    print(f"Issues: {result['issues']}")

if __name__ == "__main__":
    # Test on a sample image
    test_image = "output/images/twin_0000.png"
    if Path(test_image).exists():
        visualize_sanitization(test_image)

        # Batch sanitization
        sanitizer = InputSanitizer()
        sanitizer.sanitize_batch("output/images")
    else:
        print(f"Test image {test_image} not found.")</content>
<parameter name="filePath">e:\BTech CS with AI\OvernightHackathonDhi\input_sanitizer.py