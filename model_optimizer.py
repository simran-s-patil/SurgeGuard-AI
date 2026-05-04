import torch
from train_segmentation import UNet

def convert_to_torchscript(model_path, output_path):
    """Convert PyTorch model to TorchScript for faster inference"""
    device = torch.device('cpu')
    model = UNet().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    # Create example input
    example_input = torch.randn(1, 3, 128, 128).to(device)
    
    # Convert to TorchScript
    scripted_model = torch.jit.trace(model, example_input)
    scripted_model.save(output_path)
    print(f"TorchScript model saved to {output_path}")

def convert_to_onnx(model_path, output_path):
    """Convert PyTorch model to ONNX for cross-platform inference"""
    device = torch.device('cpu')
    model = UNet().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    # Create example input
    example_input = torch.randn(1, 3, 128, 128).to(device)
    
    # Export to ONNX
    torch.onnx.export(model, example_input, output_path, 
                      input_names=['input'], output_names=['output'],
                      dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
    print(f"ONNX model saved to {output_path}")

if __name__ == "__main__":
    model_path = "models/unet_surgeguard.pth"
    convert_to_torchscript(model_path, "models/unet_surgeguard.pt")
    convert_to_onnx(model_path, "models/unet_surgeguard.onnx")