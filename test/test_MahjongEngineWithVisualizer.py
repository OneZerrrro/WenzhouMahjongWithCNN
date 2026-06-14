import sys
import os
import time

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MahjongEngine.MahjongEngine import MahjongEngine
import random

def main():
    game_rounds = 1000
    # 创建一个麻将游戏引擎实例，指定玩家类型和模型
    # print("正在创建游戏引擎...")
    engine = MahjongEngine(None)
    # print("游戏引擎创建完成，开始模拟1000局游戏...")

    HuNum = 0
    HuPlayer = {i: 0 for i in range(4)}

    # for i in range(game_rounds): # 3-5向听数最为接近实际游戏情况。
    engine.reset([3, 3, 3, 3], [None for _ in range(4)], random.randint(0, 3), random.randint(0, 33), -1, 1, True)
    _, endReasonNum, WinResult = engine.play_one_round()
    HuNum += 1 if endReasonNum == 1 else 0
    if WinResult.hu_player_index != -1:
        HuPlayer[WinResult.hu_player_index] += 1

    if endReasonNum == 1:
        print("这一局获胜的玩家是玩家", WinResult.hu_player_index)
    else:
        print("这一局没有玩家胡牌，流局结束")
    # if (i+1) % 100 == 0:
    #     print(f"{i+1}局游戏模拟完成...")

    # print(f"{game_rounds}局游戏模拟完成，耗时: {end_time - start_time:.2f}秒")
    # print(f"平均每局游戏耗时: {(end_time - start_time) / game_rounds:.4f}秒")
    # print(f"{game_rounds}局游戏中，胡牌次数: {HuNum}, 胡牌率: {HuNum/game_rounds:.2%}")
    # print("各玩家胡牌次数分布:")
    # for player_id, count in HuPlayer.items():
    #     print(f"玩家{player_id}: {count}次胡牌, 胡牌率: {count/game_rounds:.2%}")

if __name__ == "__main__":
    main()