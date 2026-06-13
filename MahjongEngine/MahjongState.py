# 处理牌桌上各种状态

from typing import Literal
import numpy as np
import os
import json
import torch
import torch.nn as nn
from .Players import CNNPlayer
from Modules.ModulesSturcture import MahjongCNN_v1

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_LIST_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "config", "model", "ModelList.json"))


class PlayerHuStatus:
    """玩家胡牌状态类，包含玩家的特殊牌型信息
    - .has_eight_pairs: 是否八对
    - .has_three_gods: 是否三财神"""
    def __init__(self):
        self.has_eight_pairs: bool = False
        """是否八对"""
        self.has_three_gods: bool = False
        """是否三财神"""

class WinResult:
    """胡牌结果类，包含胡牌类型和相关信息
    - .hu_player_index (int): 胡牌玩家索引
    - .category (int): 胡牌类型
        - 0：软胡、自摸、财神归位/没有财神/财神牛/单吊/碰碰胡
        - 1：抢杠胡
        - 2：其他牌型
    - .tian_hu[bool]: 是否天胡
    - .di_hu[bool]: 是否地胡
    - .player_status: 玩家状态列表，包含每个玩家的状态信息
        - [n].has_eight_pairs[bool]: 是否八对
        - [n].has_three_gods[bool]: 是否三财神"""
    def __init__(self):
        self.hu_player_index: Literal[0, 1, 2, 3] = 0
        """胡牌玩家索引"""
        self.category: Literal[0, 1, 2] = 0
        """胡牌类型
        - 0：自摸
        - 1：抢杠胡
        - 2：其他牌型
        """
        self.tian_hu: bool = True
        """是否天胡"""
        self.di_hu: bool = True
        """是否地胡"""
        self.player_status = [PlayerHuStatus() for _ in range(4)]
        """玩家状态列表，包含每个玩家的状态信息
        - [n].has_eight_pairs[bool]: 是否八对
        - [n].has_three_gods[bool]: 是否三财神"""

    def reset(self):
        """重置胡牌结果，准备开始新的一轮游戏"""
        self.hu_player_index = 0
        self.category = 0
        self.tian_hu = True
        self.di_hu = True
        for player_status in self.player_status:
            player_status.has_eight_pairs = False
            player_status.has_three_gods = False

class GameState:
    """游戏状态类，包含游戏的当前状态和阶段信息
    - .end_state (int): 游戏状态
        - 0：游戏进行
        - 1：胡局
        - 2：流局
    - .game_state (int): 游戏阶段标志
        - 0：摸牌阶段
        - 1：响应阶段
        - 2：弃牌阶段
        - 3：抢杠胡阶段
    - .draw_counter (int): 摸牌计数器，记录当前轮次的摸牌次数
    - .discard_counter (int): 弃牌计数器，记录当前轮次的弃牌次数
    - .last_discard_tile_id (int): 上一次弃牌的牌ID，初始值为-1
    - .current_player_index (int): 当前玩家索引，0、1、2、3分别代表有上下家关系的四个玩家
    - .current_god_id (int): 当前财神索引，0-26分别代表不同的牌，33表示白板"""
    def __init__(self):
        self.end_state: Literal[0, 1, 2] = 0
        """游戏状态
        - 0：游戏进行
        - 1：胡局
        - 2：流局
        """
        self.game_state: Literal[-1, 0, 1, 2, 3] = -1
        """游戏阶段标志
        - -1：初始状态
        - 0：摸牌阶段
        - 1：响应阶段
        - 2：弃牌阶段
        - 3：抢杠胡阶段
        """
        self.draw_counter = 0
        """摸牌计数器，记录当前轮次的摸牌次数"""
        self.gang_counter = 0
        """杠牌计数器，记录当前轮次的杠牌次数"""
        self.last_discard_tile_id: int = -1
        """上一次弃牌的牌ID，初始值为-1"""
        self.current_player_index: Literal[0, 1, 2, 3] = 0
        """当前玩家索引，0、1、2、3分别代表有上下家关系的四个玩家"""
        self.current_god_id: int = 33
        """当前财神索引"""
        self.current_score: int = 1
        """当前底分，初始值为1"""

    def reset(self):
        """重置游戏状态，准备开始新的一轮游戏"""
        self.end_state = 0
        self.game_state = -1
        self.draw_counter = 0
        self.gang_counter = 0
        self.last_discard_tile_id = -1
        self.current_player_index = 0
        self.current_god_id = 33
        self.current_score = 1
        
