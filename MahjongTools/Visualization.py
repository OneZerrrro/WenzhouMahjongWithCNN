# Todo
# 负责将当前局面在命令行画出来
# 先规定一下Human的命令显示格式，当前动作表如下：
# -----------------------------------
# 000 过牌 001 胡牌
# 弃牌：万 002-010  条 011-019  筒 020-028  字 029-035  +002
# 暗杠：万 036-044  条 045-053  筒 054-062  字 063-069  +036
# 明杠：万 070-078  条 079-087  筒 088-096  字 097-103  +070
# 补牌：万 104-112  条 113-121  筒 122-130  字 131-137  +104
# 碰牌：万 138-146  条 147-155  筒 156-164  字 165-171  +138
# 吃牌：万 172-192  条 193-213  筒 214-234
# 吃牌映射表：
# 万 +0  条 +21  筒 +42
# +00 - +06：[v] v+1 v+2    +00  ->  172: 万二三吃一  173: 万三四吃二 ...
# +07 - +13：v-1 [v] v+1    +07  ->  179: 万一三吃二  180: 万二四吃三 ...
# +14 - +20：v-2 v-1 [v]    +14  ->  186: 万一二吃三  187: 万二三吃四 ...
# -----------------------------------
# 情况如下：
# 统计当前玩家所有可能的动作数量，并且将原先有空缺的动作映射到连续的数字上，例如：
# 当前玩家有以下合法动作：
# 胡牌(001)，弃牌(002, 003, 004)，暗杠(036)，补牌(113)
# 那么我们就将这些动作映射到连续的数字上：
# 胡牌(001)，弃牌(002, 003, 004)，暗杠(005)，补牌(006)

import numpy as np
import os
from copy import deepcopy
import time

TILE_NAMES = [
        ["一萬", "二萬", "三萬", "四萬", "伍萬", "六萬", "七萬", "八萬", "九萬"],
        ["一條", "二條", "三條", "四條", "伍條", "六條", "七條", "八條", "九條"],
        ["一筒", "二筒", "三筒", "四筒", "伍筒", "六筒", "七筒", "八筒", "九筒"],
        ["東風", "南風", "西風", "北風", "紅中", "發財", "白板", "", ""]
    ]

