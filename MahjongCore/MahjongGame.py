# 麻将游戏管理器，管理游戏流程、玩家交互和状态更新
# 重新设计
# 现在主要的功能是进行多局游戏的进程
# 输入：玩家类型、对应玩家的当前分数、胜利场次
# 输出：玩家类型、对应玩家的当前分数、胜利场次
# 主要看save里存的是哪几类照着输出就行
# 
# 目的：上层传入游戏数据，本层进行游戏运行以及输出

from dataclasses import dataclass
import csv
import random
from typing import List
import numpy as np
from MahjongEngine.MahjongEngine import MahjongEngine
from MahjongEngine.MahjongEngine import WinResult
from MahjongTools.HandCheckers import HandChecker


@dataclass
class PlayerInfo:
    """玩家信息类，包含玩家ID、昵称、类型等信息
    Args:
        name (str): 玩家昵称
        class_type (str): 玩家类型
        model_name (str): AI模型名称（内部代号）"""
    name: str
    class_type: str
    model_name: str


class MahjongGame:
    """麻将游戏类，负责管理游戏流程、玩家交互和状态更新
    Args:
        model_list_path (str): 模型列表文件路径，用于加载AI模型
        csv_path (str): 玩家信息CSV文件路径，用于加载玩家信息映射表"""
    def __init__(self, model_list_path: str = None, csv_path: str = None):
        
        self.mahjong_engine = MahjongEngine(model_list_path)
        self.players_id = [3, 3, 3, 3]
        self.players_map = {}
        if csv_path: # 加载玩家信息映射表
            self.players_map = self.load_players_map(csv_path)

        # Todo: 这里写的是多轮对局的流程，单轮对局的流程在MahjongEngine中实现
        # 初始化应该初始化下面start game里提到的内容：
        # 需要加载：历史对局胜率、历史积分（类似游戏存档）
        # ✔ ai陪练类似游戏角色一样，一般是一个ai对应一个模型（可能相同），可能需要一个文件保存对应关系
        # ✔ 就是：ai陪练代码 - 对应模型名称 - 对应外部显示昵称 - 对应历史胜率和积分等数据
        # ✔ 以及玩家个人的昵称 - 历史胜率和积分等数据（可能需要一个文件来存储）
        # ✔ 当然存档要做到可以中途加入新的ai陪练。

    def load_players_map(self, csv_path: str) -> dict[int, PlayerInfo]:
        """加载玩家信息映射表，包括玩家ID、昵称、类型等信息
        Args:
            csv_path (str): 玩家信息CSV文件路径
        Returns:
            dict (int, PlayerInfo): 玩家信息映射表"""
        players_map = {}
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)  # 自动按列名读取
            for row in reader:
                player_id = int(row["PlayerID"])
                players_map[player_id] = PlayerInfo(
                    name=row["PlayersName"],
                    class_type=row["PlayerClass"],
                    model_name=row["PlayerModelName"]
                )
        return players_map

    def reset_game(self, player_id: list[int]):
        """重置游戏状态，类似和新的一桌人开始游戏"""
        self.players_id = player_id
        self.base_score: int = 1
        self.model_type = [None] * len(player_id)
        # Todo
        # 传入模型名称，现在的逻辑应该是：
        # MahjongEngine不再判定AI模型是否增加，而是根据MahjongGame传入的类型来确定ai
        # 判断的工作交给MahjongGame
        # MahjongEngine负责：根据玩家类型和模型名称来载入模型并进行游戏
        # MahjongGame负责：根据输入的玩家类型来确定模型名称并传入给MahjongEngine
        pass
    
    def start_game(self, shanting_num: int = -1, round_num: int = 1):
        """开始游戏，处理游戏流程和玩家交互"""
        banker_index = random.randint(0,3) # 随机选庄家
        god_id = random.randint(0,33) # 随机选财神
        if round_num == -1:
            while True:
                self.mahjong_engine.reset(players_type=self.players_type, 
                                          model_name=self.model_type, 
                                          banker_index=banker_index, 
                                          god_id=god_id, shanting_num=shanting_num, 
                                          current_base_score=self.base_score)
                players_state, end_reason, win_result = self.mahjong_engine.play_one_round()
                players_scores = self.get_score(players_state, end_reason, win_result, god_id)

                # 判断是否进入下一轮（-1一般用于玩家交互时）
        else:
            for _ in range(round_num):
                self.mahjong_engine.reset(players_type=self.players_type, 
                                          model_name=self.model_type, 
                                          banker_index=banker_index, 
                                          god_id=god_id, shanting_num=shanting_num, 
                                          current_base_score=self.base_score)
                players_state, end_reason, win_result = self.mahjong_engine.play_one_round()
                players_scores = self.get_score(players_state, end_reason, win_result, god_id)

                # 一般用于ai自对弈时，或者玩家当看客
        pass
        # Todo: 这里写的是多轮对局的流程，单轮对局的流程在MahjongEngine中实现
        # 处理玩家的计分状态和逻辑、选择玩家交互方式（如输入或AI决策）
        # 排座次，例如玩家总是坐在Player0位置，其他玩家依次坐下
        # 初始化游戏状态，传入：玩家种类、模型名称、庄家、初始向听数、底分等参数
        # 进入游戏循环，直到游戏结束
        # 然后进行分数计算和结果展示，更新玩家的历史胜率和积分等数据
        # 需要保存：每轮对局的结果、玩家的计分状态和逻辑、选择玩家交互方式
        # 
        # 庄家的轮换逻辑


    def get_score(self, player_state: dict[int, dict[str, np.ndarray]], end_reason: int, win_result: WinResult, god_id: int) -> List[int]:
        """获取当前游戏的分数情况
        Args:
            player_state (dict[int, dict[str, np.ndarray]]): 当前玩家状态，包括手牌、鸣牌等信息
            end_reason (int): 游戏结束原因，1-正常胡牌，2-流局
            win_result (WinResult): 胡牌结果对象，包含胡牌类型、胡牌玩家等信息
            god_id (int): 本局游戏的财神ID
        Returns:
            List (int): 包含每位玩家分数的列表，顺序与玩家ID对应"""
        if end_reason == 2: # 流局
            god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
            total = sum(god_num)
            player_scores = [gn * 4 - total for gn in god_num]
            return player_scores
        else: # 胡牌
            if win_result.player_status[win_result.hu_player_index].has_three_gods: # 三财神
                if self.mahjong_engine.hand_checker.BaseHu_Checker(player_state[win_result.hu_player_index]['hand']):
                    player_scores = [-(self.base_score * 4 + 3) for _ in range(4)] # 底分*4倍率+3财神分
                    player_scores[win_result.hu_player_index] = (self.base_score * 4 + 3) * 3
                    return player_scores
                else:
                    player_scores = [-(self.base_score * 2 + 3) for _ in range(4)] # 底分*2倍率+3财神分
                    player_scores[win_result.hu_player_index] = (self.base_score * 2 + 3) * 3
                    return player_scores
            elif win_result.player_status[win_result.hu_player_index].has_eight_pairs: # 八对
                if player_state[win_result.hu_player_index]['hand'][3, 6, 0] == 0:
                    player_scores = [-(self.base_score * 4) for _ in range(4)] # 底分*4倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 4) * 3
                else:
                    player_scores = [-(self.base_score * 2) for _ in range(4)] # 底分*2倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 2) * 3
                god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                total = sum(god_num)
                player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                return player_scores
            elif win_result.tian_hu or win_result.di_hu: # 天胡、地和
                player_scores = [-(self.base_score * 4) for _ in range(4)] # 底分*4倍率
                player_scores[win_result.hu_player_index] = (self.base_score * 4) * 3
                god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                total = sum(god_num)
                player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                return player_scores
            else: # 普通胡牌，已经确保了至少符合胡牌牌型条件
                if player_state[win_result.hu_player_index]['hand'].sum() == 2 and player_state[win_result.hu_player_index]['hand'][3, 6, 0] == 0: # 单吊
                    player_scores = [-(self.base_score * 4) for _ in range(4)] # 底分*4倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 4) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                elif player_state[win_result.hu_player_index]['melds'][:,:,0].sum() == 0: # 碰碰胡
                    player_scores = [-(self.base_score * 4) for _ in range(4)] # 底分*4倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 4) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                elif player_state[win_result.hu_player_index]['hand'].sum() == 2: # 财神牛（与单吊区别在有财神）
                    player_scores = [-(self.base_score * 2) for _ in range(4)] # 底分*2倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 2) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                elif win_result.category == 1: # 抢杠胡
                    player_scores = [-(self.base_score * 2) for _ in range(4)] # 底分*2倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 2) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                elif win_result.category == 0: # 自摸胡
                    player_scores = [-(self.base_score * 2) for _ in range(4)] # 底分*2倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 2) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                elif self.mahjong_engine.hand_checker.God_inplace_Checker(god_id, player_state[win_result.hu_player_index]['hand']): # 财神归位
                    player_scores = [-(self.base_score * 2) for _ in range(4)] # 底分*2倍率
                    player_scores[win_result.hu_player_index] = (self.base_score * 2) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores
                else: # 普通胡牌
                    player_scores = [-(self.base_score) for _ in range(4)] # 底分倍率
                    player_scores[win_result.hu_player_index] = (self.base_score) * 3
                    god_num = [ps['hand'][3, 6, 0] for ps in player_state.values()]
                    total = sum(god_num)
                    player_scores = [ps + gn * 4 - total for ps, gn in zip(player_scores, god_num)]
                    return player_scores