
import csv
from dataclasses import dataclass
from MahjongCore.MahjongGame import MahjongGame


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
class PlayerSaveData:
    """玩家存档数据类，包含玩家ID、历史胜率、历史积分等信息
    Args:
        player_id (int): 玩家ID
        total_round (int): 总对局数
        win_round (int): 胜利对局数
        tie_round (int): 平局对局数
        credit (int): 当前积分
        if_human_nicname (str, optional): 如果是人类玩家，存储玩家昵称，默认为None"""
    player_id: int
    total_round: int
    win_round: int
    tie_round: int
    credit: int
    if_human_nicname: str = None

class MahjongMain:
    def __init__(self, model_list_path: str = None, csv_path: str = None):
        self.mahjone_game = MahjongGame(model_list_path, csv_path)
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

    def load_save(self):
        """加载游戏存档，包括历史对局胜率、历史积分等"""
        pass
    
    def create_save(self):
        """创建游戏存档文件，用于保存历史对局胜率、历史积分等"""
        pass

    def save_game(self):
        """保存当前游戏状态到存档文件，包括历史对局胜率、历史积分等"""
        pass

    def load_models(self):
        """加载AI模型，用于AI玩家的决策"""
        