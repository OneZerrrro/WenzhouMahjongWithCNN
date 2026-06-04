# 修改记录
所有修改记录会被记录在此处
## [unreleased] Name
### Added
### Changed
### Removed
### Repaired
### Deprecated

## [2026-06-04-01] Hsia
## Added
- 添加了初始代码
  - MahjongEngine：处理一轮麻将要干的事情
  - HandGenerator：生成符合要求的手牌
  - MahjongState：一轮麻将中的状态信息
  - Players：保存玩家的行为方式
    - Random Player：随机出牌，有胡就胡
    - Rule Based Player：基于减小向听数的Ai，有胡就胡
  - MahjongGame[Todo]：处理多轮麻将要干的事情及计分系统
  - MahjongMain[Todo]：处理主菜单的事
  - ModulesStructure：保存AI玩家的CNN结构
  - ShantenMapGenerator：生成向听查找表