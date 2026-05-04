import cv2
import torch
import numpy as np
from collections import deque
import torch.nn.functional as F
from train_segmentation import UNet

class BleedMonitor:
    def __init__(self, buffer_size=30, alert_threshold=0.15):
        self.buffer_size = buffer_size
        self.alert_threshold = alert_threshold
        self.area_buffer = deque(maxlen=buffer_size)

    def analyze_frame(self, red_pixel_area):
        """
        Analyzes the red pixel area. Returns True if alert is triggered.
        """
        self.area_buffer.append(red_pixel_area)
        
        # We need at least buffer_size frames to compare
        if len(self.area_buffer) == self.buffer_size:
            base_area = self.area_buffer[0]
            current_area = self.area_buffer[-1]
            
            # Avoid division by zero
            if base_area > 0:
                increase = (current_area - base_area) / base_area
                if increase > self.alert_threshold:
                    return True, increase
            elif current_area > 0:
                # If base area was 0 and now we have red pixels, that's definitely an increase
                # We can treat this as an alert if current_area is significant
                # Here we just use a small epsilon or trigger directly
                return True, float('inf')
                
        return False, 0.0


class UNetGradCAM:
    def __init__(self, model, target_layer_name='u3'):
        self.model = model
        self.model.eval()
        self.target_layer_name = target_layer_name
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        # Find the target layer
        target_layer = dict([*self.model.named_modules()]).get(self.target_layer_name)
        if target_layer is None:
            raise ValueError(f"Layer {self.target_layer_name} not found in the model.")
            
        target_layer.register_forward_hook(forward_hook)
        target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor):
        # Forward pass
        output = self.model(input_tensor)
        
        # We want to explain the segmentation mask, so we use the sum of the predicted mask 
        # as the target score (or you could target specific pixels).
        # We'll use the mean of the positive predictions as our target
        pred_mask = torch.sigmoid(output)
        target_score = pred_mask.sum()

        self.model.zero_grad()
        target_score.backward()

        # Pool the gradients across the spatial dimensions
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])

        # Weight the channels by corresponding gradients
        activations = self.activations.detach()
        for i in range(activations.shape[1]):
            activations[:, i, :, :] *= pooled_gradients[i]

        # Average the channels of the activations
        heatmap = torch.mean(activations, dim=1).squeeze()

        # Relu on top of the heatmap
        heatmap = F.relu(heatmap)

        # Normalize the heatmap
        heatmap /= torch.max(heatmap) + 1e-8
        
        return heatmap.cpu().numpy(), pred_mask.detach().cpu().squeeze().numpy()

def overlay_gradcam(image, heatmap, colormap=cv2.COLORMAP_JET):
    # Resize heatmap to match image dimensions
    heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
    
    # Scale to 0-255 and apply colormap
    heatmap_colored = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_colored, colormap)
    
    # Overlay using alpha blend
    overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
    return overlay

if __name__ == "__main__":
    # Example usage / testing
    device = torch.device('cpu')
    model = UNet().to(device)
    
    # Load model if exists
    import os
    if os.path.exists("models/unet_surgeguard.pth"):
        model.load_state_dict(torch.load("models/unet_surgeguard.pth", map_location=device, weights_only=True))
        print("Model loaded successfully.")
    
    grad_cam = UNetGradCAM(model, target_layer_name='u3')
    monitor = BleedMonitor(buffer_size=30, alert_threshold=0.15)
    
    # Simulate a stream of 35 frames
    print("Simulating 35 frames stream...")
    for frame_idx in range(35):
        # Create a dummy image (1, 3, 128, 128)
        dummy_image = torch.rand(1, 3, 128, 128).to(device)
        
        # Get heatmap and prediction
        heatmap, pred_mask = grad_cam.generate_heatmap(dummy_image)
        
        # Calculate red pixel area (using prediction threshold of 0.5)
        # Assuming the U-Net is trained to output 1 for red pixels (bleed)
        binary_mask = (pred_mask > 0.5).astype(np.float32)
        red_pixel_area = np.sum(binary_mask)
        
        # In a real scenario, this area would increase during a bleed.
        # Let's artificially inflate it after frame 25 to trigger the alert
        if frame_idx > 25:
            red_pixel_area += 1000 * (frame_idx - 25)
            
        alert_triggered, increase_pct = monitor.analyze_frame(red_pixel_area)
        
        status = "NORMAL"
        if alert_triggered:
            status = f"OCCULT_BLEED_ALERT (Increase: {increase_pct*100:.1f}%)"
            
        print(f"Frame {frame_idx:02d} | Red Area: {red_pixel_area:7.1f} | Status: {status}")