class EngineVisualization:
    """游戏过程可视化类，负责将当前局面在命令行画出来"""
    def __init__(self):
        self.true_tile_names = TILE_NAMES
    
    def reset(self, god_id: int) -> None:
        """重置可视化状态"""
        self.true_tile_names = deepcopy(TILE_NAMES)
        god_tile_name = TILE_NAMES[god_id//9][god_id%9]
        self.true_tile_names[god_id//9][god_id%9] = "白板"
        self.true_tile_names[3][6] = god_tile_name # 将财神牌显示为白板，原本的财神牌信息放在白板位置
        return

    def draw_game(self, game_state: dict) -> None:
        """绘制当前游戏状态，包括玩家手牌、牌墙剩余牌数、当前玩家等信息
        Args:
            game_state: 当前游戏状态对象，从MahjongEngine的get_visible_state方法获取"""
        os.system('cls' if os.name == 'nt' else 'clear') # 每次绘制前先清屏，保持界面整洁
        self.display_game_state(game_state)
        self.display_last_action(game_state['last_action'])
        time.sleep(1)
        return

    def display_game_state(self, game_state: dict) -> None:
        """显示当前游戏状态，包括玩家手牌、牌墙剩余牌数、当前玩家等信息
        Args:
            game_state: 当前游戏状态对象，从MahjongEngine的get_visible_state方法获取"""
        game_state = deepcopy(game_state) # 避免修改原始游戏状态对象
        player_meld = {i: {} for i in range(3)} # 按相对玩家的位置信息存储每个(第三方)玩家的牌面信息
        current_player_meld = self.format_player_meld(game_state['real_order'][0], game_state, True)
        # 手牌中将财神牌和白板牌的数量交换位置，以正确显示信息
        # god_num = game_state['hand'][game_state['god_id']//9][game_state['god_id']%9]
        # game_state['hand'][game_state['god_id']//9][game_state['god_id']%9] = game_state['hand'][3][6]
        # game_state['hand'][3][6] = god_num
        for i in range(3):
            player_meld[i] = self.format_player_meld(game_state['real_order'][i+1], game_state, False)
        print("当前庄家玩家: 玩家", game_state['banker_index'], "，当前底分: ", game_state['basic_score'])
        print("牌墙剩余牌数: ", int(game_state['remaining_tiles'] * 56), "，当前财神牌: ", TILE_NAMES[game_state['god_id']//9][game_state['god_id']%9])
        print("--------------------")
        print_name_map = {0: "下", 1: "对", 2: "上"}
        for i in range(3):
            j = (i + 1) % 3
            total_vertical = [["副", " "], ["露", " "]]
            discard_vertical = [["弃", " "], ["牌", " "]]
            print(f"{print_name_map[j]}家: 玩家", game_state['real_order'][j+1])
            if player_meld[j]['peng']:                  self.format_and_add_meld_to_vertical(total_vertical, player_meld[j]['peng'], 'peng') # print("碰牌: ", player_meld[j]['peng'])
            if player_meld[j]['chi']:                   self.format_and_add_meld_to_vertical(total_vertical, player_meld[j]['chi'], 'chi') # print("吃牌: ", player_meld[j]['chi'])
            if player_meld[j]['ming_gang']:             self.format_and_add_meld_to_vertical(total_vertical, player_meld[j]['ming_gang'], 'ming_gang') # print("明杠: ", player_meld[j]['ming_gang'])
            if total_vertical[0]:                       print("".join(total_vertical[0]))
            if total_vertical[1]:                       print("".join(total_vertical[1]))
            if player_meld[j]['an_gang_count'] > 0:     print("暗杠数量: ", player_meld[j]['an_gang_count'])
            if player_meld[j]['discards']:              self.format_and_add_meld_to_vertical(discard_vertical, player_meld[j]['discards'], 'discards') # print("弃牌: ", player_meld[j]['discards'])
            if discard_vertical[0]:                     print("".join(discard_vertical[0]))
            if discard_vertical[1]:                     print("".join(discard_vertical[1]))
            print("--------------------")
        print("当前玩家: 玩家", game_state['real_order'][0])
        hand_vertical = [["手", " "], ["牌", " "]]
        total_vertical = [["副", " "], ["露", " "]]
        discard_vertical = [["弃", " "], ["牌", " "]]
        self.format_and_add_meld_to_vertical(hand_vertical, current_player_meld['hand'], 'hand') # print("手牌: ", current_player_meld['hand'])
        if current_player_meld['peng']:         self.format_and_add_meld_to_vertical(total_vertical, current_player_meld['peng'], 'peng') # print("碰牌: ", current_player_meld['peng'])
        if current_player_meld['chi']:          self.format_and_add_meld_to_vertical(total_vertical, current_player_meld['chi'], 'chi') # print("吃牌: ", current_player_meld['chi'])
        if current_player_meld['ming_gang']:    self.format_and_add_meld_to_vertical(total_vertical, current_player_meld['ming_gang'], 'ming_gang') # print("明杠: ", current_player_meld['ming_gang'])
        if current_player_meld['an_gang']:      self.format_and_add_meld_to_vertical(total_vertical, current_player_meld['an_gang'], 'an_gang') # print("暗杠: ", current_player_meld['an_gang'])
        if current_player_meld['discards']:     self.format_and_add_meld_to_vertical(discard_vertical, current_player_meld['discards'], 'discards') # print("弃牌: ", current_player_meld['discards'])
        print("".join(hand_vertical[0]))
        print("".join(hand_vertical[1]))
        if total_vertical[0]:                      print("".join(total_vertical[0]))
        if total_vertical[1]:                      print("".join(total_vertical[1]))
        if discard_vertical[0]:                    print("".join(discard_vertical[0]))
        if discard_vertical[1]:                    print("".join(discard_vertical[1]))
        print("--------------------")
        return

    def format_player_meld(self, playerid: int, state: dict, is_current_player: bool) -> dict[str, int | list]:
        """格式化收到的手牌并转换成人能看得懂的形式并返回
        Args:
            playerid(int): 玩家ID，0-3
            state(dict): 当前游戏状态对象
            is_current_player(bool): 是否为当前玩家，True表示是当前玩家，False表示其他玩家
        Returns:
            meld(dict): 包含玩家手牌、碰牌、杠牌、吃牌等的字典"""
        meld = {}
        # 转换碰牌信息
        meld.setdefault('peng', [])
        peng = state['peng'][playerid]
        for c in range(4):
            for v in range(9):
                if peng[c][v]:
                    meld['peng'].append(self.true_tile_names[c][v])
        # 转换明杠信息
        ming_gang = state['ming_gang'][playerid]
        meld.setdefault('ming_gang', [])
        for c in range(4):
            for v in range(9):
                if ming_gang[c][v]:
                    meld['ming_gang'].append(self.true_tile_names[c][v])
        # 转换弃牌信息
        discards = state['discards'][playerid][:state['discard_ptr'][playerid]]
        meld.setdefault('discards', [])
        for tile_id in discards:
            if tile_id == -1:
                continue # 一般不会遇到-1，保险起见留一下
            c = tile_id // 9
            v = tile_id % 9
            meld['discards'].append(self.true_tile_names[c][v])
        # 转换吃牌信息
        meld.setdefault('chi', [])
        chi = state['chi'][playerid]
        for c in range(3):
            for v in range(7):
                count = chi[c][v]
                for _ in range(count):
                    meld['chi'].append(f"{self.true_tile_names[c][v]},{self.true_tile_names[c][v+1]},{self.true_tile_names[c][v+2]}") # 吃牌显示为三个牌的组合
        # 转换暗杠数量
        meld['an_gang_count'] = state['an_gang_count'][playerid]
        
        if is_current_player:
            # 转换自己暗杠信息
            meld['an_gang'] = []
            an_gang = state['an_gang']
            for c in range(4):
                for v in range(9):
                    if an_gang[c][v]:
                        meld['an_gang'].append(self.true_tile_names[c][v])
            # 转换自己手牌信息
            meld['hand'] = []
            hand = state['hand']
            for c in range(4):
                for v in range(9):
                    count = int(hand[c][v])
                    meld['hand'].extend([self.true_tile_names[c][v]] * count)
        else:
            meld['an_gang'] = [] # 暗杠信息不显示具体牌面，只显示数量

        return meld
    
    def display_last_action(self, last_action: dict[str, int | None]) -> None:
        """显示上一个玩家的动作，包括动作类型和涉及的牌面信息
        Args:
            last_action(dict): 上一个玩家的动作信息，包含动作类型和涉及的牌面信息"""
        if last_action['playerid'] is None:
            print("各家摸牌完毕，正在判定三财神、八对...")
            return # 出现在游戏开始时判定三财神、八对的情况
        if last_action['playerid'] == -1:
            print("当前玩家摸牌  ", self.true_tile_names[last_action['action_id']//9][last_action['action_id']%9])
        else:
            print(f"刚刚玩家{last_action['playerid']}", end="")
            if last_action['action_id'] == 0:
                print("过牌") # 正常不应该触发这个
            elif last_action['action_id'] == 1:
                print("胡牌") # 正常不应该触发这个
            elif 2 <= last_action['action_id'] <= 35:
                print("弃掉了", self.true_tile_names[(last_action['action_id']-2)//9][(last_action['action_id']-2)%9])
            elif 36 <= last_action['action_id'] <= 69:
                print("暗杠") # 不可显示具体牌面信息
            elif 70 <= last_action['action_id'] <= 103:
                print("明杠了", self.true_tile_names[(last_action['action_id']-70)//9][(last_action['action_id']-70)%9])
            elif 104 <= last_action['action_id'] <= 137:
                print("补杠了", self.true_tile_names[(last_action['action_id']-104)//9][(last_action['action_id']-104)%9]) # 正常不应该触发这个
            elif 138 <= last_action['action_id'] <= 171:
                print("碰了", self.true_tile_names[(last_action['action_id']-138)//9][(last_action['action_id']-138)%9])
            elif 172 <= last_action['action_id'] <= 234:
                chi_card_type = (last_action['action_id'] - 172) // 21 # 0-2分别对应万条筒
                chi_card_class = (last_action['action_id'] - 172) % 21 # 对应吃牌的三种组合
                if chi_card_class <= 6:
                    print("用", self.true_tile_names[chi_card_type][chi_card_class + 1], "和", self.true_tile_names[chi_card_type][chi_card_class + 2], "吃了", self.true_tile_names[chi_card_type][chi_card_class])
                elif 7 <= chi_card_class <= 13:
                    print("用", self.true_tile_names[chi_card_type][chi_card_class - 7], "和", self.true_tile_names[chi_card_type][chi_card_class - 5], "吃了", self.true_tile_names[chi_card_type][chi_card_class - 6])
                else:
                    print("用", self.true_tile_names[chi_card_type][chi_card_class - 14], "和", self.true_tile_names[chi_card_type][chi_card_class - 13], "吃了", self.true_tile_names[chi_card_type][chi_card_class - 12])
        print("--------------------")
        return
    
    @staticmethod
    def format_and_add_meld_to_vertical(total_vertical: list[list[str]], meld: list[str], meld_type: str) -> None:
        """将碰牌、杠牌、吃牌等信息格式化为竖排显示的字符串，方便在命令行中展示
        Args:
            total_vertical(list): 已有的竖排显示字符串
            meld(list): 包含玩家碰牌、杠牌、吃牌等信息的列表，元素为字符串形式的牌面信息
            meld_type(str): 牌型，'peng'表示碰牌，'chi'表示吃牌，'ming_gang'表示明杠，'discards'表示弃牌，'hand'表示手牌，'an_gang'表示暗杠
        Returns:
            None"""
        if total_vertical:
            total_vertical[0].append("  ")
            total_vertical[1].append("  ")
        if meld_type == 'peng':
            for tile in meld:
                for i in range(6):
                    total_vertical[i//3].append(tile[i//3])
                    total_vertical[i//3].append(" ")
        elif meld_type == 'ming_gang' or meld_type == 'an_gang':
            for tile in meld:
                if meld_type == 'an_gang':
                    total_vertical[0].append("[ ")
                    total_vertical[1].append("[ ")
                for i in range(8):
                    total_vertical[i//4].append(tile[i//4])
                    total_vertical[i//4].append(" ")
                if meld_type == 'an_gang':
                    total_vertical[0].append("]")
                    total_vertical[1].append("]")
        elif meld_type == 'discards' or meld_type == 'hand':
            for tile in meld:
                total_vertical[0].append(tile[0])
                total_vertical[0].append(" ")
                total_vertical[1].append(tile[1])
                total_vertical[1].append(" ")
        else:
            for tile in meld:
                parts = tile.split(",")
                for i in range(6):
                    total_vertical[i//3].append(parts[i%3][i//3])
                    total_vertical[i//3].append(" ")
        return