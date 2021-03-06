# A generative adversarial network for the MNIST database

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader
import pytorch_lightning as pl

import os
from torchvision.datasets import MNIST
from torchvision import transforms
import matplotlib.pyplot as plt

class Generator(nn.Module):

    def __init__(self):
        super(Generator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(100, 128),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(128, 256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(256, 512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(512, 28*28),
            nn.Tanh(),
        )

    def forward(self, x):
        return self.model(x)

class Discriminator(nn.Module):

    def __init__(self):
        super(Discriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(28*28, 512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.model(x.view(x.size(0), -1))

class GANModel(pl.LightningModule):

    def __init__(self):
        super(GANModel, self).__init__()
        self.generator = Generator()
        self.discriminator = Discriminator()
        self.generated_images = None

    def forward(self, x):
        return self.generator(x)

    def training_step(self, batch, batch_idx, optimizer_idx):
        images, _ = batch
        if optimizer_idx == 0:
            random_noise = torch.randn(images.size(0), 100)
            self.generated_images = self(random_noise)
            y = torch.ones(images.size(0), 1)
            y_pred = self.discriminator(self.generated_images)
            loss = F.binary_cross_entropy(y_pred, y)
            return loss

        if optimizer_idx == 1:
            y_real = torch.ones(images.size(0), 1)
            y_pred_real = self.discriminator(images)
            loss_real = F.binary_cross_entropy(y_pred_real, y_real)

            y_fake = torch.zeros(images.size(0), 1)
            y_pred_fake = self.discriminator(self.generated_images.detach())
            loss_fake = F.binary_cross_entropy(y_pred_fake, y_fake)
            return (loss_real + loss_fake) / 2

    def configure_optimizers(self):
        return [torch.optim.Adam(self.generator.parameters(), lr=0.0002),
                torch.optim.Adam(self.discriminator.parameters(), lr=0.0002)]

    def train_dataloader(self):
        preprocess = transforms.Compose([transforms.ToTensor(),
                                         transforms.Normalize([0.5], [0.5])])
        train_dataset = MNIST(os.getcwd(), train=True, transform=preprocess)
        train_loader = DataLoader(train_dataset, batch_size=100)
        return train_loader

model = GANModel()

trainer = pl.Trainer(max_epochs=200)
trainer.fit(model)

model.eval()

while True:
    random_noise = torch.randn(1, 100)
    y_pred = model(random_noise)
    score = model.discriminator(y_pred).item()
    
    plt.title(f"{score * 100:.1f}")
    plt.imshow(y_pred.detach().view(28, 28))
    plt.show()