class ActionManager:
    """玩家操作管理器
    - .legal_action_list: 玩家合法操作列表，包含每个玩家的合法动作列表
    - .is_quested: 是否已经询问过玩家操作，防止重复询问
    - .action_choosen: 玩家选择的动作"""
    def __init__(self):    
        self.legal_action_list = {i: [] for i in range(4)}
        """玩家合法操作列表self.legal_action_list[playerid]"""
        self.is_quested = {i: False for i in range(4)}
        """是否已经询问过玩家操作，防止重复询问"""
        self.action_choosen = {i: None for i in range(4)}
        """玩家选择的动作"""
        self.priority_map = {
            'HU': 3,
            'GANG': 2,
            'PENG': 2, # 同时存在的杠和碰只有一种（如碰三条之后不可能出现杠三条）
            'CHI': 1,
            'PASS': 0
        }
    
    def reset(self):
        """重置操作管理器，准备开始新的一轮游戏"""
        self.legal_action_list = {i: [] for i in range(4)}
        self.is_quested = {i: False for i in range(4)}
        self.action_choosen = {i: None for i in range(4)}

    def get_action_type(self, action_id: int) -> str:
        """根据动作ID获取动作类型
        Args:
            action_id (int): 动作ID，0表示Pass，1表示胡牌，2表示明杠，3表示碰牌，4表示吃牌
        Returns:
            str: 动作类型，'PASS'、'HU'、'GANG'、'PENG'、'CHI'"""
        if action_id == 0: return 'PASS'
        if action_id == 1: return 'HU'
        if 70<= action_id <= 103: return 'GANG'
        if 138<= action_id <= 171: return 'PENG'
        if 172<= action_id <= 234: return 'CHI'

    def judge_action_priority(self, current_player_index: int) -> tuple[int, int]:
        """判断玩家操作优先级，返回需要执行操作的玩家索引
        - 优先级：胡牌 > 明杠 > 碰牌 > 吃牌
        - 如果没有玩家选择胡牌，按照玩家索引顺序执行其他操作
        Args:
            current_player_index (int): 当前玩家索引
        Returns:
            Tuple (int, int): 需要执行操作的玩家索引和对应的操作id
                - 如果没有玩家被询问操作，返回(-1, -1)
                - 如果所有被询问的玩家均选择Pass，返回(-1, -1)"""
        # 这个函数只在开局、响应、抢杠胡三个阶段进行
        # 开局处理胡牌先后顺序
        # 响应阶段处理玩家胡、明杠、碰、吃、Pass的优先级
        # 抢杠胡阶段处理玩家胡牌先后顺序
        target_player_index = -1
        max_priority = -1
        for i in range(1, 4):
            pid = (current_player_index + i) % 4
            if self.is_quested[pid]: # 只考虑被询问的玩家
                current_type = self.get_action_type(self.action_choosen[pid])
                current_priority = self.priority_map.get(current_type, 0)
                if current_priority > max_priority:
                    max_priority = current_priority
                    target_player_index = pid
                elif current_priority == max_priority:
                    # 按照麻将“截胡”逻辑，座次靠前的（更接近出牌人的下家）优先
                    # 因为循环本身就是按座次走的，所以不需要更新target_player_index
                    pass
        if max_priority <= 0:
            return -1, -1
        return target_player_index, self.action_choosen[target_player_index]

class CNNModelManager:
    """模型管理器，负责管理AI模型的加载和更新
    - model_list_path: 模型列表文件路径
    - models: 存放具体的神经网络对象 {name: model_instance}
    - loaded_info: 存放内存中当前模型的元数据 {name: {version: ..., path: ...}}
    Args:
        model_list_path (str): 模型列表文件路径，格式为[{"name": "cnn_v1", "version": 1.2, "path": "..."}, ...]"""
    def __init__(self, model_list_path: str = MODEL_LIST_PATH):
        self.model_list_path = model_list_path
        self.models: dict[str, nn.Module] = {} # 存放具体的神经网络对象 {name: model_instance}
        self.loaded_info: dict[str, dict] = {} # 存放内存中当前模型的元数据 {name: {version: ..., path: ...}}

    def check_model_update(self):
        """检查是否需要更新AI模型，如果需要则处理模型更新"""
        if not os.path.exists(self.model_list_path):
            return
            
        try:
            with open(self.model_list_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)  # 格式假设为: [{"name": "cnn_v1", "version": 1.2, "path": "..."}, ...]
        except Exception as e:
            # print(f"读取配置文件失败: {e}")
            return
        model_list = config_data.get('Model_List', [])
        for info in model_list:
            if not info or 'name' not in info or 'version' not in info or 'path' not in info:
                continue
            name = info['name']
            new_version = info['version']
            path = info['path']

            if name not in self.loaded_info or self.loaded_info[name]['version'] != new_version:
                if path != "Example": # 这个判断是为了测试
                    self.load_or_update_model(name, new_version, path)
        
    def load_or_update_model(self, name: str, version: float, path: str):
        """加载或更新模型，如果模型不存在则加载模型，如果模型版本不同则更新模型
        Args:
            name (str): 模型名称
            version (float): 模型版本
            path (str): 模型路径"""
        try:
            state_dict = torch.load(path, map_location='cpu')
            if name not in self.models:
                self.models[name] = MahjongCNN_v1()
            target_model = self.models[name] # 指向同一地址
            target_model.load_state_dict(state_dict)
            target_model.eval()
            self.loaded_info[name] = {'version': version, 'path': path}

        except Exception as e:
            print(f"加载模型 {name} 失败: {e}")

    def get_model(self, name):
        """提供给 Engine 或 Player 调用"""
        return self.models.get(name)



