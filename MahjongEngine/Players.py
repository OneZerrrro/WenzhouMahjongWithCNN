# AI/真人玩家和牌桌的交互逻辑

import torch
from  abc import ABC, abstractmethod
import torch.nn as nn
from Modules.ModulesSturcture import MahjongCNN_v1
import random
import numpy as np
from MahjongTools.HandCheckers import HandChecker



class BaseMahjongAgent(ABC):
    def __init__(self, name: str):
        self.playerid = None
        self.name = name
        pass

    @abstractmethod
    def choose_action(self, game_state: dict, legal_actions: list[int]) -> int:
        """根据当前游戏状态和合法动作列表选择一个动作
        - game_state: 当前游戏状态对象，包含牌桌信息、玩家信息等
            - 'real_order': 真实上下家顺序（自己为1号玩家，如2号玩家视角下：0123 -> 2301）
            - 'god_id': 当前财神牌ID
            - 'hand': 当前玩家的手牌信息，4x9矩阵，表示每种牌的数量（不包括副露）
            - 'an_gang': 当前玩家的暗杠信息，4x9矩阵，表示每种牌是否暗杠
            - 'ming_gang': 每个玩家的明杠信息，4x9矩阵，表示每种牌是否明杠
            - 'peng': 每个玩家的碰牌信息，4x9矩阵，表示每种牌是否碰牌
            - 'chi': 每个玩家的吃牌信息，4x9矩阵，表示吃牌数量（取顺子首张牌）
            - 'discards': 每个玩家的弃牌历史，长度为28的数组，表示每次弃牌的牌ID，初始值为-1
            - 'current_phase': 当前游戏阶段，整数表示不同阶段
            - 'remaining_tiles': 剩余牌数量，整数表示牌堆中剩余的牌数
            - 'is_banker': 是否为庄家，1表示是庄家，0表示非庄家
            - 'players_hand': 
                所有玩家的完整手牌信息
                仅在playerid = -1 时返回且playerid = -1 仅返回这个值
                包含每个玩家的手牌、明杠、暗杠、碰牌、吃牌和弃牌信息
        - legal_actions: 当前玩家可执行的合法动作列表，每个动作包含动作类型和相关参数
            - 全部操作表：000 过牌 001 胡牌
            - 弃牌：万 002-010  条 011-019  筒 020-028  字 029-035  +002
            - 暗杠：万 036-044  条 045-053  筒 054-062  字 063-069  +036
            - 明杠：万 070-078  条 079-087  筒 088-096  字 097-103  +070
            - 补牌：万 104-112  条 113-121  筒 122-130  字 131-137  +104
            - 碰牌：万 138-146  条 147-155  筒 156-164  字 165-171  +138
            - 吃牌：万 172-192  条 193-213  筒 214-234
            - 吃牌映射表：
            - 万 +0  条 +21  筒 +42
            - +00 - +06：[v] v+1 v+2    +00
            - +07 - +13：v-1 [v] v+1    +07
            - +14 - +20：v-2 v-1 [v]    +14"""
        pass

    # def __str__(self):
    #     return f"[{self.name}] Player {self.playerid})"
    
class Human(BaseMahjongAgent):
    def choose_action(self, game_state: dict, legal_actions: list[int]) -> int:
        """通过用户输入选择一个动作"""
        # Todo
        pass

class RandomAI(BaseMahjongAgent):
    def choose_action(self, game_state: dict, legal_actions: list[int]) -> int:
        """随机选择一个动作"""
        if not legal_actions: # 没有合法动作时返回0，不知道为什么会有这种情况，先加个保护
            return 0
        if 1 in legal_actions:
            return 1  # 优先选择胡牌，有胡傻逼也胡了
        return random.choice(legal_actions)

