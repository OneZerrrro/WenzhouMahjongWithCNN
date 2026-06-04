# 手牌生成器

from numpy import random
import numpy as np
from numpy.typing import NDArray
from typing import Literal, Any
from MahjongTools.HandCheckers import HandChecker

class HandGenerator:
    """手牌生成器类，负责生成符合条件的手牌
    - .generate_hand(target_shanten): 生成（对第一层指定向听数的）手牌"""
    def __init__(self):
        self.checker = HandChecker()  # 注入手牌检查器，用于计算向听数

        self.full_wall = np.full((4, 9), 4, dtype=int)
        """温州麻将全手牌，去掉一张白牌"""
        self.full_wall[3, 7:] = 0
        self.full_wall[3, 6] = 3
        self.player_hand = np.zeros((4, 9, 4), dtype=int)

    def add_triple(self, pool_matrix, hand_matrix):
        r"""添加一个刻子
        Args:
            pool_matrix (np.ndarray): 当前牌池矩阵，`4*9`
            hand_matrix (np.ndarray): 当前手牌矩阵，`4*9*4`
        Returns:
            None: 直接操作数组"""
        candidates = np.argwhere(pool_matrix >= 3)
        candidates = [c for c in candidates if not (c[0]==3 and c[1]==6)]
        if len(candidates) == 0: return None
        choice = np.random.randint(0, len(candidates))
        pool_matrix[candidates[choice][0], candidates[choice][1]] -= 3
        hand_matrix[candidates[choice][0], candidates[choice][1], 0] += 3
        return

    def add_sequence(self, pool_matrix, hand_matrix):
        r"""添加一个顺子
        Args:
            pool_matrix (np.ndarray): 当前牌池矩阵，`4*9`
            hand_matrix (np.ndarray): 当前手牌矩阵，`4*9*4`
        Returns:
            None: 直接操作数组"""
        candidates = []
        for color in range(3):
            for value in range(7):
                if pool_matrix[color, value] > 0 and pool_matrix[color, value+1] > 0 and pool_matrix[color, value+2] > 0:
                    candidates.append((color, value))
        if len(candidates) == 0: return None
        choice = np.random.randint(0, len(candidates))
        pool_matrix[candidates[choice][0], candidates[choice][1]:candidates[choice][1]+3] -= 1
        hand_matrix[candidates[choice][0], candidates[choice][1]:candidates[choice][1]+3, 0] += 1
        return

    def add_pair(self, pool_matrix, hand_matrix):
        r"""添加一个对子
        Args:
            pool_matrix (np.ndarray): 当前牌池矩阵，`4*9`
            hand_matrix (np.ndarray): 当前手牌矩阵，`4*9*4`
        Returns:
            None: 直接操作数组"""
        candidates = np.argwhere(pool_matrix >= 2)
        candidates = [c for c in candidates if not (c[0]==3 and c[1]==6)]
        if len(candidates) == 0: return None
        choice = np.random.randint(0, len(candidates))
        pool_matrix[candidates[choice][0], candidates[choice][1]] -= 2
        hand_matrix[candidates[choice][0], candidates[choice][1], 0] += 2
        return
    
    def get_one_card(self, target, pool_matrix, hand_matrix, level):
        r"""从牌池中拿取一张牌
        Args:
            target (int, int): 目标手牌坐标
            pool_matrix (np.ndarray): 当前牌池矩阵，`4*9`
            hand_matrix (np.ndarray): 当前手牌矩阵，`4*9*4`
            level (int): 操作的手牌层数
        Returns:
            None: 直接操作数组"""
        hand_matrix[target[0], target[1], level] +=1
        pool_matrix[target[0], target[1]] -=1
        return
    
    def generate_tenpai_hand(self, pool, player_hand): 
        # 并非严格按照数学概率生成，但是能用，而且差的应该不是很多。
        r"""生成一个听牌手牌，向听数为0
        Args:
            pool (np.ndarray): 当前牌池矩阵，`4*9`
            player_hand (np.ndarray): 当前玩家手牌矩阵，`4*9*4`
        Returns:
            None: 直接修改输入的player_hand和pool矩阵，生成一个听牌手牌
        """
        num_triples = random.randint(0, 6)
        # 生成num_triples个刻子，5-num_triples个顺子，1个对子
        # 随机丢弃掉一张牌，保证生成的牌型是听牌的 且不包含白板
        for _ in range(num_triples):
            self.add_triple(pool, player_hand)
        for _ in range(5-num_triples):
            self.add_sequence(pool, player_hand)
        self.add_pair(pool, player_hand)
        drop_candidates = np.argwhere(pool > 0)
        choice = np.random.randint(0, len(drop_candidates))
        player_hand[drop_candidates[choice][0], drop_candidates[choice][1], 0] -= 1
        pool[drop_candidates[choice][0], drop_candidates[choice][1]] += 1

        # 换三张财神进去，模拟摸到了财神
        counts = np.array([1642914, 126378, 2142, 6])
        probabilities = counts / counts.sum()
        for _ in range(np.random.choice([0, 1, 2, 3], size=1, p=probabilities)[0]):
            candidates = np.argwhere(player_hand >= 1)
            candidates = [c for c in candidates if not (c[0]==3 and c[1]==6)]
            choice = np.random.randint(0, len(candidates))
            player_hand[candidates[choice][0], candidates[choice][1], 0] -= 1
            pool[candidates[choice][0], candidates[choice][1]] += 1
            self.get_one_card((3, 6), pool, player_hand, 0)
        return # 听牌牌型肯定能生成成功的
    
    def add_one_shanten_to_hand(self, pool: NDArray[Any], player_hand: NDArray[Any]):
        r"""对当前手牌增加一层向听数
        Args:
            pool (np.ndarray): 当前牌池矩阵，`4*9`
            player_hand (np.ndarray): 当前玩家手牌矩阵，`4*9*4`
        Returns:
            None: 直接修改输入的player_hand和pool矩阵，增加1向听数"""
        base_shanten_number = self.checker.get_shanten_num(player_hand[:, :, 0])
        hand_indices = np.argwhere(player_hand[:, :, 0] > 0)
        hand_coords = [tuple(c) for c in hand_indices if not (c[0] == 3 and c[1] == 6)]
        np.random.shuffle(hand_coords)
        pool_indices = np.argwhere(pool > 0)
        pool_coords = [tuple(c) for c in pool_indices if not (c[0] == 3 and c[1] == 6)]
        np.random.shuffle(pool_coords)
        for h_c in hand_coords:
            for p_c in pool_coords:
                player_hand[h_c[0], h_c[1], 0] -= 1
                pool[h_c[0], h_c[1]] += 1
                self.get_one_card(p_c, pool, player_hand, 0)
                shanten_number = self.checker.get_shanten_num(player_hand[:, :, 0])
                if shanten_number == base_shanten_number + 1:
                    return True # 成功找到一个交换，增加了1向听数
                else:
                    player_hand[p_c[0], p_c[1], 0] -= 1
                    pool[p_c[0], p_c[1]] += 1
                    self.get_one_card(h_c, pool, player_hand, 0)
        return False  # 没有找到合适的交换来增加向听数，理论上不应该发生

    def get_hand(self, level, pool, player_hand):
        r"""对一层分发16张手牌
        Args:
            level (int): 当前分发手牌的玩家层数，0-3分别代表第一层到第四层
            pool (np.ndarray): 当前牌池矩阵，`4*9`
            player_hand (np.ndarray): 当前玩家手牌矩阵，`4*9*4`
        Returns:
            None: 直接修改输入的player_hand和pool矩阵，分发16张手牌给玩家"""
        coords = np.argwhere(pool > 0) # N行2列的有牌的坐标矩阵
        counters = pool[coords[:, 0], coords[:, 1]] # N行1列的对应坐标的牌数矩阵
        wall = np.repeat(coords, counters, axis=0) # 扩展成每张牌对应一行的牌堆矩阵，长度为剩余牌数
        np.random.shuffle(wall) # 洗牌
        hand_tiles = wall[:16] # 取前16张牌作为手牌
        for c, v in hand_tiles:
            player_hand[c, v, level] += 1
            pool[c, v] -= 1
        return

    def generate_hand(self, target_shanten: Literal[-1, 0, 1, 2, 3, 4, 5, 6, 7] = -1) -> tuple[NDArray[Any], NDArray[Any]]:
        """生成手牌，对玩家1启用向听数控制
        - -1：不指定向听数，随机生成一个合法手牌
        - 0：听牌手牌
        - 1：一向听手牌
        - 2：二向听手牌
        - ......        
        Args:
            target_shanten (int): 目标向听数，默认为-1（随机发牌）
        Returns:
            Tuple (np.ndarray, np.ndarray): 生成的手牌数组和剩余牌池矩阵
            - 生成的玩家手牌数组，形状为(4, 9, 4)
            - 生成后的剩余牌池矩阵，形状为(4, 9)"""
        if target_shanten > 7:
            target_shanten = 7 # 强制限制最大向听数为7，不然可能会死循环（摸到三张财神后最大向听数为7）
        if target_shanten >=0:
            generate_successful = False
            while not generate_successful:
                pool = self.full_wall.copy()
                self.player_hand.fill(0)
                self.generate_tenpai_hand(pool, self.player_hand)
                generate_successful = True
                for _ in range(target_shanten):
                    generate_successful = self.add_one_shanten_to_hand(pool, self.player_hand)
                    if not generate_successful:
                        break
            self.get_hand(1, pool, self.player_hand)
            self.get_hand(2, pool, self.player_hand)
            self.get_hand(3, pool, self.player_hand)
        else:
            pool = self.full_wall.copy()
            self.player_hand.fill(0)
            self.get_hand(0, pool, self.player_hand)
            self.get_hand(1, pool, self.player_hand)
            self.get_hand(2, pool, self.player_hand)
            self.get_hand(3, pool, self.player_hand)
        return self.player_hand, pool