class HandManager:
    """玩家手牌管理器，包含玩家的手牌、吃碰杠牌、弃牌和牌堆信息
    - .players_hand: 玩家数据结构，包含每个玩家的手牌、吃碰杠牌、弃牌和弃牌指针
        - .hand: 玩家手牌，4x9x1的numpy数组，表示每个玩家的手牌数量
        - .melds: 玩家吃碰杠牌，4x9x4的numpy数组，表示每个玩家的吃碰杠牌数量
            - 第一层代表吃牌，仅记录吃牌的第一张牌（如六七八条记六条）
            - 第二层代表碰牌
            - 第三层代表明杠
            - 第四层代表暗杠
        - .discards: 玩家弃牌，长度为28的numpy数组，表示每个玩家的弃牌记录，初始值为-1
        - .discard_ptr: 玩家弃牌指针，记录当前玩家的弃牌位置
    - .tile_wall: 摸牌牌堆，长度为71的numpy数组，初始值为0
    - .wall_ptr: 牌堆指针，记录当前摸牌的位置"""
    def __init__(self):
        # 初始化 4 个玩家的数据结构
        # 4*9矩阵示意图：
        #       0  1  2  3  4  5  6  7  8
        #       一 二 三 四 五 六 七 八 九
        # 0 万  0  1  2  3  4  5  6  7  8
        # 1 条  9  10 11 12 13 14 15 16 17
        # 2 筒  18 19 20 21 22 23 24 25 26
        # 3 字  东 南 西 北 中 发 白  0  0
        # 使用 dict 存储，方便通过 player_id (0-3) 索引
        self.players_hand: dict[int, dict[str, np.ndarray]] = {i: {
            'hand': np.zeros((4, 9, 1), dtype=int),
            'melds': np.zeros((4, 9, 4), dtype=int),
            'discards': np.full(28, -1, dtype=int),
            'discard_ptr': 0
        } for i in range(4)}
        """玩家数据结构，包含每个玩家的手牌、吃碰杠牌、弃牌和弃牌指针
        - .hand: 玩家手牌，4x9x1的numpy数组，表示每个玩家的手牌数量
        - .melds: 玩家吃碰杠牌，4x9x4的numpy数组，表示每个玩家的吃碰杠牌数量
            - 第一层代表吃牌，仅记录吃牌的第一张牌（如六七八条记六条）
            - 第二层代表碰牌
            - 第三层代表明杠
            - 第四层代表暗杠
        - .discards: 玩家弃牌，长度为28的numpy数组，表示每个玩家的弃牌记录，初始值为-1
        - .discard_ptr: 玩家弃牌指针，记录当前玩家的弃牌位置"""
        self.tile_wall = np.zeros(71, dtype=int) 
        """摸牌牌堆，长度为71的numpy数组，初始值为0"""
        self.wall_ptr = 0
        """牌堆指针，记录当前摸牌的位置"""
        self.CHI_OFFSET = np.array([
            [1, 2], # 吃牌类型0，吃的是顺子中的第一张
            [0, 2], # 吃牌类型1，吃的是顺子中的第二张
            [0, 1]  # 吃牌类型2，吃的是顺子中的第三张
        ])
    
    def reset(self):
        """重置玩家手牌和牌堆，准备开始新的一轮游戏"""
        for player_id in range(4):
            self.players_hand[player_id]['hand'].fill(0)
            self.players_hand[player_id]['melds'].fill(0)
            self.players_hand[player_id]['discards'].fill(-1)
            self.players_hand[player_id]['discard_ptr'] = 0
        self.tile_wall.fill(0)
        self.wall_ptr = 0

    def draw_card(self, player_id: int) -> int:
        """摸牌，从牌堆摸一张牌并更新玩家手牌（已加入手牌）
        Args:
            player_id (int): 当前玩家索引，0-3
        Returns:
            card_id (int): 摸到的牌ID，0-33分别代表不同的牌"""
        if self.wall_ptr < len(self.tile_wall):
            card_id = self.tile_wall[self.wall_ptr]
            self.wall_ptr += 1
            self.players_hand[player_id]['hand'][card_id // 9, card_id % 9, 0] += 1
            return card_id
        else: # 理论上基本不可能发生这种事情，因为在游戏流程中会在摸牌阶段检查牌堆是否为空并处理流局
            raise IndexError("牌堆已空，无法摸牌")

    def do_Discard(self, player_id: int, tile_id: int) -> None:
        """将手牌加入玩家的弃牌区
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        # 将 tile_id 加入玩家的弃牌区
        discard_ptr = self.players_hand[player_id]['discard_ptr']
        if discard_ptr < len(self.players_hand[player_id]['discards']):
            self.players_hand[player_id]['discards'][discard_ptr] = tile_id
            self.players_hand[player_id]['discard_ptr'] += 1
        else:
            # 理论上基本不可能发生这种事情
            # 但是为了代码的鲁棒性，应该处理这种极端情况
            # 需要覆盖之前的弃牌数据，即：所有弃牌向前移动一位，最后一位放入新的 tile_id
            self.players_hand[player_id]['discards'][:-1] = self.players_hand[player_id]['discards'][1:]
            self.players_hand[player_id]['discards'][-1] = tile_id
        return

    def do_AnGang(self, player_id: int, tile_id: int) -> None:
        """执行暗杠操作，更新玩家手牌和牌堆状态
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['melds'][tile_id // 9, tile_id % 9, 3] += 1
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] -= 4
        return

    def do_MingGang(self, player_id: int, tile_id: int) -> None:
        """执行明杠操作，更新玩家手牌和牌堆状态
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['melds'][tile_id // 9, tile_id % 9, 2] += 1
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] -= 3
        return

    def do_BuGang(self, player_id: int, tile_id: int) -> None:
        """执行补杠操作，更新玩家手牌和牌堆状态
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] -= 1
        self.players_hand[player_id]['melds'][tile_id // 9, tile_id % 9, 1] -= 1
        self.players_hand[player_id]['melds'][tile_id // 9, tile_id % 9, 2] += 1
        return

    def do_Peng(self, player_id: int, tile_id: int) -> None:
        """执行碰牌操作，更新玩家手牌和牌堆状态
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['melds'][tile_id // 9, tile_id % 9, 1] += 1
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] -= 2
        return

    def do_Chi(self, player_id: int, action_id: int) -> None:
        """执行吃牌操作，更新玩家手牌和牌堆状态
        Args:
            player_id (int): 当前玩家索引，0-3
            action_id (int): 动作ID，172-234分别代表吃牌的不同牌型"""
        color = (action_id - 172) // 21 # 吃牌的花色，0-2分别代表万条筒，3代表字牌
        chi_type = (action_id - 172) % 21 // 7 # 吃牌的类型，0-2代表吃的是顺子中的第0-2张
        tile_num = ((action_id - 172) % 21 % 7)# 顺子的第一张牌的数字
        off1,off2 = self.CHI_OFFSET[chi_type]
        self.players_hand[player_id]['melds'][color, tile_num, 0] += 1
        self.players_hand[player_id]['hand'][color, tile_num + off1, 0] -= 1
        self.players_hand[player_id]['hand'][color, tile_num + off2, 0] -= 1
        return

    def remove_card(self, player_id: int, tile_id: int) -> None:
        """从玩家手牌中移除一张牌
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] -= 1
        return
    
    def add_card(self, player_id: int, tile_id: int) -> None:
        """向玩家手牌中添加一张牌，用于处理吃牌胡时的手牌问题（最后回传状态的时候胡家要是17张的状态）
        Args:
            player_id (int): 当前玩家索引，0-3
            tile_id (int): 牌ID，0-33"""
        self.players_hand[player_id]['hand'][tile_id // 9, tile_id % 9, 0] += 1
        return