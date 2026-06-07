
import csv
from dataclasses import dataclass, field
from MahjongCore.MahjongGame import MahjongGame
from typing import Literal, Any
import json

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

@dataclass
class SaveData:
    """玩家存档数据类，包含玩家角色ID、历史胜率、历史积分等信息
    Args:
        character_id (int): 玩家角色ID
        total_round (int): 总对局数
        win_round (int): 胜利对局数
        tie_round (int): 平局对局数
        credit (int): 当前积分
        if_human_nicname (str, optional): 如果是人类玩家，存储玩家昵称，默认为None"""
    character_id: int
    total_round: int
    win_round: int
    tie_round: int
    credit: int
    if_human_nicname: str | None = None

@dataclass
class GameInputState:
    """游戏选项
    Args:
        players_type (list): [自动配置]玩家类型列表
        model_name (list): [自动配置]使用的模型名称列表
        banker_index (int): [自动配置]庄家索引
        god_id (int): [当局]财神牌ID
        shanting_num (int): [当局]0号玩家初始手牌向听数（训练用，默认-1）
        current_base_score (int): [当局]底分"""
    players_type: list = field(default_factory=list)
    model_name: list = field(default_factory=list)
    banker_index: int = 0
    god_id: int = 0
    shanting_num: int = -1
    current_base_score: Literal[1, 2, 3, 4] = 1

class MahjongMain:
    def __init__(self, model_list_path: str = None, save_path: str = None):
        self.FSM_state: Literal[0, 1, 2, 3, 4] = 0
        """状态机状态, 包括：
        - 0: 单存档主界面
        - 1: 开始今天游戏（嵌套状态机）
        - 2: 查看当前存档信息
        - 3: 保存并回到上一级菜单
        - 4: 保存并直接退出"""
        self.game_state: Literal[0, 1, 2, 3] = 0
        """游戏状态, 包括：
        - 0: 等待玩家选择对局模式
        - 1: 开始新一轮对局
        - 2: 显示当前玩家信息
        - 3: 返回上一级菜单"""
        self.save_name = None
        """存档名称，默认为None，表示没有加载存档"""
        self.save_info: dict[int, SaveData] = {}
        """[Todo]存档信息，包含玩家角色ID、历史胜率、历史积分等信息，默认为None，表示没有加载存档"""
        self.game_input_state = GameInputState()
        """游戏的输入状态，包括初始选项和可变选项"""
        # [Todo] 尚未添加当局结算相关信息
        self.mahjone_game = MahjongGame(model_list_path, save_path)
        self.players_map = {}
        # [Todo] 尚未载入玩家信息映射表，应该在加载存档时载入


        # Todo: 这里写的是多轮对局的流程，单轮对局的流程在MahjongEngine中实现
        # 初始化应该初始化下面start game里提到的内容：
        # 需要加载：历史对局胜率、历史积分（类似游戏存档）
        # ✔ ai陪练类似游戏角色一样，一般是一个ai对应一个模型（可能相同），可能需要一个文件保存对应关系
        # ✔ 就是：ai陪练代码 - 对应模型名称 - 对应外部显示昵称 - 对应历史胜率和积分等数据
        # ✔ 以及玩家个人的昵称 - 历史胜率和积分等数据（可能需要一个文件来存储）
        # ✔ 当然存档要做到可以中途加入新的ai陪练。

    def reset_SingleSave_FSM(self, save_name: str) -> None:
        """重置单存档状态机，包括加载玩家信息映射表、重置状态机状态等
        Args:
            save_name (str): 玩家存档名称"""
        self.FSM_state = 0
        self.game_state = 0
        self.save_name = save_name
        self.save_info = self.load_save(self.save_name)
        self.game_input_state = GameInputState()
        return
    
    @staticmethod
    def load_save(save_name: str) -> dict[int, SaveData]:
        """加载游戏存档，包括历史对局胜率、历史积分等
        Args:
            save_name (str): 玩家存档名称"""
        save_info: dict[int, SaveData] = {}
        save_path = f"saves/{save_name}.json" # 当前路径为默认路径，以后可以添加修改默认路径的功能
        with open(save_path, 'r', encoding='utf-8') as f:
            save_file: dict[str, dict[str, int|str]] = json.load(f)
            for character_id, data in save_file["character"].items():
                character_id = int(character_id)  # JSON中的键是字符串，需要转换为整数
                save_info[character_id] = SaveData(
                    character_id=character_id,
                    total_round=int(data["total_round"]),
                    win_round=int(data["win_round"]),
                    tie_round=int(data["tie_round"]),
                    credit=int(data["credit"]),
                    if_human_nicname=str(data["if_human_nicname"])
                        if "if_human_nicname" in data 
                        else None
                )
        return save_info

    def load_players_map(self, save_name: str) -> dict[int, PlayerInfo]:
        """[Todo] 这个函数现在有严重问题，需要修改：不是当前的文件格式(json)"""
        
        """加载玩家信息映射表，包括玩家ID、昵称、类型等信息
        Args:
            save_name (str): 玩家存档名称
        Returns:
            dict (int, PlayerInfo): 玩家信息映射表
            
            [Todo: 返回值待定]"""
        players_map = {}
        with open(save_name, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)  # 自动按列名读取
            for row in reader:
                player_id = int(row["PlayerID"])
                players_map[player_id] = PlayerInfo(
                    name=row["PlayersName"],
                    class_type=row["PlayerClass"],
                    model_name=row["PlayerModelName"]
                )
        return players_map
    
    def play_SingleSave_FSM(self):
        """使用当前存档进行游戏，包括加载历史对局胜率、历史积分等信息"""
        while True:
            if self.FSM_state == 0: # 单存档主界面
                # [Todo] 绘制界面
                self.FSM_state = int(input("请输入您的操作：", end=''))
                while self.FSM_state not in [1, 2, 3, 4]:
                    print("\033[F\033[K" + "无效操作，", end='')
                    self.FSM_state = int(input("请在1-4之间选择：", end=''))
            elif self.FSM_state == 1: # 开始今天游戏（嵌套状态机）
                # [Todo] 绘制界面
                # [Todo] 需要手动输入 - 参与游戏的玩家名称
                players_names = input("请输入参与游戏的玩家名称，用逗号分隔：").split(',') # [Todo] 等待修正，不一定用这个输入方式
                self.PlayGame_FSM(players_names)
            elif self.FSM_state == 2: # 查看当前存档信息
                # 显示当前存档信息界面，包括历史对局胜率、历史积分等信息
                pass
            elif self.FSM_state == 3: # 保存并回到上一级菜单
                # 保存当前游戏状态到存档文件，并回到上一级菜单
                pass
            elif self.FSM_state == 4: # 保存并直接退出
                # 保存当前游戏状态到存档文件，并直接退出游戏
                pass


    def PlayGame_FSM(self, players_names) -> None:
        """进行游戏的状态机"""
        pass
    
    def create_save(self):
        """创建游戏存档文件，用于保存历史对局胜率、历史积分等"""
        pass

    def save_game(self):
        """保存当前游戏状态到存档文件，包括历史对局胜率、历史积分等"""
        pass

    def load_models(self):
        """加载AI模型，用于AI玩家的决策"""
        