class RuleBasedAI(BaseMahjongAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.checker = HandChecker()
        self.remaining_cards = np.zeros((4, 9), dtype=int) # 记录剩余牌数量的矩阵，4x9表示每种牌的剩余数量
        self.chi_counts = np.zeros((4, 9), dtype=int) # 记录每种牌被吃的次数，4x9表示每种牌被吃的数量
        self.total_count = np.full((4, 9), 4)
        self.total_count[3, 7:] = 0  # 字牌只有 7 种，索引 7 和 8 设为 0
        self.total_count[3, 6] = 3  # 白板只有 3 张，索引 6 设为 3
    def choose_action(self, game_state: dict, legal_actions: list[int]) -> int:
        """基于规则选择一个动作"""
        if not legal_actions: # 没有合法动作时返回0，不知道为什么会有这种情况，先加个保护
            return 0
        if 1 in legal_actions:
            return 1  # 优先选择胡牌
        gang_actions = [a for a in legal_actions if 36 <= a <= 137]
        if gang_actions: # 选择暗杠明杠补杠，优先级：暗杠>明杠>补杠
            return gang_actions[0] # 但是暗杠和补杠不会和明杠同时出现，所以直接返回第一个就行了
        
        peng_actions = [a for a in legal_actions if 138 <= a <= 171]
        if peng_actions: # 选择碰牌
            return peng_actions[0]
        
        chi_actions = [a for a in legal_actions if 172 <= a <= 234]
        if chi_actions: # 选择吃牌
            return self.choose_chi(game_state, chi_actions)
        
        discard_actions = [a for a in legal_actions if 2 <= a <= 35]
        if discard_actions: # 选择弃牌
            return self.choose_discard(game_state, discard_actions)
        
    def choose_chi(self, game_state: dict[str, dict[int, np.ndarray] | np.ndarray], chi_actions: list[int]) -> int:
        """基于规则选择一个吃牌动作
        Args:
            game_state: 当前游戏状态对象，包含牌桌信息、玩家信息等
            chi_actions: 当前玩家可执行的吃牌动作列表，每个动作包含动作类型和相关参数
        Returns:
            int: 选择的吃牌动作ID"""
        best_chi_action = chi_actions[0]
        best_efficiency = -1
        current_hand: np.ndarray = game_state['hand'].copy()
        current_hand_for_discard: np.ndarray = game_state['hand'].copy()
        peng_sum = np.sum(list(game_state['peng'].values()), axis=0) * 3
        gang_sum = np.sum(list(game_state['ming_gang'].values()), axis=0) * 4 + np.sum(game_state['an_gang'], axis=0) * 4
        all_discarded = np.concatenate(list(game_state['discards'].values()))
        valid_discards = all_discarded[all_discarded >= 0]
        discard_sum = np.bincount(valid_discards, minlength=36).reshape(4, 9)
        all_chi = np.array(list(game_state['chi'].values()))
        chi_base = all_chi[:, :3, :]
        self.chi_counts[:3, :] = (
            chi_base.sum(axis=0) + # 作为顺子起点 [v, v+1, v+2]
            np.pad(chi_base[:, :, :-1].sum(axis=0), ((0,0), (1,0)))[:, :9] + # 作为中点
            np.pad(chi_base[:, :, :-2].sum(axis=0), ((0,0), (2,0)))[:, :9]   # 作为终点
        )
        for action in chi_actions:
            self.chi_counts.fill(0)
            self.remaining_cards[:3, :] = 4
            self.remaining_cards[3, :7] = 4
            cards_to_remove = self.parse_chi_action(action)
            for c, v in cards_to_remove:
                current_hand[c, v] -= 1
                self.remaining_cards[c, v] -= 1
                current_hand_for_discard[c, v] -= 1
            # 计算仍然没有出现过的牌
            exist_matrix = discard_sum + peng_sum + gang_sum + current_hand + self.chi_counts
            self.remaining_cards = np.maximum(0, self.total_count - exist_matrix)
            norm_id = action - 172
            suit, offset = norm_id // 21, norm_id % 21
            if offset < 7:
                self.remaining_cards[suit, offset] -= 1
            elif offset < 14:
                self.remaining_cards[suit, offset - 6] -= 1
            else:
                self.remaining_cards[suit, offset - 12] -= 1
            legal_discard_actions_after_chi = [a + 2 for a in range(34) if current_hand[a // 9, a % 9] > 0]
            # 计算弃牌后的效率
            max_efficiency = -1
            for discard_action in legal_discard_actions_after_chi:
                norm_id = discard_action - 2
                c, v = norm_id // 9, norm_id % 9
                current_hand_for_discard[c, v] -= 1
                current_shanten = self.checker.get_shanten_num(current_hand_for_discard)
                efficiency = 0
                # 遍历 34 种牌 (万条筒 0-8, 字 0-6)
                for tc in range(4):
                    for tv in range(9 if tc < 3 else 7):
                        if self.remaining_cards[tc, tv] > 0:  # 假如还有可能摸入这张牌，模拟摸入
                            current_hand_for_discard[tc, tv] += 1
                            if self.checker.get_shanten_num(current_hand_for_discard) < current_shanten: # 如果摸入后向听数减小，则是有效进张
                                efficiency += self.remaining_cards[tc, tv] # 累加这张牌在场上的剩余张数
                            current_hand_for_discard[tc, tv] -= 1 # 回溯（减去模拟摸的牌）
                score = (10 - current_shanten) * 100 + efficiency
                if score > max_efficiency:
                    max_efficiency = score
                current_hand_for_discard[c, v] += 1
            if best_efficiency < max_efficiency:
                best_efficiency = max_efficiency
                best_chi_action = action
            for c, v in cards_to_remove:
                current_hand[c, v] += 1
                current_hand_for_discard[c, v] += 1
        return best_chi_action
    
    def choose_discard(self, game_state: dict[str, dict[int, np.ndarray] | np.ndarray], discard_actions: list[int]) -> int:
        """根据当前手牌和规则选择一个弃牌动作
        Args:
            game_state (dict[str, dict[int, np.ndarray]]): 当前游戏状态对象，包含牌桌信息、玩家信息等
            discard_actions (list[int]): 当前玩家可执行的弃牌动作列表，每个动作包含动作类型和相关参数
        Returns:
            int: 选择的弃牌动作ID"""
        self.chi_counts.fill(0)
        self.remaining_cards[:3, :] = 4
        self.remaining_cards[3, :7] = 4
        peng_sum = np.sum(list(game_state['peng'].values()), axis=0) * 3
        gang_sum = np.sum(list(game_state['ming_gang'].values()), axis=0) * 4 + np.sum(game_state['an_gang'], axis=0) * 4
        all_discarded = np.concatenate(list(game_state['discards'].values()))
        valid_discards = all_discarded[all_discarded >= 0]
        discard_sum = np.bincount(valid_discards, minlength=36).reshape(4, 9)
        all_chi = np.array(list(game_state['chi'].values()))
        chi_base = all_chi[:, :3, :]
        self.chi_counts[:3, :] = (
            chi_base.sum(axis=0) + # 作为顺子起点 [v, v+1, v+2]
            np.pad(chi_base[:, :, :-1].sum(axis=0), ((0,0), (1,0)))[:, :9] + # 作为中点
            np.pad(chi_base[:, :, :-2].sum(axis=0), ((0,0), (2,0)))[:, :9]   # 作为终点
        )
        exist_matrix = discard_sum + peng_sum + gang_sum + game_state['hand'] + self.chi_counts
        self.remaining_cards = np.maximum(0, self.total_count - exist_matrix)

        best_action = discard_actions[0]
        max_efficiency = -1
        current_hand: np.ndarray = game_state['hand'].copy()
        for action in discard_actions:
            norm_id = action - 2
            c, v = norm_id // 9, norm_id % 9
        
            current_hand[c, v] -= 1
            current_shanten = self.checker.get_shanten_num(current_hand)
            efficiency = 0
            # 遍历 34 种牌 (万条筒 0-8, 字 0-6)
            for tc in range(4):
                for tv in range(9 if tc < 3 else 7):
                    if self.remaining_cards[tc, tv] > 0:  # 假如还有可能摸入这张牌，模拟摸入
                        current_hand[tc, tv] += 1
                        if self.checker.get_shanten_num(current_hand) < current_shanten: # 如果摸入后向听数减小，则是有效进张
                            efficiency += self.remaining_cards[tc, tv] # 累加这张牌在场上的剩余张数
                        current_hand[tc, tv] -= 1 # 回溯（减去模拟摸的牌）
            score = (10 - current_shanten) * 100 + efficiency
            if score > max_efficiency:
                max_efficiency = score
                best_action = action
            current_hand[c, v] += 1
        return best_action

    def parse_chi_action(self, action: int) -> list[tuple[int, int]]:
        """解析吃牌动作ID，返回需要消耗的两张牌的坐标列表
        Args:
            action: 吃牌动作ID，范围为172-234
        Returns:
            list (tuple[int, int]): 需要消耗的两张牌的坐标列表，每个坐标为(花色, 数值)"""
        norm_id = action - 172
        suit = norm_id // 21
        offset = norm_id % 21
        if offset < 7:
            return [(suit, offset + 1), (suit, offset + 2)]
        elif offset < 14:
            return [(suit, offset - 7), (suit, offset - 7 + 2)]
        else:
            return [(suit, offset - 14), (suit, offset - 14 + 1)]
        
class CNNPlayer(BaseMahjongAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.model: MahjongCNN_v1 = None
    
    def bind_model(self, model_obj: MahjongCNN_v1):
        """让这个Agent绑定到ModelManager里的某个模型"""
        self.model = model_obj

    def choose_action(self, game_state: dict, legal_actions: list[int]) -> int:
        """使用卷积神经网络模型选择一个动作"""
        if self.model is None:
            return legal_actions[0]
        # Todo
        pass