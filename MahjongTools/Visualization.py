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

TILE_NAMES = [
        ["一万", "两万", "三万", "四万", "五万", "六万", "七万", "八万", "九万"],
        ["一条", "两条", "三条", "四条", "五条", "六条", "七条", "八条", "九条"],
        ["一筒", "两筒", "三筒", "四筒", "五筒", "六筒", "七筒", "八筒", "九筒"],
        ["东风", "南风", "西风", "北风", "红中", "发财", "白板", "", ""]
    ]

class EngineVisualization:
    """游戏过程可视化类，负责将当前局面在命令行画出来"""
    def __init__(self):
        pass
    
    def display_game_state(self, game_state: dict) -> None:
        """显示当前游戏状态，包括玩家手牌、牌墙剩余牌数、当前玩家等信息
        Args:
            game_state: 当前游戏状态对象，从MahjongEngine的get_visible_state方法获取"""
        player_meld = {i: {} for i in range(3)} # 按相对玩家的位置信息存储每个(第三方)玩家的牌面信息
        current_player_meld = self.format_player_meld(game_state['real_order'][0], game_state, True)
        for i in range(3):
            player_meld[i] = self.format_player_meld(game_state['real_order'][i+1], game_state, False)
        print("当前庄家玩家: 玩家", game_state['banker_index'],"，当前底分:", game_state['basic_score'])
        print("牌墙剩余牌数: ", int(game_state['remaining_tiles'] * 56), "，当前财神牌: ", TILE_NAMES[game_state['god_id']//9][game_state['god_id']%9])
        print("--------------------")
        print("对家: 玩家", game_state['real_order'][2])
        print("碰牌: ", player_meld[1]['peng'])
        print("吃牌: ", player_meld[1]['chi'])
        print("明杠: ", player_meld[1]['ming_gang'])
        print("暗杠数量: ", player_meld[1]['an_gang_count'])
        print("弃牌: ", player_meld[1]['discards'])
        print("--------------------")
        print("上家: 玩家", game_state['real_order'][3])
        print("碰牌: ", player_meld[2]['peng'])
        print("吃牌: ", player_meld[2]['chi'])
        print("明杠: ", player_meld[2]['ming_gang'])
        print("暗杠数量: ", player_meld[2]['an_gang_count'])
        print("弃牌: ", player_meld[2]['discards'])
        print("--------------------")
        print("下家: 玩家", game_state['real_order'][1])
        print("碰牌: ", player_meld[0]['peng'])
        print("吃牌: ", player_meld[0]['chi'])
        print("明杠: ", player_meld[0]['ming_gang'])
        print("暗杠数量: ", player_meld[0]['an_gang_count'])
        print("弃牌: ", player_meld[0]['discards'])
        print("--------------------")
        print("当前玩家: 玩家", game_state['real_order'][0])
        print("手牌: ", current_player_meld['hand'])
        print("碰牌: ", current_player_meld['peng'])
        print("吃牌: ", current_player_meld['chi'])
        print("明杠: ", current_player_meld['ming_gang'])
        print("暗杠: ", current_player_meld['an_gang'])
        print("弃牌: ", current_player_meld['discards'])
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
                    meld['peng'].append(TILE_NAMES[c][v])
        # 转换明杠信息
        ming_gang = state['ming_gang'][playerid]
        meld.setdefault('ming_gang', [])
        for c in range(4):
            for v in range(9):
                if ming_gang[c][v]:
                    meld['ming_gang'].append(TILE_NAMES[c][v])
        # 转换弃牌信息
        discards = state['discards'][playerid][:state['discard_ptr'][playerid]]
        meld.setdefault('discards', [])
        for tile_id in discards:
            if tile_id == -1:
                continue # 一般不会遇到-1，保险起见留一下
            c = tile_id // 9
            v = tile_id % 9
            meld['discards'].append(TILE_NAMES[c][v])
        # 转换吃牌信息
        meld.setdefault('chi', [])
        chi = state['chi'][playerid]
        for c in range(3):
            for v in range(7):
                count = chi[c][v]
                for _ in range(count):
                    meld['chi'].append(f"{TILE_NAMES[c][v]},{TILE_NAMES[c][v+1]},{TILE_NAMES[c][v+2]}") # 吃牌显示为三个牌的组合
        # 转换暗杠数量
        meld['an_gang_count'] = state['an_gang_count'][playerid]
        
        if is_current_player:
            # 转换自己暗杠信息
            meld['an_gang'] = []
            an_gang = state['an_gang']
            for c in range(4):
                for v in range(9):
                    if an_gang[c][v]:
                        meld['an_gang'].append(TILE_NAMES[c][v])
            # 转换自己手牌信息
            meld['hand'] = []
            hand = state['hand']
            for c in range(4):
                for v in range(9):
                    count = int(hand[c][v])
                    meld['hand'].extend([TILE_NAMES[c][v]] * count)
        else:
            meld['an_gang'] = [] # 暗杠信息不显示具体牌面，只显示数量

        return meld
    
    def display_last_action(self, action: int) -> None:
        """显示上一个玩家的动作，包括动作类型和涉及的牌面信息
        Args:
            action(int): 上一个玩家的动作编码，整数表示不同的动作类型和牌面信息"""
        pass