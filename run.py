import argparse
import yaml
from util import printl, printl_file
from util import prepare_saving_dir
import torch
import torch.nn as nn
import numpy as np
from box import Box
import sys
from data import get_dataloader
from model import prepare_models
from cosine_annealing_warmup import CosineAnnealingWarmupRestarts
from tqdm import tqdm


def main(parse_args, configs):
    torch.cuda.empty_cache()
    curdir_path, result_path, checkpoint_path, log_path, config_path = prepare_saving_dir(parse_args)
    """
    Banner
    """
    printl(f"{'=' * 128}")
    printl("               ______   ______   .__   __. .___________..______          ___   .___________.  ______ .______      ")
    printl("              /      | /  __  \  |  \ |  | |           ||   _  \        /   \  |           | /      ||   _  \     ")
    printl("             |  ,----'|  |  |  | |   \|  | `---|  |----`|  |_)  |      /  ^  \ `---|  |----`|  ,----'|  |_)  |    ")
    printl("             |  |     |  |  |  | |  . `  |     |  |     |      /      /  /_\  \    |  |     |  |     |      /     ")
    printl("             |  `----.|  `--'  | |  |\   |     |  |     |  |\  \----./  _____  \   |  |     |  `----.|  |\  \----.")
    printl("              \______| \______/  |__| \__|     |__|     | _| `._____/__/     \__\  |__|      \______|| _| `._____|")
    printl()
    """
    Description
    """
    printl(f"{'=' * 128}", log_path=log_path)
    printl(configs.description, log_path=log_path)
    """
    CMD
    """
    printl(f"{'=' * 128}", log_path=log_path)
    command = ''.join(sys.argv)
    printl(f"Executed with: python {command}", log_path=log_path)
    """
    Directories
    """
    printl(f"{'=' * 128}", log_path=log_path)
    printl(f"Result Directory: {result_path}", log_path=log_path)
    printl(f"Checkpoint Directory: {checkpoint_path}", log_path=log_path)
    printl(f"Log Directory: {log_path}", log_path=log_path)
    printl(f"Config Directory: {config_path}", log_path=log_path)
    printl(f"Current Working Directory: {curdir_path}", log_path=log_path)
    """
    Configration File
    """
    printl(f"{'=' * 128}", log_path=log_path)
    printl_file(parse_args.config_path, log_path=log_path)
    # """
    # Random Seed
    # """
    # if type(configs.fix_seed) == int:
    #     torch.manual_seed(configs.fix_seed)
    #     torch.random.manual_seed(configs.fix_seed)
    #     np.random.seed(configs.fix_seed)
    #     printl(f"{'=' * 128}", log_path=log_path)
    #     printl(f'Random seed set to {configs.fix_seed}.', log_path=log_path)
    """
    Dataloader
    """
    printl(f"{'=' * 128}", log_path=log_path)
    dataloaders = get_dataloader(configs)
    printl(f'Number of Steps for Training Data: {len(dataloaders["train_loader"])}', log_path=log_path)
    printl(f'Number of Steps for Validation Data: {len(dataloaders["valid_loader"])}', log_path=log_path)
    # printl(f'Number of Steps for Test Data: {len(dataloaders_dict["test"])}', log_path=log_path)
    printl("Data loading complete.", log_path=log_path)
    """
    Model
    """
    printl(f"{'=' * 128}", log_path=log_path)
    encoder, projection_head = prepare_models(configs, log_path=log_path)
    device = torch.device("cuda")
    encoder.to(device)
    projection_head.to(device)
    printl("ESM-2 encoder & projection head initialization complete.", log_path=log_path)
    """
    Tokenizer, Optimizer, Schedular, Criterion
    """
    alphabet = encoder.alphabet
    tokenizer = alphabet.get_batch_converter()  # truncation_seq_length=512?
    optimizer = torch.optim.AdamW(
        list(encoder.parameters()) + list(projection_head.parameters()),
        lr=float(configs.max_learning_rate),
        betas=(float(configs.optimizer_beta1), float(configs.optimizer_beta2)),
        weight_decay=float(configs.optimizer_weight_decay),
        eps=float(configs.optimizer_eps)
    )
    schedular = CosineAnnealingWarmupRestarts(
        optimizer,
        first_cycle_steps=int(configs.schedular_first_cycle_steps),
        max_lr=float(configs.max_learning_rate),
        min_lr=float(configs.min_learning_rate),
        warmup_steps=int(configs.schedular_warmup_epochs),
        gamma=float(configs.schedular_gamma)
    )
    if configs.contrastive_mode == "Triplet":
        criterion = nn.TripletMarginLoss(margin=1, reduction='mean')
        printl("Tokenizer, Optimizer, Schedular, Criterion initialization complete.", log_path=log_path)
        printl(f"{'=' * 128}", log_path=log_path)
        for epoch in range(1, configs.epochs + 1):
            train_triplet(encoder, projection_head, epoch, dataloaders["train_loader"], tokenizer, optimizer, schedular, criterion, log_path)

    else:
        raise ValueError("Wrong contrastive mode specified.")

    return


