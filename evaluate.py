from argparse import ArgumentParser
from torchinfo import summary
import torchtext
from torch.utils.data import DataLoader
import transformers
from transformers import DistilBertTokenizer
from ibm_dataset import IBMDebater
import utils
from transformers import DistilBertTokenizer
import torch
from tqdm import tqdm
from config import config
transformers.logging.set_verbosity_error()


def evaluate_pipeline(args):
    checkpoint_path = args.checkpoint_path
    cfg_path = args.cfg_path
    device = args.device
    cfg = config.get_cfg_defaults()
    cfg.merge_from_file(cfg_path)
    cfg.freeze()

    state_dict = torch.load(checkpoint_path, device)
    model = utils.get_model(cfg)
    model.load_state_dict(state_dict)
    summary(model)

    data_path = cfg.DATASET.DATA_PATH
    load_audio = cfg.DATASET.LOAD_AUDIO
    load_text = cfg.DATASET.LOAD_TEXT
    chunk_length = cfg.DATASET.CHUNK_LENGTH
    text_transform = torchtext.transforms.ToTensor()
    tokenizer = DistilBertTokenizer.from_pretrained(cfg.DATASET.TOKENIZER)

    data_test = IBMDebater(data_path, 
                    split='test', 
                    tokenizer=tokenizer, 
                    max_audio_len=chunk_length, 
                    text_transform=text_transform,
                    load_audio=load_audio,
                    load_text=load_text)
    
    model_name = cfg.MODEL.NAME
    if model_name == 'text':
        collate_fn = utils.batch_generator_text
    elif model_name == 'audio':
        collate_fn = utils.batch_generator_wav2vec
    else:
        collate_fn = utils.batch_generator_multimodal

    batch_size = cfg.DATASET.LOADER.BATCH_SIZE
    num_workers = cfg.DATASET.LOADER.NUM_WORKERS
    loader_test = DataLoader(data_test,
                        batch_size=batch_size,
                        shuffle=False,
                        collate_fn=collate_fn,
                        drop_last=False,
                        num_workers=num_workers)
    evaluate(model, loader_test, device)

def evaluate(model, data_loader, device):
    model.eval()
    with torch.no_grad():
        total_acc = 0.0
        total = 0
        results = {}
        model_name = model.__class__.__name__
        for data in tqdm(data_loader):
            if model_name == 'TextModel':
                input_dict = data[0]
                input_dict = {k:input_dict[k].to(device) for k in input_dict.keys()}
                labels = data[1].to(device)
                output = model(**input_dict)
            elif model_name == 'AudioModel':
                waves = data[0].to(device)
                labels = data[1].to(device)
                output = model(waves)
            else:
                input_dict = data[0]
                input_dict = {k:input_dict[k].to(device) for k in input_dict.keys()}
                waves = data[1].to(device)
                labels = data[2].to(device)
                output = model(input_dict, waves)
            output = output.squeeze(1)

            total += labels.size(0)
            acc = ((output > 0).float() == labels).sum().item()
            total_acc += acc
        print('test_accuracy:', total_acc / total)
    return results

    

if __name__ == '__main__':
    args = ArgumentParser()
    args.add_argument('checkpoint_path', help='Path of the checkpoint file')
    args.add_argument('cfg_path', help='Path of the model\'s configuration file')
    args.add_argument('--device', '-d', default='cuda', help='Device name, default is \"cuda\"')
    args = args.parse_args()
    evaluate_pipeline(args)


