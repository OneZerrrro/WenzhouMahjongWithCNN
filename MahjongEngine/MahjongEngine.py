# 麻将引擎

import numpy as np
from typing import Literal
from .MahjongState import GameState, WinResult, HandManager, ActionManager, CNNModelManager
from .HandGenerator import HandGenerator
from MahjongTools.HandCheckers import HandChecker
from MahjongTools.Visualization import EngineVisualization
from .Players import BaseMahjongAgent, Human, RandomAI, RuleBasedAI, CNNPlayer


class MahjongEngine:
    """麻将引擎类，负责处理一轮麻将游戏的逻辑和规则
    Args:
        model_list_path (str): 模型列表文件路径，用于加载AI模型"""
    def __init__(self, model_list_path: str = None):
        # 初始化游戏状态管理器
        self.game_state = GameState()
        """游戏状态对象，包含游戏的当前状态和阶段信息"""
        self.win_result = WinResult()
        """胡牌结果对象，包含胡牌类型和相关信息"""
        self.hand_generator = HandGenerator()
        """手牌生成器对象，负责生成初始牌墙和玩家手牌"""
        self.hand_manager = HandManager()
        """手牌管理器对象，负责管理玩家的手牌和副露状态"""
        self.action_manager = ActionManager()
        """操作管理器对象，负责处理玩家的操作和游戏状态的更新"""
        if model_list_path is not None:
            self.model_manager = CNNModelManager(model_list_path)
            """模型管理器对象，负责管理AI模型的加载和更新"""
        else:
            self.model_manager = CNNModelManager()
            """模型管理器对象，负责管理AI模型的加载和更新"""
        self.permanent_players = [CNNPlayer(name=f"CNNAI_{i}") for i in range(4)]
        """预建玩家列表，包含四个CNNPlayer对象，玩家ID为0-3，名称为CNNAI_0到CNNAI_3"""
        self.static_players = {
            0: Human(name="Human"),
            2: RandomAI(name="Random"),
            3: RuleBasedAI(name="Rule")
        }
        """静态玩家字典，包含非CNN玩家的预建对象，键为玩家类型，值为对应的玩家对象"""
        self.hand_checker = HandChecker()
        """手牌检查器"""
        self.if_display = False
        """是否显示游戏过程，默认为False"""
        self.visualizer = EngineVisualization()
        """游戏过程可视化对象，负责将当前局面在命令行画出来"""
        self.banker_index = 0
        """庄家索引，0-3分别代表四个玩家"""
        self.last_action = {"playerid": None, "action_id": None} # 注：当playerid=-1时表示是摸牌进张，action_id为摸牌的牌ID
        """记录上一次操作的玩家ID和操作ID"""
        self.players_type = [0, 0, 0, 0]
        """玩家类型列表，数字含义：0代表默认观看视角（默认是人类玩家），1代表任意类型的AI玩家"""

    def reset(self, players_type: list, model_name: list, banker_index: Literal[0, 1, 2, 3], 
              god_id: int = 33, shanting_num: Literal[-1, 0, 1, 2] = -1, current_base_score: Literal[1, 2, 3, 4] = 1, if_display: bool = False):
        """重置游戏状态，准备开始新的一轮游戏
        Args:
            players_type (list): 按顺序输入玩家类型列表，数字含义：
                - 0代表人类玩家
                - 1代表CNN玩家
                - 2代表随机玩家
                - 3代表规则玩家
            model_name (list): 按顺序输入玩家使用的模型名称列表，字符串格式，CNN玩家需要指定模型名称，其他玩家填None
            banker_index (int): 庄家索引，0-3分别代表四个玩家中的庄家
            god_id (int): 财神牌ID，0-26分别代表不同的牌，33表示白板，默认为33
            shanting_num (int): 0号玩家初始手牌向听数，-1表示不限制向听数
            current_base_score (int): 当前底分，1-4分别代表不同的底分值，默认为1
            if_display (bool): 是否显示游戏过程，默认为False"""
        
        self.if_display = if_display
        self.model_manager.check_model_update() # 检查CNN模型更新
        self.players: list[BaseMahjongAgent] = []
        for i, (p_type, m_name) in enumerate(zip(players_type, model_name)):
            if p_type == 1:
                player = self.permanent_players[i]
                player.bind_model(self.model_manager.get_model(m_name))
                self.players_type[i] = 1
            else:
                player = self.static_players[p_type] # 规则/随机玩家
                self.players_type[i] = 0 if p_type == 0 else 1
                if p_type == 0:
                    self.static_players[0].reset(god_id)
            self.players.append(player)
            # 根据玩家类型设置self.players_type

        self.game_state.reset()
        self.win_result.reset()
        self.hand_manager.reset()
        self.visualizer.reset(god_id)
        self.banker_index = banker_index
        self.game_state.current_player_index = banker_index
        self.game_state.current_god_id = god_id
        self.game_state.current_score = current_base_score
        self.action_manager.reset()
        self.last_action: dict[str, None | int] = {"playerid": None, "action_id": None}
        if not 0 in self.players_type: # 如果没有默认观看视角，则默认第一个人为观看视角
            self.players_type[0] = 0

        # 抓牌、看牌，洗牌、码牌
        self.initial_hands, self.initial_wall = self.hand_generator.generate_hand(shanting_num)
        for i in range(4):
            self.hand_manager.players_hand[i]['hand'] = self.initial_hands[:, :, i:i+1]
        coords = np.argwhere(self.initial_wall > 0) # N行2列的有牌的坐标矩阵
        counters = self.initial_wall[coords[:, 0], coords[:, 1]] # N行1列的对应坐标的牌数矩阵
        tile_id = coords[:, 0] * 9 + coords[:, 1] # N行1列的牌ID矩阵
        self.hand_manager.tile_wall = np.repeat(tile_id, counters, axis=0) # 扩展成每张牌对应一行的牌堆矩阵，长度为剩余牌数
        np.random.shuffle(self.hand_manager.tile_wall) # 洗牌
        return
        
    def play_one_round(self) -> tuple[dict[int, dict[str, np.ndarray]], int, WinResult]:
        """完整运行一局游戏
        Returns:
            tuple (dict[int, dict[str, np.ndarray]], int, WinResult): 
            - 牌桌状态：包含每位玩家的手牌和副露状态，格式为{playerid: {'hand': np.ndarray, 'melds': np.ndarray}}
            - 游戏状态：当前游戏结束原因，数字含义如下：1 胡局 2 流局
            - 胡牌结果：WinResult对象，包含胡牌类型和相关信息: 
                hu_player_index: 胡牌玩家索引，零至三分别代表四个玩家，-1表示无人胡牌
                category: 胡牌类型，数字含义如下：0 基本胡牌 1 抢杠胡 2 其他特殊牌型
                tian_hu: 是否天胡
                di_hu: 是否地胡
                player_status: 每位玩家是否有八对、三财神，格式为{playerid: {'has_eight_pairs': bool, 'has_three_gods': bool}}"""
        for playerid in range(4):
            self.action_manager.legal_action_list[playerid] = self.get_legal_actions(playerid=playerid)
        for pid, actions in self.action_manager.legal_action_list.items():
            if 1 in actions:    # 仅询问能胡牌的玩家
                if self.if_display and self.players_type[pid] == 0:
                    self.visualizer.draw_game(self.get_visible_state(pid)) # 开局检查阶段询问玩家操作前先可视化当前局面
                self.action_manager.is_quested[pid] = True
                self.action_manager.action_choosen[pid] = self.players[pid].choose_action(self.get_visible_state(pid), actions)
        action_player_index, _ = self.action_manager.judge_action_priority(self.game_state.current_player_index)
        # 根据action_player_index和action_id执行相应的操作
        if action_player_index == -1:
            for playerid in range(4):
                self.win_result.player_status[playerid].has_eight_pairs = False
                self.action_manager.is_quested[playerid] = False
        else:
            self.game_state.end_state = 1
            self.win_result.hu_player_index = action_player_index
            self.win_result.category = 2

        self.game_state.game_state = 0
        while self.game_state.end_state == 0:
            if self.game_state.game_state == 0:
                self.game_state.game_state = self.draw_phase()
            elif self.game_state.game_state == 1:
                self.game_state.game_state = self.response_phase()
            elif self.game_state.game_state == 2:
                self.game_state.game_state = self.discard_phase()
            elif self.game_state.game_state == 3:
                self.game_state.game_state = self.qiang_gang_hu_phase()

        # if self.game_state.end_state == 1:
            # 有人胡局，处理胡牌结算逻辑
            # pass
        # if self.game_state.end_state == 2:
            # 流局，处理流局结算逻辑
            # pass
        # 统一传回牌桌状态、游戏结束原因和胡牌结果，不再分支处理，供外部调用者使用
        final_visible_state = self.get_visible_state(-1) # 游戏结束后返回完整的牌桌状态
        return final_visible_state, self.game_state.end_state, self.win_result

    def get_legal_actions(self, playerid: int) -> list[int]:
        """获取当前玩家的合法操作列表
        - self.game_state.game_state = -1 开局检查阶段
        - self.game_state.game_state = 0 摸牌阶段
        - self.game_state.game_state = 1 响应阶段，需要current_player和current_card
        - self.game_state.game_state = 2 弃牌阶段，需要待定
        - self.game_state.game_state = 3 抢杠胡阶段，需要待定
        Args:
            playerid (int): 目标玩家的索引，0-3分别代表四个玩家
        Returns:
            list: 合法操作列表
        """
        # 全部操作表：000 过牌 001 胡牌
        # 弃牌：万 002-010  条 011-019  筒 020-028  字 029-035  +002
        # 暗杠：万 036-044  条 045-053  筒 054-062  字 063-069  +036
        # 明杠：万 070-078  条 079-087  筒 088-096  字 097-103  +070
        # 补牌：万 104-112  条 113-121  筒 122-130  字 131-137  +104
        # 碰牌：万 138-146  条 147-155  筒 156-164  字 165-171  +138
        # 吃牌：万 172-192  条 193-213  筒 214-234

        # 吃牌映射表：
        # 万 +0  条 +21  筒 +42
        # +00 - +06：[v] v+1 v+2    +00
        # +07 - +13：v-1 [v] v+1    +07
        # +14 - +20：v-2 v-1 [v]    +14

        # 通过读取阶段self.game_state.game_state
        # 玩家手牌状态self.hand_manager.players_hand[playerid]['hand']
        # 玩家副露状态self.hand_manager.players_hand[playerid]['melds']
        # 来判断合法操作

        legal_actions = []
        if self.game_state.game_state == -1:
            # 开局检查阶段
            legal_actions.append(0)
            self.win_result.player_status[playerid].has_eight_pairs = self.hand_checker.EightPair_Checker(self.hand_manager.players_hand[playerid])
            self.win_result.player_status[playerid].has_three_gods = self.hand_checker.ThreeGods_Checker(self.hand_manager.players_hand[playerid])
            if self.win_result.player_status[playerid].has_eight_pairs or self.win_result.player_status[playerid].has_three_gods:
                legal_actions.append(1)
        
        elif self.game_state.game_state == 0:
            # 摸牌阶段   检查胡牌 出牌 暗杠 补杠
            self.win_result.player_status[playerid].has_three_gods = self.hand_checker.ThreeGods_Checker(self.hand_manager.players_hand[playerid]) if not self.win_result.player_status[playerid].has_three_gods else True
            if self.win_result.player_status[playerid].has_three_gods:
                legal_actions.append(1)
            elif self.hand_checker.BaseHu_Checker(self.hand_manager.players_hand[playerid]['hand']):
                legal_actions.append(1)
                self.win_result.category = 0

            # 检查出牌
            hand_counts = self.hand_manager.players_hand[playerid]['hand'][:, :, 0]
            val = np.where(hand_counts[3, 0:6] == 1)[0]
            cgod, vgod = divmod(self.game_state.current_god_id, 9)
            if val.size > 0: # or (hand_counts[cgod, vgod] > 0 and 27 <= self.game_state.current_god_id < 33): # 优先打出单张字牌以及前端的代替白板的数字牌（除了白板）
                for v in val:
                    tile_id = 3 * 9 + v
                    if tile_id < 34: # 排除掉 4x9 矩阵中最后多出的位（理论上没有）
                        legal_actions.append(tile_id + 2)
                # if (hand_counts[cgod, vgod] > 0 and 27 <= self.game_state.current_god_id < 33):
                #     legal_actions.append(self.game_state.current_god_id + 2)
                if hand_counts[3, 6] > 0 and 27 <= self.game_state.current_god_id < 33:
                    legal_actions.append(33 + 2)
            else:
                col, val = np.where(hand_counts > 0)
                for c, v in zip(col, val):
                    tile_id = c * 9 + v
                    if tile_id < 34: # 排除掉 4x9 矩阵中最后多出的位（理论上没有）
                        legal_actions.append(tile_id + 2) 
            
            # 检查暗杠
            rows, cols = np.where(hand_counts == 4)
            for c, v in zip(rows, cols):
                tile_id = c * 9 + v
                if tile_id < 34:
                    legal_actions.append(tile_id + 36)

            # 检查补杠
            pong_melds = self.hand_manager.players_hand[playerid]['melds'][:, :, 1]
            can_bu_gang = np.logical_and(pong_melds > 0, hand_counts > 0)
            rows, cols = np.where(can_bu_gang)
            for c, v in zip(rows, cols):
                tile_id = c * 9 + v
                if tile_id < 34:
                    legal_actions.append(tile_id + 104)

        elif self.game_state.game_state == 1:
            # 响应阶段   检查胡牌 明杠 碰牌 吃牌 Pass
            last_tile_id = self.game_state.last_discard_tile_id
            last_player = self.game_state.current_player_index
            c, v = divmod(last_tile_id, 9)
            hand_counts = self.hand_manager.players_hand[playerid]['hand'][:, :, 0]
            tile_count = hand_counts[c, v]
            is_next_player = (last_player + 1) % 4 == playerid

            legal_actions.append(0)

            if playerid != self.game_state.current_player_index:
                # 检查胡牌
                if self.hand_checker.MixedHu_Checker(self.hand_manager.players_hand[playerid]['hand'], last_tile_id):
                    legal_actions.append(1)
                    self.win_result.category = 2
                
                # 检查明杠
                if tile_count == 3:
                    legal_actions.append(last_tile_id + 70)
                
                # 检查碰牌
                if tile_count == 2:
                    legal_actions.append(last_tile_id + 138)

                # 检查吃牌
                if is_next_player and c < 3:
                    chow_actions = self.get_legal_chow_actions(c, v, hand_counts)
                    legal_actions.extend(chow_actions)
                pass
            else:
                # 当前玩家仅检查八对胡
                self.win_result.player_status[playerid].has_eight_pairs = self.hand_checker.EightPair_Checker(self.hand_manager.players_hand[playerid])
                if self.win_result.player_status[playerid].has_eight_pairs:
                    legal_actions.append(1)

        elif self.game_state.game_state == 2:
            # 弃牌阶段   检查出牌
            hand_counts = self.hand_manager.players_hand[playerid]['hand'][:, :, 0]
            val = np.where(hand_counts[3, 0:6] == 1)[0]
            cgod, vgod = divmod(self.game_state.current_god_id, 9)
            if val.size > 0: # or (hand_counts[cgod, vgod] > 0 and 27 <= self.game_state.current_god_id < 33): # 优先打出单张字牌（除了白板）
                for v in val:
                    tile_id = 3 * 9 + v
                    if tile_id < 34: # 排除掉 4x9 矩阵中最后多出的位（理论上没有）
                        legal_actions.append(tile_id + 2)
                # if (hand_counts[cgod, vgod] > 0 and 27 <= self.game_state.current_god_id < 33):
                #     legal_actions.append(self.game_state.current_god_id + 2)
                if hand_counts[3, 6] > 0 and 27 <= self.game_state.current_god_id < 33:
                    legal_actions.append(33 + 2)
            else:
                col, val = np.where(hand_counts > 0)
                for c, v in zip(col, val):
                    tile_id = c * 9 + v
                    if tile_id < 34: # 排除掉 4x9 矩阵中最后多出的位（理论上没有）和白板
                        legal_actions.append(tile_id + 2)

        elif self.game_state.game_state == 4:
            # 抢杠胡阶段   检查胡牌 Pass
            # 注：phase不用3是因为抢杠胡阶段没有调用legal action进行判定，而是在摸牌阶段将game state设置为4进行判定
            # 实际上应为摸牌阶段的抢杠胡判定
            legal_actions.append(0)
            if self.hand_checker.MixedHu_Checker(self.hand_manager.players_hand[playerid]['hand'], self.game_state.last_discard_tile_id):
                legal_actions.append(1)

        return legal_actions
    
    def get_legal_chow_actions(self, c: int, v: int, hand_counts: np.ndarray) -> list:
        """获取合法的吃牌动作
        Args:
            c (int): 当前出牌所在的行
            v (int): 当前出牌所在的列
            hand_counts (np.ndarray): 玩家手牌
        Returns:
            List: 合法动作列表
        """
        actions = []
        offset = 172 + c * 21
        # 情况 1：手牌有 v+1, v+2 -> 组成 [v], v+1, v+2
        if v <= 6 and hand_counts[c, v+1] > 0 and hand_counts[c, v+2] > 0:
            actions.append(offset + v)
        # 情况 2：手牌有 v-1, v+1 -> 组成 v-1, [v], v+1
        if 1 <= v <= 7 and hand_counts[c, v-1] > 0 and hand_counts[c, v+1] > 0:
            actions.append(offset + (v - 1) + 7)
        # 情况 3：手牌有 v-2, v-1 -> 组成 v-2, v-1, [v]
        if v >= 2 and hand_counts[c, v-2] > 0 and hand_counts[c, v-1] > 0:
            actions.append(offset + (v - 2) + 14)
        return actions

    def draw_phase(self) -> int:
        """摸牌阶段，当前玩家从牌堆摸牌，并更新游戏状态和玩家手牌"""
        draw_card_id = self.hand_manager.draw_card(self.game_state.current_player_index)
        self.last_action = {"playerid": -1, "action_id": draw_card_id} # 记录摸牌动作
        if self.if_display and self.players_type[self.game_state.current_player_index] == 0:
            self.visualizer.draw_game(self.get_visible_state(self.game_state.current_player_index)) # 摸牌后立即可视化当前局面，包含摸牌动作
        self.game_state.draw_counter += 1
        # 检查是否流局：当牌堆剩余牌数不足以支持每位玩家再摸一次牌时，判定为流局
        if self.game_state.draw_counter - self.game_state.gang_counter >= 56:
            self.game_state.end_state = 2 # 流局
        self.action_manager.legal_action_list[self.game_state.current_player_index] = self.get_legal_actions(playerid=self.game_state.current_player_index)
        
        # 检查当前玩家是否有多个合法操作，如果有则询问玩家选择，否则直接执行唯一的合法操作
        self.last_action['playerid'] = self.game_state.current_player_index # 记录last_action的玩家id
        if len(self.action_manager.legal_action_list[self.game_state.current_player_index]) > 1 or self.players_type[self.game_state.current_player_index] == 0: # 有多个合法操作或者是人类玩家都需要选择
            self.action_manager.action_choosen[self.game_state.current_player_index] = self.players[self.game_state.current_player_index].choose_action(self.get_visible_state(self.game_state.current_player_index), self.action_manager.legal_action_list[self.game_state.current_player_index])
        else:
            self.action_manager.action_choosen[self.game_state.current_player_index] = self.action_manager.legal_action_list[self.game_state.current_player_index][0]
        self.last_action['action_id'] = self.action_manager.action_choosen[self.game_state.current_player_index] # 记录玩家选择的动作id

        if self.action_manager.action_choosen[self.game_state.current_player_index] == 1: # 胡牌
            self.win_result.hu_player_index = self.game_state.current_player_index
            # 摸牌阶段的胡牌不用把牌加入手牌，因为已经加入了
            self.game_state.end_state = 1
            return 0 # 无所谓多少
        elif 36 <= self.action_manager.action_choosen[self.game_state.current_player_index] <=69: # 暗杠
            self.win_result.category = 2
            self.game_state.gang_counter += 1
            self.win_result.tian_hu = False
            self.hand_manager.do_AnGang(self.game_state.current_player_index, self.action_manager.action_choosen[self.game_state.current_player_index] - 36)
            if self.if_display: # 这里暗杠之后的可视化是给人类玩家看的
                self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 暗杠后立即可视化当前局面，包含暗杠动作
            return 0 # 重新进入摸牌阶段
            # 这里说明暗杠之后直接进入摸牌阶段，也就是说visualizer并不会显示暗杠（暗杠那一条信息）
        elif 104 <= self.action_manager.action_choosen[self.game_state.current_player_index] <= 137: # 补杠
            self.win_result.category = 2
            self.game_state.last_discard_tile_id = self.action_manager.action_choosen[self.game_state.current_player_index] - 104
            self.hand_manager.remove_card(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
            if self.if_display: # 这里补杠之后的可视化是给人类玩家看的
                self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 补杠后立即可视化当前局面，包含补杠动作
            self.game_state.game_state = 4 # 设置为针对摸牌阶段的抢杠胡判定阶段
            for playerid in range(4): # 更新所有玩家的合法操作列表，检查是否有玩家可以抢杠胡
                self.action_manager.legal_action_list[playerid] = self.get_legal_actions(playerid=playerid)
            for pid, actions in self.action_manager.legal_action_list.items():
                if len(actions) > 1: # 标记能胡牌的玩家
                    self.action_manager.is_quested[pid] = True
            if any(self.action_manager.is_quested.values()):
                return 3 # 进入抢杠胡阶段
            else:
                self.hand_manager.do_BuGang(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
                self.game_state.gang_counter += 1
                return 0 # 重新进入摸牌阶段

        elif 2 <= self.action_manager.action_choosen[self.game_state.current_player_index] <= 35:
            self.win_result.category = 2
            if self.action_manager.action_choosen[self.game_state.current_player_index] == 33:
                self.win_result.player_status[self.game_state.current_player_index].has_three_gods = False
            self.win_result.tian_hu = False
            self.game_state.last_discard_tile_id = self.action_manager.action_choosen[self.game_state.current_player_index] - 2
            self.hand_manager.remove_card(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
            return 1 # 进入响应阶段

    def response_phase(self) -> int:
        """响应阶段，其他玩家根据当前玩家的操作进行响应，并更新游戏状态和玩家手牌"""
        if self.game_state.last_discard_tile_id != 33:
            for playerid in range(4):
                self.action_manager.legal_action_list[playerid] = self.get_legal_actions(playerid=playerid)
            for pid, actions in self.action_manager.legal_action_list.items():
                if (len(actions) > 1 or self.players_type[pid] == 0) and pid != self.game_state.current_player_index:
                    # 标记有多个合法操作的玩家或者人类玩家需要选择，且不是当前出牌的玩家才能进行询问
                    if self.if_display and self.players_type[pid] == 0:
                        self.visualizer.draw_game(self.get_visible_state(pid)) # 响应阶段询问玩家操作前先可视化当前局面，包含打牌动作
                    self.action_manager.is_quested[pid] = True
                    self.action_manager.action_choosen[pid] = self.players[pid].choose_action(self.get_visible_state(pid), actions)
            if any(self.action_manager.is_quested.values()):
                action_player_index, actionid = self.action_manager.judge_action_priority(self.game_state.current_player_index)
                self.action_manager.is_quested = {i: False for i in range(4)}
                if actionid != 1:
                    self.last_action['playerid'] = action_player_index
                    self.last_action['action_id'] = actionid 
                    # 当动作不是过牌时记录响应阶段的玩家动作，便于visualizer显示

                if actionid == 1: # 胡牌
                    self.win_result.hu_player_index = action_player_index
                    self.hand_manager.add_card(action_player_index, self.game_state.last_discard_tile_id) # 胡牌时把牌加回去
                    self.game_state.end_state = 1
                    return 0 # 无所谓多少
                elif 70 <= actionid <= 103: # 明杠
                    self.win_result.category = 2
                    self.game_state.gang_counter += 1
                    self.win_result.di_hu = False
                    self.hand_manager.do_MingGang(action_player_index, actionid - 70)
                    for pid in range(4):
                        self.win_result.player_status[pid].has_eight_pairs = False
                    if self.if_display: # 这里明杠之后的可视化是给人类玩家看的
                        self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 明杠后立即可视化当前局面，包含明杠动作
                    self.game_state.current_player_index = action_player_index
                    return 0 # 重新进入摸牌阶段
                elif 138 <= actionid <= 171:
                    self.win_result.category = 2
                    self.win_result.di_hu = False
                    self.hand_manager.do_Peng(action_player_index, actionid - 138)
                    self.game_state.current_player_index = action_player_index
                    for pid in range(4):
                        self.win_result.player_status[pid].has_eight_pairs = False
                    if self.if_display: # 这里碰牌之后的可视化是给人类玩家看的
                        self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 碰牌后立即可视化当前局面，包含碰牌动作
                    return 2 # 进入弃牌阶段
                elif 172 <= actionid <= 234:
                    self.win_result.category = 2
                    self.win_result.di_hu = False
                    self.hand_manager.do_Chi(action_player_index, actionid)
                    self.game_state.current_player_index = action_player_index
                    for pid in range(4):
                        self.win_result.player_status[pid].has_eight_pairs = False
                    if self.if_display: # 这里吃牌之后的可视化是给人类玩家看的
                        self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 吃牌后立即可视化当前局面，包含吃牌动作
                    return 2 # 进入弃牌阶段
                else: # 所有人都选择pass
                    self.win_result.di_hu = False
                    self.hand_manager.do_Discard(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
                    self.game_state.last_discard_tile_id = -1
                    self.game_state.current_player_index = (self.game_state.current_player_index + 1) % 4
                    if self.if_display: # 这里过牌之后的可视化是给人类玩家看的
                        self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 过牌不记录id，因此显示的是弃牌动画
                    return 0 # 进入摸牌阶段
            else:
                self.win_result.di_hu = False
                self.hand_manager.do_Discard(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
                self.game_state.last_discard_tile_id = -1
                self.game_state.current_player_index = (self.game_state.current_player_index + 1) % 4
                if self.if_display: # 这里无人响应的可视化是给人类玩家看的
                    self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 显示的是弃牌动画
                return 0 # 进入摸牌阶段
        else: # 如果打出的牌是财神牌，直接进入下一个玩家的摸牌阶段，不询问响应
            self.hand_manager.do_Discard(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
            self.game_state.last_discard_tile_id = -1
            self.game_state.current_player_index = (self.game_state.current_player_index + 1) % 4
            if self.if_display: # 这里打出财神牌之后的可视化是给人类玩家看的
                self.visualizer.draw_game(self.get_visible_state(self.players_type.index(0))) # 显示的是弃牌动画
            return 0 # 进入摸牌阶段

    def discard_phase(self) -> int:
        """弃牌阶段，当前玩家选择一张牌进行弃牌，并更新游戏状态和玩家手牌"""
        self.action_manager.legal_action_list[self.game_state.current_player_index] = self.get_legal_actions(playerid=self.game_state.current_player_index)
        self.last_action['playerid'] = self.game_state.current_player_index # 记录弃牌阶段的玩家id
        # 检查当前玩家是否有多个合法操作
        if len(self.action_manager.legal_action_list[self.game_state.current_player_index]) > 1 or self.players_type[self.game_state.current_player_index] == 0: # 有多个合法操作或者是人类玩家都需要选择
            self.action_manager.action_choosen[self.game_state.current_player_index] = self.players[self.game_state.current_player_index].choose_action(self.get_visible_state(self.game_state.current_player_index), self.action_manager.legal_action_list[self.game_state.current_player_index])
        else:
            self.action_manager.action_choosen[self.game_state.current_player_index] = self.action_manager.legal_action_list[self.game_state.current_player_index][0]
        self.last_action['action_id'] = self.action_manager.action_choosen[self.game_state.current_player_index] # 记录玩家选择的动作id

        if self.action_manager.action_choosen[self.game_state.current_player_index] == 33:
            self.win_result.player_status[self.game_state.current_player_index].has_three_gods = False
        self.game_state.last_discard_tile_id = self.action_manager.action_choosen[self.game_state.current_player_index] - 2
        self.hand_manager.remove_card(self.game_state.current_player_index, self.action_manager.action_choosen[self.game_state.current_player_index] - 2)
        return 1 # 进入响应阶段，此处不需要可视化是因为响应阶段的可视化会显示打牌动作

    def qiang_gang_hu_phase(self) -> int:
        """抢杠胡阶段，其他玩家根据当前玩家的杠牌操作进行抢杠胡响应，并更新游戏状态和玩家手牌"""
        for playerid in range(4):
            if self.action_manager.is_quested[playerid]:
                self.action_manager.action_choosen[playerid] = self.players[playerid].choose_action(self.get_visible_state(playerid), self.action_manager.legal_action_list[playerid])
        playerid, _ = self.action_manager.judge_action_priority(self.game_state.current_player_index)
        if playerid != -1:
            self.win_result.hu_player_index = playerid
            self.hand_manager.add_card(playerid, self.game_state.last_discard_tile_id)
            self.game_state.end_state = 1
            self.win_result.category = 1
            return 0 # 无所谓多少
        else:
            self.hand_manager.do_BuGang(self.game_state.current_player_index, self.game_state.last_discard_tile_id)
            self.game_state.gang_counter += 1
            return 0 # 重新进入摸牌阶段
        

    def get_visible_state(self, playerid: Literal[-1, 0, 1, 2, 3]) -> dict:
        """获取当前玩家可见的游戏状态信息，供玩家决策使用
        RL模型输入149维向量，包括：
        自己手牌 * 4
        每个人动作(吃 * 5 + 碰 * 1 + 明杠 * 1) * 4 个玩家
        自己暗杠 * 1
        每个人弃牌历史 28 * 4
        剩余牌 * 4
        财神牌 * 1
        阶段层 * 4
        Args:
            playerid (int): 目标玩家的索引，0-3分别代表四个玩家，-1表示结算时获取所有玩家状态
        Returns:
            dict: 包含当前玩家可见的游戏状态信息的字典
            - 'real_order': 真实上下家顺序（自己为1号玩家，如2号玩家视角下：0123 -> 2301）
            - 'god_id': 当前财神牌ID
            - 'hand': 当前玩家的手牌信息，4x9矩阵，表示每种牌的数量（不包括副露）
            - 'an_gang': 当前玩家的暗杠信息，4x9矩阵，表示每种牌是否暗杠
            - 'ming_gang': 每个玩家的明杠信息，4x9矩阵，表示每种牌是否明杠
            - 'an_gang_count': 每个玩家的暗杠数量
            - 'peng': 每个玩家的碰牌信息，4x9矩阵，表示每种牌是否碰牌
            - 'chi': 每个玩家的吃牌信息，4x9矩阵，表示吃牌数量（取顺子首张牌）
            - 'discards': 每个玩家的弃牌历史，长度为28的数组，表示每次弃牌的牌ID，初始值为-1
            - 'discard_ptr': 每个玩家的弃牌指针，整数表示当前弃牌历史中最新一张牌的位置
            - 'current_phase': 当前游戏阶段，整数表示不同阶段
            - 'remaining_tiles': 剩余牌数量，整数表示牌堆中剩余的牌数
            - 'is_banker': 是否为庄家，1表示是庄家，0表示非庄家
            - 'banker_index': 庄家索引，0-3分别代表四个玩家
            - 'basic_score': 当前底分，整数表示当前的底分值
            - 'last_action': 上一玩家和上一玩家执行的动作
            ---
            - 'players_hand': 
                所有玩家的完整手牌和副露信息
                仅在playerid = -1 时返回且playerid = -1 仅返回这个值
                包含每个玩家的手牌、明杠、暗杠、碰牌、吃牌和弃牌信息
        """
        if playerid != -1:
            real_order = [(playerid + i) % 4 for i in range(4)]
            visible_state = {
                'real_order': real_order,
                'god_id': self.game_state.current_god_id,
                'hand': self.hand_manager.players_hand[playerid]['hand'][:, :, 0],
                'an_gang': self.hand_manager.players_hand[playerid]['melds'][:, :, 3],
                'ming_gang': {i: self.hand_manager.players_hand[i]['melds'][:, :, 2] for i in range(4)},
                'an_gang_count':{i: int(np.sum(self.hand_manager.players_hand[i]['melds'][:, :, 3])) for i in range(4)},
                'peng': {i: self.hand_manager.players_hand[i]['melds'][:, :, 1] for i in range(4)},
                'chi': {i: self.hand_manager.players_hand[i]['melds'][:, :, 0] for i in range(4)},
                'discards': {i: self.hand_manager.players_hand[i]['discards'] for i in range(4)},
                'discard_ptr': {i: self.hand_manager.players_hand[i]['discard_ptr'] for i in range(4)},
                'current_phase': self.game_state.game_state,
                'remaining_tiles': (56 - (self.game_state.draw_counter - self.game_state.gang_counter)) / 56,
                'is_banker': 1 if playerid == self.banker_index else 0,
                'banker_index': self.banker_index,
                'basic_score': self.game_state.current_score,
                'last_action': self.last_action
            }
        else:
            visible_state = {i: self.hand_manager.players_hand[i] for i in range(4)}
        return visible_state