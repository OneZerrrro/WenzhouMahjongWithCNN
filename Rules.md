# AiPlayers写入规则
1. PlayerID不允许重复
2. PlayerName不建议重复
3. PlayerClass可以重复
4. 如果只可能有一种权重（全随机/判别式AI），PlayerModelName填写0
5. 如果有多种权重（各类CNN），PlayerModelName需要填写对应名称
   - 所有名称需要在ModelList中有对应模型存在
## 说明
AiPlayer中写入的是所有AI。
一个PlayerID对应一个AI，其中：

# save1写入规则
1. PlayerID对应AiPlayers中的PlayerID，可以少但是不可以多
2. TotalRound对应的是当前玩家玩过的总场次
3. WinRound对应的是当前玩家获胜过的场次
4. TieRound对应的是玩家流局的场次
5. Credit对应的是玩家当前分数，默认有1000分
6. 一个存档至少有四名玩家

举例说明：
AiPlayers.csv内部如下
<tr><th>PlayerID</th><th>PlayersName</th><th>PlayerClass</th><th>PlayerModelName</th></tr>
<tr><td>0</td><td>Human</td><td>Human</td><td>0</td></tr>
<tr><td>1</td><td>Test</td><td>CNN_v1</td><td>cnn_v1_1</td></tr>
<tr><td>2</td><td>AAA外卖批发</td><td>RuleBased</td><td>0</td></tr>
<tr><td>3</td><td>老鼠</td><td>RuleBased</td><td>0</td></tr>
<tr><td>4</td><td>钉子头</td><td>RuleBased</td><td>0</td></tr>

save1.csv内部如下
<tr><th>PlayerID</th><th>TotalRounds</th><th>WinRound</th><th>TieRound</th><th>Credit</th></tr>
<tr><td>0</td><td>100</td><td>24</td><td>1</td><td>11451</td></tr>
<tr><td>1</td><td>100</td><td>24</td><td>1</td><td>6000</td></tr>
<tr><td>2</td><td>100</td><td>25</td><td>1</td><td>4000</td></tr>
<tr><td>3</td><td>100</td><td>23</td><td>1</td><td>5000</td></tr>

那么：Player234都是同一类ai
Player2在游戏中的昵称是**AAA外卖批发**，Player3在游戏中的昵称是**老鼠**