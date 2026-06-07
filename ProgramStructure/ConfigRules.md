# AiPlayers写入规则
1. CharacterID不允许重复，类似database中的主键
2. Name不建议重复，本质上是对一个角色的称呼
3. ["ai"]["type"]可以重复
4. 如果只可能有一种权重（全随机/判别式AI），PlayerModelName填写0
5. 如果有多种权重（各类CNN），["ai"]["model"]需要填写对应名称
   - 所有名称需要在ModelList中有对应模型存在
## 说明
AiPlayer中写入的是所有AI。类比：
> AiPlayer中写入的是有几个不同的“人”以及Ta们的配置，程序内部按照PlayerID来区分
save1文件中写入的是哪几个特定的“人”参与了这个存档

一个PlayerID对应一个AI，其中：

# save1写入规则
1. PlayerID对应AiPlayers中的PlayerID，可以少但是不可以多
2. TotalRound对应的是当前玩家玩过的总场次
3. WinRound对应的是当前玩家获胜过的场次
4. TieRound对应的是玩家流局的场次
5. Credit对应的是玩家当前分数，默认有1000分
6. 一个存档至少有四名玩家

举例说明：

**以下csv相关内容作废，更换成json**
---
AiPlayers.csv内部如下
|PlayerID|PlayersName|PlayerClass|PlayerModelName|
|---|---|---|---|
|0|Human|Human|0|
|1|Test|CNN_v1|cnn_v1_1|
|2|AAA外卖批发|RuleBased|0|
|3|老鼠|RuleBased|0|
|4|钉子头|RuleBased|0|

save1.csv内部如下
|PlayerID|TotalRounds|WinRound|TieRound|Credit|
|---|---|---|---|---|
|0|100|24|1|11451|
|1|100|24|1|6000|
|2|100|25|1|4000|
|3|100|23|1|5000|

---

Characters.json内部如下：
```json
{
   {
      "character_id": "这里填写角色id，不重复",
      "name": "这里填写角色名称，最好不重复",
      "ai": {
         "type": "这里填写Ai模型版本",
         "model": "这里填写模型的名称"
      }
   }
}
```
举例而言：
```json
{
   {
      "character_id": 0,
      "name": "Human",
      "ai": {
         "type": "Human",
         "model": "None"
      }
   },
   {
      "character_id": 1,
      "name": "Test",
      "ai": {
         "type": "cnn_v1",
         "model": "cnn_v1_1"
      }
   },
   {
      "character_id": 2,
      "name": "AAA外卖批发",
      "ai": {
         "type": "RuleBased",
         "model": "None"
      }
   },
   {
      "character_id": 3,
      "name": "老鼠",
      "ai": {
         "type": "RuleBased",
         "model": "None"
      }
   },
   {
      "character_id": 4,
      "name": "钉子头",
      "ai": {
         "type": "RuleBased",
         "model": "None"
      }
   }
}
```
save.json内部如下
```json
{
   "save_name": "存档名称",
   "character": {
      "character_id": {
         "credit": "当前人物点数",
         "total_round": "当前人物进行对局总数",
         "win_round": "当前人物获胜场次",
         "tie_round": "当前人物流局场次",
      }
   }
}
```
举例而言：
```json
{
   "save_name": "save1",
   "character": {
      "0": {
         "credit": 10000,
         "total_round": 100,
         "win_round": 24,
         "tie_round": 1,
      },
      "1": {
         "credit": 12345,
         "total_round": 100,
         "win_round": 25,
         "tie_round": 1,
      },
      "2": {
         "credit": 1659,
         "total_round": 100,
         "win_round": 25,
         "tie_round": 1,
      },
      "3": {
         "credit": 169,
         "total_round": 100,
         "win_round": 25,
         "tie_round": 1,
      }
   }
}
```
说明：这个程序设定上有5个“人/Ai”，他们分别是**Human**、**Test**、**AAA外卖批发**、**老鼠**和**钉子头**，而且在save1中不能使用**钉子头**
那么：Player234都是同一类ai（RuleBased）
Player1的cnn模型结构是cnn_v1，模型权重文件名称是cnn_v1_1
Player2在游戏中的昵称是**AAA外卖批发**，Player3在游戏中的昵称是**老鼠**