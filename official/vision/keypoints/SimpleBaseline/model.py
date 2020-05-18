import megengine as mge
import megengine.functional as F
import megengine.hub as hub
import megengine.module as M
import official.vision.classification.resnet.model as B

import numpy as np
from config import Config
from functools import partial


class DeconvLayers(M.Module):
    def __init__(self, nf1, nf2s, kernels, num_layers, bias=True, norm=M.BatchNorm2d):
        super(DeconvLayers, self).__init__()
        _body = []
        for i in range(num_layers):
            kernel = kernels[i]
            padding = kernel // 3
            _body += [
                M.ConvTranspose2d(
                    nf1, nf2s[i], kernel, 2, padding, bias=bias
                ),
                norm(nf2s[i]),
                M.ReLU()
            ]
            nf1 = nf2s[i]
        self.body = M.Sequential(*_body)

    def forward(self, x):
        return self.body(x)


class SimpleBaseline(M.Module):
    def __init__(self, backbone, cfg, pretrained=False):

        norm = partial(M.BatchNorm2d, momentum=cfg.bn_momentum)
        self.backbone = getattr(B, backbone)(norm=norm, pretrained=pretrained)
        del self.backbone.fc

        self.cfg = cfg

        self.deconv_layers = DeconvLayers(
            cfg.initial_deconv_channels, 
            cfg.deconv_channels,
            cfg.deconv_kernel_sizes,
            cfg.num_deconv_layers,
            cfg.deconv_with_bias,
            norm
        )
        self.last_layer = M.Conv2d(
            cfg.deconv_channels[-1], 
            cfg.keypoint_num,
            3,
            1, 
            1
        )

        self._initialize_weights()

        self.inputs = {
            "image": mge.tensor(dtype="float32"),
            "heatmap": mge.tensor(dtype="float32"),
            "heat_valid": mge.tensor(dtype="float32")
        }
    
    def _initialize_weights(self):

        for k, m in self.deconv_layers.named_modules():
            if isinstance(m, M.ConvTranspose2d):
                M.init.normal_(m.weight, std=0.001)
                if self.cfg.deconv_with_bias:
                    M.init.zeros_(m.bias)
            if isinstance(m, M.BatchNorm2d):
                M.init.ones_(m.weight)
                M.init.zeros_(m.bias)

        M.init.normal_(self.last_layer.weight, std=0.001)
        M.init.zeros_(self.last_layer.bias)

    def forward(self, x):
        f = self.backbone.extract_features(x)['res5']
        f = self.deconv_layers(f)
        pred = self.last_layer(f)
        return pred
        

@hub.pretrained(
    "https://data.megengine.org.cn/models/weights/simplebaseline50_256x192_0_255_71_2.pkl"
)
def SimpleBaseline_Res50(**kwargs): 
    cfg = Config()
    model = SimpleBaseline(backbone='resnet50', cfg=cfg, **kwargs)
    return model

@hub.pretrained(
    "https://data.megengine.org.cn/models/weights/simplebaseline101_256x192_0_255_72_3.pkl"
)
def SimpleBaseline_Res101(**kwargs):
    
    cfg = Config()
    model = SimpleBaseline(backbone='resnet101', cfg=cfg, **kwargs)
    return model

@hub.pretrained(
    "https://data.megengine.org.cn/models/weights/simplebaseline152_256x192_0_255_72_3.pkl"
)
def SimpleBaseline_Res152(**kwargs):
    
    cfg = Config()
    model = SimpleBaseline(backbone='resnet152', cfg=cfg, **kwargs)
    return model

     


        



    
