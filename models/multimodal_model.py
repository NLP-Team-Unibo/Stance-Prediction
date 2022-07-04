import torch
from torch import nn

from models.stance_prediction_module import StancePredictionModule
from models.mult_modules.transformer import TransformerEncoder

def freeze_model(model):
    for param in model.parameters():
        param.requires_grad = False

class MultimodalModel(StancePredictionModule):
    def __init__(
            self, 
            text_model, 
            audio_model, 
            dropout_values = (0.3),
            freeze_text = False,
            freeze_audio = False,
        ):
        """
            Creates a model accepting two inputs of different type: a text sequence, which is passed to the text_model component, and
            a raw audio signal, which is fed as input to the audio_model. Once we obtain two separate embeddings for the inputs, they are 
            concatenated and passed through a linear layer for the classification step.
    
            Parameters
            ----------
            text_model: nn.Module
                The desired TextModel instance; it will be used to process the text portion of the input.
            audio_model: nn.Module
                The desired AudioModel instance; it will be used to process the audio portion of the input.
            dropout_values: tuple of floats
                The value to be used for dropout after concatenating the embeddings of the two modlities. Default to (0.3). 
            freeze_text: bool
                Whether to freeze all the parameters in the text model. Default to False.
            freeze_audio: bool
                Whether to freeze all the parameters in the audio model. Default to False.
            
        """
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

class MultimodalModelMulT(StancePredictionModule):
    def __init__(
            self, 
            text_model, 
            audio_model, 
            dropout_values = (0.3),
            freeze_text = False,
            freeze_audio = False,
        ):
        """
            Creates a model accepting two inputs of different type: a text sequence, which is passed to the text_model component, and
            a raw audio signal, which is fed as input to the audio_model. Once we obtain two separate embeddings for the inputs, they are 
            concatenated and passed through a linear layer for the classification step.
    
            Parameters
            ----------
            text_model: nn.Module
                The desired TextModel instance; it will be used to process the text portion of the input.
            audio_model: nn.Module
                The desired AudioModel instance; it will be used to process the audio portion of the input.
            dropout_values: tuple of floats
                The value to be used for dropout after concatenating the embeddings of the two modlities. Default to (0.3). 
            freeze_text: bool
                Whether to freeze all the parameters in the text model. Default to False.
            freeze_audio: bool
                Whether to freeze all the parameters in the audio model. Default to False.
            
        """
        super(MultimodalModelMulT, self).__init__()
        self.text_model = text_model
        self.audio_model = audio_model

        if freeze_text: freeze_model(self.text_model)
        if freeze_audio: freeze_model(self.audio_model)

        self.crossmodal = TransformerEncoder(embed_dim=768, 
                                             num_heads=8, 
                                             layers=4, 
                                             attn_dropout=0.1, 
                                             relu_dropout=0.1, 
                                             res_dropout=0.1,
                                             embed_dropout=0.25,
                                             attn_mask=True)
        self.relu = nn.ReLU()
        self.classifier = nn.Linear(768, 1)
        #self.dropout = nn.Dropout(p=dropout_values[0])
        
    def forward(self, text_input, audio_input):
        text_sequences = self.text_model(**text_input)
        audio_sequences = self.audio_model(audio_input)
        text_sequences = text_sequences.permute(1, 0, 2)
        audio_sequences = audio_sequences.permute(1, 0, 2)
        x = self.crossmodal(audio_sequences, text_sequences, text_sequences)
        x = x.permute(1, 0, 2)
        x = torch.mean(x, dim=1)
        x = self.relu(x)
        x = self.classifier(x)
        return x


"""from models.text_model_mult import TextModel
from models.audio_model_mult import AudioModel
t = TextModel(return_sequences=True)
a = AudioModel()

m = MultimodalModelMulT(t, a)

import torch
input_id = torch.randint(0, 10, (8, 512))
attention_mask = torch.ones((8, 512))

wav = torch.rand((8, 15*16000))

text = {'input_ids':input_id, 'attention_mask': attention_mask}
x = m(text, wav)
print(x.size())"""