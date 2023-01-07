import torch
import torch.nn as nn
from fusionlab.segmentation.base import SegmentationModel
from fusionlab.utils import autopad


class UNet(SegmentationModel):
    def __init__(self, cin, cout):
        super().__init__()
        self.encoder = Encoder(cin, base_dim=64)
        self.bridger = Bridger()
        self.decoder = Decoder(1024, 512)
        self.head = Head(64, cout)


class Encoder(nn.Module):
    def __init__(self, cin, base_dim):
        super().__init__()
        self.pool = nn.MaxPool2d(2, 2)
        self.stage1 = BasicBlock(cin, base_dim)
        self.stage2 = BasicBlock(base_dim, base_dim * 2)
        self.stage3 = BasicBlock(base_dim * 2, base_dim * 4)
        self.stage4 = BasicBlock(base_dim * 4, base_dim * 8)
        self.stage5 = BasicBlock(base_dim * 8, base_dim * 16)

    def forward(self, x):
        s1 = self.stage1(x)
        x = self.pool(s1)
        s2 = self.stage2(x)
        x = self.pool(s2)
        s3 = self.stage3(x)
        x = self.pool(s3)
        s4 = self.stage4(x)
        x = self.pool(s4)
        s5 = self.stage5(x)

        return [s1, s2, s3, s4, s5]


class Decoder(nn.Module):
    def __init__(self, cin, base_dim):
        super().__init__()
        self.d4 = DecoderBlock(cin, cin//2, base_dim)
        self.d3 = DecoderBlock(base_dim, cin//4, base_dim//2)
        self.d2 = DecoderBlock(base_dim//2, cin//8, base_dim//4)
        self.d1 = DecoderBlock(base_dim//4, cin//16, base_dim//8)

    def forward(self, x):
        # print('encoder' , x.shape)
        f1, f2, f3, f4, f5 = x
        for i in x:
            print('f1 ~ f5' , i.shape)
        x = self.d4(f5, f4)
        x = self.d3(x, f3)
        x = self.d2(x, f2)
        x = self.d1(x, f1)
        return x


class Bridger(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        outputs = [nn.Identity()(i) for i in x]
        for o in outputs:
            print("Bridger", o.shape)
        return outputs


class Head(nn.Sequential):
    def __init__(self, cin, cout):
        conv = nn.Conv2d(cin, cout, 1)
        super().__init__(conv)


class BasicBlock(nn.Sequential):
    def __init__(self, cin, cout):
        conv1 = nn.Sequential(
            nn.Conv2d(cin, cout, 3, 1, autopad(3)),
            nn.ReLU(),
        )
        conv2 = nn.Sequential(
            nn.Conv2d(cout, cout, 3, 1, autopad(3)),
            nn.ReLU(),
        )
        super().__init__(conv1, conv2)


class DecoderBlock(nn.Module):
    def __init__(self, c1, c2, cout):
        super().__init__()
        self.up = nn.Upsample(scale_factor=2)
        self.conv = BasicBlock(c1 + c2, cout)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        x = torch.concat([x1, x2], dim=1)
        x = self.conv(x)
        return x


if __name__ == '__main__':
    H = W = 224
    inputs = torch.normal(0, 1, (1, 3, H, W))
    # encoder = Encoder(3, base_dim=16)
    # outputs = encoder(inputs)
    # for o in outputs:
    #     print(o.shape)
    #
    # bridger = Bridger()
    # outputs = bridger(outputs)
    # for o in outputs:
    #     print(o.shape)
    #
    # i1 = torch.normal(0, 1, (1, 16, H, W))
    # i2 = torch.normal(0, 1, (1, 32, H//2, W//2))
    # upblock = DecoderBlock(32, 16, 64)
    # outputs = upblock(i2, i1)
    # print(outputs.shape)
    #
    # i1 = torch.normal(0, 1, (1, 64, 224, 224))
    # i2 = torch.normal(0, 1, (1, 128, 112, 112))
    # i3 = torch.normal(0, 1, (1, 256, 56, 56))
    # i4 = torch.normal(0, 1, (1, 512, 28, 28))
    # i5 = torch.normal(0, 1, (1, 1024, 14, 14))
    # decoder = Decoder(1024, 512)
    # outputs = decoder([i1, i2, i3, i4, i5])
    # print(outputs.shape)
    #
    # head = Head(64, 10)
    # outputs = head(outputs)
    # print(outputs.shape)

    unet = UNet(3, 10)
    outputs = unet(inputs)
    print(outputs.shape)