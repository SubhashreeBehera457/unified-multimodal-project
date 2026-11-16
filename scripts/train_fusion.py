import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from transformers import DistilBertModel, DistilBertTokenizer
import numpy as np
from PIL import Image

class SyntheticMultimodalDataset(Dataset):
    def __init__(self, num_samples=200):
        self.num_samples = num_samples
        self.labels = np.random.randint(0, 3, size=(num_samples,))
        self.texts = [
            "Severe flooding in the streets, cars are submerged." if l == 2 else 
            "A bit of water on the road, mild issues." if l == 1 else 
            "Everything is fine, clear skies." 
            for l in self.labels
        ]
        
    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Generate dummy image
        img_data = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        image = Image.fromarray(img_data)
        
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        image_tensor = transform(image)
        text = self.texts[idx]
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        
        return image_tensor, text, label

class EarlyFusionModel(nn.Module):
    def __init__(self, num_classes=3):
        super(EarlyFusionModel, self).__init__()
        
        # Vision Backbone
        self.resnet = models.resnet50(pretrained=True)
        # Remove the classification head
        self.resnet = nn.Sequential(*list(self.resnet.children())[:-1])
        
        # Text Backbone
        self.distilbert = DistilBertModel.from_pretrained('distilbert-base-uncased')
        
        # Freeze backbones
        for param in self.resnet.parameters():
            param.requires_grad = False
        for param in self.distilbert.parameters():
            param.requires_grad = False
            
        # Fusion Head (2048 from ResNet + 768 from DistilBERT = 2816)
        self.fc1 = nn.Linear(2816, 512)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(512, num_classes)
        
    def forward(self, image, input_ids, attention_mask):
        # Vision features
        img_features = self.resnet(image).squeeze(-1).squeeze(-1) # (Batch, 2048)
        
        # Text features (CLS token)
        text_outputs = self.distilbert(input_ids=input_ids, attention_mask=attention_mask)
        text_features = text_outputs.last_hidden_state[:, 0, :] # (Batch, 768)
        
        # Concat
        fused = torch.cat((img_features, text_features), dim=1) # (Batch, 2816)
        
        # Classification
        x = self.fc1(fused)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

def train_fusion():
    print("Initializing Early Fusion Multimodal Network...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    dataset = SyntheticMultimodalDataset(num_samples=200)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    model = EarlyFusionModel(num_classes=3).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print("Training Fusion Head (Backbones frozen)...")
    model.train()
    for epoch in range(3):
        running_loss = 0.0
        for images, texts, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)
            
            tokens = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
            
            optimizer.zero_grad()
            outputs = model(images, tokens['input_ids'], tokens['attention_mask'])
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
        print(f"Epoch [{epoch+1}/3] Loss: {running_loss/len(dataloader):.4f}")
        
    os.makedirs("models/fusion_model", exist_ok=True)
    torch.save(model.state_dict(), "models/fusion_model/early_fusion_head.pth")
    print("Fusion model saved successfully!")

if __name__ == "__main__":
    train_fusion()
