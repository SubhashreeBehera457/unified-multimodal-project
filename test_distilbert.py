import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

print('=== DistilBERT Test ===')
tokenizer = DistilBertTokenizer.from_pretrained('models/misinformation_filter')
model = DistilBertForSequenceClassification.from_pretrained('models/misinformation_filter')
model.eval()

test_cases = [
    'Heavy rainfall has flooded several roads and residents are being evacuated.',
    'Everyone in the entire city is dead. The government is hiding it.',
    'Huge flood in downtown right now! Cars are floating! Send help!',
]

for text in test_cases:
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        p_genuine = float(probs[0][1].item())
        p_misinfo = float(probs[0][0].item())
        is_genuine = p_genuine >= 0.5
    print(f'Text: "{text[:60]}..."')
    print(f'  P(genuine)={p_genuine:.3f} P(misleading)={p_misinfo:.3f} -> {"GENUINE" if is_genuine else "MISLEADING"}')
    print()
