# 保存着所有模型结构的定义，供Players.py里的CNNPlayer调用

import torch.nn as nn
from torchvision.models.resnet import BasicBlock
import torch
from typing import Literal, Any
import numpy as np



class MahjongCNN_v1(nn.Module):
    """麻将卷积神经网络模型，包含输入层、卷积层、全连接层等结构
    RL模型输入53维向量，包括：
        自己手牌 * 4   one hot
        自己暗杠 * 1   one hot
        每个人动作(吃 * 1 + 碰 * 1 + 明杠 * 1) * 4 个玩家  one hot
        每个人依序弃牌历史 (4 + 2) * 4  one hot
        剩余牌 * 4  one hot
        财神牌 * 1  one hot
        阶段层 * 4  one hot
        是否庄家 * 1  one hot
        底分 * 1  (代表当前底分，float，1、2、3、4)
        剩余牌层 * 1 （代表牌墙剩下的牌占原始牌墙牌的总数，float）"""
    def __init__(self, action_dim = 235):
        super(MahjongCNN_v1, self).__init__()
        self.inplanes = 64 
        self.conv1 = nn.Conv2d(53, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.layer1 = self.make_layer(BasicBlock, 64, 2, stride=1)
        self.layer2 = self.make_layer(BasicBlock, 128, 2, stride=1)
        self.layer3 = self.make_layer(BasicBlock, 256, 2, stride=1)
        self.layer4 = self.make_layer(BasicBlock, 512, 2, stride=1)
        self.compress = nn.Sequential(
            nn.Conv2d(512, 128, kernel_size=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True)
        )
        self.fc_shared = nn.Sequential(
            nn.Linear(4608, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Linear(512, 512),
            nn.ReLU(inplace=True)
        )
        self.policy_head = nn.Linear(512, action_dim)
        self.value_head = nn.Sequential(
            nn.Linear(512, 1),
            nn.Tanh()
        )
    
    def make_layer(self, block: BasicBlock, planes, blocks, stride=1):
        downsample = None   # 如果输入输出通道不一致，使用 1x1 卷积对齐残差路径
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x_map):   # x_map: (Batch, 53, 4, 9)
        x = self.conv1(x_map) # 第1层
        x = self.bn1(x)
        x = self.relu(x)
        x = self.layer1(x) # 2-5层
        x = self.layer2(x) # 6-9层
        x = self.layer3(x) # 10-13层
        x = self.layer4(x) # 14-17层
        x = self.compress(x)
        x = torch.flatten(x, 1)
        feat = self.fc_shared(x)
        return self.policy_head(feat), self.value_head(feat)
    
class MahjongCNN_v1_FeatureExtractor(nn.Module):
    def __init__(self):
        self.height = 4
        self.width = 9
        self.feature_map = np.zeros((53, self.height, self.width), dtype=np.float32)
        self.thresholds = np.array([1, 2, 3, 4]).reshape(4, 1, 1)
        self.counts = np.zeros((4, 9), dtype=int)
        self.full_wall = np.full((4, 9), 4, dtype=int)

    def encode(self, game_state: dict[str, Any]) -> torch.Tensor:
        """编码游戏状态为CNN输入的特征图，返回一个形状为(53, 4, 9)的张量
        Args:
            game_state (dict): 包含当前玩家可见的游戏状态信息的字典
        Returns:
            torch.Tensor: 形状为(53, 4, 9)的特征图张量，包含当前玩家可见的游戏状态信息"""
        #   dict: 包含当前玩家可见的游戏状态信息的字典
        #   - 'real_order': 真实上下家顺序（自己为1号玩家，如2号玩家视角下：0123 -> 2301）
        #   - 'god_id': 当前财神牌ID
        #   - 'hand': 当前玩家的手牌信息，4x9矩阵，表示每种牌的数量（不包括副露）
        #   - 'an_gang': 当前玩家的暗杠信息，4x9矩阵，表示每种牌是否暗杠
        #   - 'ming_gang': 每个玩家的明杠信息，4x9矩阵，表示每种牌是否明杠
        #   - 'peng': 每个玩家的碰牌信息，4x9矩阵，表示每种牌是否碰牌
        #   - 'chi': 每个玩家的吃牌信息，4x9矩阵，表示吃牌数量（取顺子首张牌）
        #   - 'discards': 每个玩家的弃牌历史，长度为28的数组，表示每次弃牌的牌ID，初始值为-1
        #   - 'current_phase': 当前游戏阶段，整数表示不同阶段
        #   - 'remaining_tiles': 剩余牌数量，整数表示牌堆中剩余的牌数
        #   - 'is_banker': 是否为庄家，1表示是庄家，0表示非庄家
        #   - 'basic_score': 当前底分，整数表示当前的底分值
        self.feature_map.fill(0)
        playerid = game_state['real_order']
        hand_matrix: np.ndarray = game_state['hand']  # 4x9矩阵，表示每种牌的数量（不包括副露）
        self.feature_map[0:4] = (hand_matrix[np.newaxis, :, :] >= self.thresholds).astype(np.float32)  # 0-3层：手牌One hot
        self.feature_map[4] = (game_state['an_gang'] >= 1).astype(np.float32)  # 4层：暗杠One hot
        for i in range(4): # 5-16层：每个玩家的吃碰杠信息One hot；吃牌只记录顺子首张牌
            self.feature_map[5+i*3] = (game_state['chi'][playerid[i]]).astype(np.float32)
            self.feature_map[6+i*3] = (game_state['peng'][playerid[i]] >= 1).astype(np.float32)
            self.feature_map[7+i*3] = (game_state['ming_gang'][playerid[i]] >= 1).astype(np.float32)
            self.encode_single_player_discards(game_state['discards'][playerid[i]], 17+i*6) # 17-40层：每个玩家的弃牌历史One hot
        self.remaining_tiles_layer(game_state['hand'])  # 41-44层：剩余牌数量One hot
        c_god, v_god = divmod(game_state['god_id'], 9)
        self.feature_map[45, c_god, v_god] = 1.0  # 45层：财神牌One hot
        if game_state['current_phase'] < 0:
            pass
        else:
            self.feature_map[46+game_state['current_phase'], :, :] = 1.0  # 46-49层：阶段层One hot
        self.feature_map[50, :, :] = game_state['remaining_tiles'] # 50层：剩余牌占比，float
        self.feature_map[51, :, :] = game_state['is_banker']  # 51层：是否庄家，1或0
        self.feature_map[52, :, :] = game_state['basic_score']  # 52层：底分
        return self.feature_map.copy()

    def encode_single_player_discards(self, player_discard_history: np.ndarray, index: int) -> np.ndarray:
        """编码单个玩家的弃牌历史为CNN输入的特征图，返回一个形状为(6, 4, 9)的数组
        Args:
            player_discard_history (np.ndarray): 长度为28的数组，表示玩家的弃牌历史，初始值为-1
            index (int): 位置索引
        Returns:
            np.ndarray: 形状为(6, 4, 9)的数组，包含玩家弃牌历史的特征图信息"""
        valid_discards = [d for d in player_discard_history if d != -1]
        if not valid_discards:
            return
        self.counts.fill(0)
        for card_id in valid_discards:
            r, c = card_id // 9, card_id % 9
            self.counts[r, c] += 1
        self.feature_map[index:index+4] = (self.counts >= self.thresholds).astype(np.float32)
        last_1 = valid_discards[-1]
        self.feature_map[index+4, last_1 // 9, last_1 % 9] = 1.0
        if len(valid_discards) >= 2:
            last_2 = valid_discards[-2]
            self.feature_map[index+5, last_2 // 9, last_2 % 9] = 1.0
        return

    def remaining_tiles_layer(self, player_hand: np.ndarray):
        """编码剩余牌数量为CNN输入的特征图，返回一个形状为(4, 4, 9)的数组
        Args:
            player_hand (int): 玩家手牌"""
        self.full_wall.fill(4)
        self.full_wall[3, 7:] = 0
        self.full_wall[3, 6] = 3
        self.full_wall -= player_hand  # 减去玩家手牌
        self.full_wall -= self.feature_map[4].astype(int) * 4  # 减去玩家暗杠
        for i in range(4):
            c_chi, v_chi = np.where(self.feature_map[5+i*3] >= 1)  # 吃牌的坐标
            for c, v in zip(c_chi, v_chi):
                self.full_wall[c, v:v+3] -= self.feature_map[5+i*3, c, v] * 1  # 减去玩家吃牌
            self.full_wall -= self.feature_map[6+i*3].astype(int) * 3  # 减去玩家碰牌
            self.full_wall -= self.feature_map[7+i*3].astype(int) * 4  # 减去玩家明杠
            self.full_wall -= self.feature_map[17+i*6:21+i*6].astype(int).sum(axis=0)  # 减去玩家弃牌
        self.feature_map[41:45] = (self.full_wall >= self.thresholds).astype(np.float32)
        return