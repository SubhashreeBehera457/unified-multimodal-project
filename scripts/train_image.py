import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader
import numpy as np
from PIL import Image
import pandas as pd

class SyntheticCrisisDataset(Dataset):
    def __init__(self, num_samples=500, transform=None):
        self.num_samples = num_samples
        self.transform = transform
        # 0: No Damage, 1: Mild Damage, 2: Severe Damage
        self.labels = np.random.randint(0, 3, size=(num_samples,))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Generate a random noise image (3 channels, 224x224)
        img_data = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        image = Image.fromarray(img_data)
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
            
        return image, torch.tensor(label, dtype=torch.long)

def train_image_model():
    print("Initializing Image Model Training (ResNet50)...")
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    # Check if satellite data exists, else use synthetic for prototype
    dataset_path = "data/satellite"
    
    print("Using synthetic image data generator for conference prototype...")
    train_dataset = SyntheticCrisisDataset(num_samples=400, transform=transform)
    val_dataset = SyntheticCrisisDataset(num_samples=100, transform=transform)
        
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    # Load Pretrained ResNet50
    model = models.resnet50(pretrained=True)
    
    # Freeze earlier layers for faster fine-tuning
    for param in model.parameters():
        param.requires_grad = False
        
    # Replace final layer for our 3 classes
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 3)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)
    
    num_epochs = 2
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        train_acc = 100 * correct / total
        print(f"Epoch [{epoch+1}/{num_epochs}] Loss: {running_loss/len(train_loader):.4f}, Acc: {train_acc:.2f}%")
        
    print("Evaluating Model...")
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
    val_acc = 100 * correct / total
    print(f"Validation Accuracy: {val_acc:.2f}%")
    
    os.makedirs("models/image_model", exist_ok=True)
    torch.save(model.state_dict(), "models/image_model/resnet_damage.pth")
    print("Model saved to models/image_model/resnet_damage.pth")

if __name__ == "__main__":
    train_image_model()
