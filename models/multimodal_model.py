import torch
from torch import nn
from models.stance_prediction_module import StancePredictionModule

def freeze_model(model):
    for param in model.parameters():
        param.requires_grad = False

class MultimodalModel(StancePredictionModule):
    def __init__(
            self, 
            text_model, 
            audio_model, 
            dropout_values = [0.3],
            freeze_text = False,
            freeze_audio = False,
        ):
        super(MultimodalModel, self).__init__()
        self.text_model = text_model
        self.audio_model = audio_model

        if freeze_text: freeze_model(self.text_model)
        if freeze_audio: freeze_model(self.audio_model)
        
        self.dropout = nn.Dropout(p=dropout_values[0])
        self.classifier = nn.Linear(self.text_model.bert_out_dim + self.audio_model.wav2vec2_out_dim, 1)
    
    def forward(self, text_input, audio_input):
        x = self.text_model(**text_input)
        y = self.audio_model(audio_input)
        x = torch.cat([x, y], dim=1)
        x = self.dropout(x)
        x = self.classifier(x)
        return x