# 麻将手牌检查器
import numpy as np
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "config", "shanten_map", "wenzhou_v2_256.bin"))


class HandChecker:
    """麻将手牌检查器"""

    def __init__(self):
        self.Complete_Hand = np.zeros((4, 9), dtype=int)
        self.SHANTEN_TABLE = np.fromfile(BIN_PATH, dtype=np.uint16)
        self.ZIPAI_TABLE = np.array([
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 1, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])

    def get_hand_score(self, hand: np.ndarray, is_num: bool, is_god_inplace: bool = False) -> tuple[int, int, int, int]:
        """获取手牌的最优组数
        Args:
            hand (np.ndarray): 玩家手牌，包括副露信息
            is_num (bool): 是否为数字牌
            is_god_inplace (bool): 是否检查财神归位
        Returns:
            tuple (int, int, int, int): 包含刻子数、顺子数、对子数和单牌数的元组
            - 刻子数
            - 顺子数
            - 缺张刻数
            - 缺张顺数"""
        c = hand.flatten().astype(np.int32) # 1. 扁平化并转为整数，提取 9 位张数；如果 hand 是 (9, 1)，flatten 后变为 (9,)
        if is_num:  # 2. 构造 27-bit Key；逻辑：每种牌占 3 位，对应 C 语言中的 (cards[i] & 0x07) << (i * 3)
            key = (
                (c[0] & 0x07)       | ((c[1] & 0x07) << 3)  | ((c[2] & 0x07) << 6) |
                ((c[3] & 0x07) << 9)  | ((c[4] & 0x07) << 12) | ((c[5] & 0x07) << 15) |
                ((c[6] & 0x07) << 18) | ((c[7] & 0x07) << 21) | ((c[8] & 0x07) << 24)
            )
            res = self.SHANTEN_TABLE[key]   # 3. 查表并解析结果 (对应 C 语言中的位域存储格式)
            # bmk: 0-2, bms: 3-5, bp: 6-8, bd: 9-10
            mk = int(res & 0x07)           # 刻子数
            ms = int((res >> 3) & 0x07)    # 顺子数
            p  = int((res >> 6) & 0x07)    # 缺张刻数 (对子)
            d  = int((res >> 9) & 0x03)    # 缺张顺数 (搭子)
            return mk, ms, p, d
        else:
            # 字牌直接查表，剔除白板
            mks, mss, ps, ds = 0, 0, 0, 0
            for i in range(6 if is_god_inplace else 7): # 如果检查财神归位，则不考虑财神牌（id 33，对应 hand[3][6]），否则考虑所有字牌
                mks += self.ZIPAI_TABLE[c[i], 0]
                mss += self.ZIPAI_TABLE[c[i], 1]
                ps  += self.ZIPAI_TABLE[c[i], 2]
                ds  += self.ZIPAI_TABLE[c[i], 3]
            return mks, mss, ps, ds
        
    def get_shanten_num(self, hand: np.ndarray, is_god_inplace: bool = False) -> int:
        """检查向听数
        Args:
            hand: 玩家手牌，包括副露信息
            is_god_inplace (bool): 是否检查财神归位
        Returns:
            int: 听牌分数"""
        slot = hand.sum() // 3
        score = slot * 2
        total = np.zeros(4, dtype=int)
        for i in range(4):
            if np.any(hand[i]): # 如果该花色有牌
                total += self.get_hand_score(hand[i], i < 3, is_god_inplace)
        tmk, tms, tp, td = total
        has_pair = int(tp > 0)
        slot -= tmk + tms
        score -= ((tmk + tms) * 2 +                 # 去掉刻子和顺子带来的分数
                  int(hand[3, 6]) +       # 去掉财神带来的分数
                  min((tp - has_pair) + td, slot) + # 去掉缺张带来的分数，该分数最多为剩余槽位数，且缺张刻-1（如有，当作雀头）
                  has_pair)                         # 去掉雀头带来的分数（如有）
        return score
    
    def EightPair_Checker(self, hand: dict[str, np.ndarray]) -> bool:
        """检查是否为八对"""
        hand_metrix = hand['hand']
        if np.sum(hand_metrix) == 16:
            god_count = hand_metrix[3, 6, 0] # 财神id为33，对应位置为hand[3][6]
            odd_count = (hand_metrix % 2).sum() - god_count % 2 # 计算手牌中单牌的数量
            if god_count >= odd_count and (god_count - odd_count) % 2 == 0:
                return True
        else:
            return False

    def ThreeGods_Checker(self, hand: dict[str, np.ndarray]) -> bool:
        """检查是否为三财神
        Args:
            hand: 玩家手牌，包括副露信息
        Returns:
            bool: 如果满足三财神条件则返回True，否则返回False"""
        return hand['hand'][3, 6, 0] >= 3 # 财神id为33，对应位置为hand[3][6]

    def BaseHu_Checker(self, hand: np.ndarray) -> bool:
        return self.get_shanten_num(hand, False) == -1

    def MixedHu_Checker(self, hand: np.ndarray, cardid: int) -> bool:
        """检查吃牌时的基本胡牌牌型
        Args:
            hand: 玩家手牌，包括副露信息
            cardid: 吃牌的牌ID
        Returns:
            bool: 如果满足基本胡牌条件则返回True，否则返回False"""
        hand[cardid // 9, cardid % 9, 0] += 1 # 临时添加吃牌到手牌中进行检查
        result = self.get_shanten_num(hand, False) == -1
        hand[cardid // 9, cardid % 9, 0] -= 1 # 恢复手牌
        return result
    
    def God_inplace_Checker(self, god_id: int, hand: np.ndarray) -> bool:
        """检查财神是否归位
        Args:
            god_id (int): 财神ID
            hand (np.ndarray): 玩家手牌
        Returns:
            bool: 如果财神归位则返回True，否则返回False"""
        god_num = hand[3, 6] # 财神id为33，对应位置为hand[3][6]
        hand[3, 6] = hand[god_id // 9, god_id % 9]
        hand[god_id // 9, god_id % 9] = god_num
        result = self.get_shanten_num(hand, True) == -1
        hand[god_id // 9, god_id % 9] = hand[3, 6] # 恢复手牌
        hand[3, 6] = god_num
        return result