def train_triplet(encoder, projection_head, epoch, train_loader, tokenizer, optimizer, schedular, criterion, log_path):
    device = torch.device("cuda")

    encoder.train()
    projection_head.train()

    total_loss = 0

    progress_bar = tqdm(enumerate(train_loader), total=len(train_loader), desc=f"Epoch [{epoch}]")

    for batch, data in progress_bar:
        epitope_list = data['anchor_epitope']
        anchor_list = data['anchor_TCR']
        positive_list = data['positive_TCR']
        negative_list = data['negative_TCR']

        anchor_seq_batch = [(epitope_list[i], str(anchor_list[i])) for i in range(len(epitope_list))]
        _, _, anchor_tokens = tokenizer(anchor_seq_batch)

        positive_seq_batch = [(epitope_list[i], str(positive_list[i])) for i in range(len(epitope_list))]
        _, _, positive_tokens = tokenizer(positive_seq_batch)

        negative_seq_batch = [(epitope_list[i], str(negative_list[i])) for i in range(len(epitope_list))]
        _, _, negative_tokens = tokenizer(negative_seq_batch)


        anchor_emb = projection_head(encoder(anchor_tokens.to(device)).mean(dim=1))
        positive_emb = projection_head(encoder(positive_tokens.to(device)).mean(dim=1))
        negative_emb = projection_head(encoder(negative_tokens.to(device)).mean(dim=1))

        loss = criterion(anchor_emb, positive_emb, negative_emb)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        schedular.step()

        total_loss += loss.item()

        progress_bar.set_postfix(loss=loss.item())

    avg_loss = total_loss / len(train_loader)
    printl(f"Epoch [{epoch}] completed. Average Loss: {avg_loss:.4f}", log_path=log_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ContraTCR: A tool for training and predicting TCR-epitope binding using '
                                                 'contrastive learning.')
    parser.add_argument("--config_path", help="Path to the configuration file. Defaults to "
                                              "'./config/default/config.yaml'. This file contains all necessary "
                                              "parameters and settings for the operation.",
                        default='./config/default/config.yaml')
    parser.add_argument("--mode", help="Operation mode of the script. Use 'train' for training the model and "
                                       "'predict' for making predictions using an existing model. Default mode is "
                                       "'train'.", default='train')
    parser.add_argument("--result_path", default='./result/default/',
                        help="Path where the results will be stored. If not set, results are saved to "
                             "'./result/default/'. This can include prediction outputs or saved models.")
    parser.add_argument("--resume_path", default=None,
                        help="Path to a previously saved model checkpoint. If specified, training or prediction will "
                             "resume from this checkpoint. By default, this is None, meaning training starts from "
                             "scratch.")

    parse_args = parser.parse_args()

    config_path = parse_args.config_path
    with open(config_path) as file:
        config_dict = yaml.full_load(file)
        configs = Box(config_dict)

    main(parse_args, configs)
