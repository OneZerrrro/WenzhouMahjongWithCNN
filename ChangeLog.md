# 修改记录
所有修改记录会被记录在此处，格式：
> \## [unreleased] Name
> \### Added
> \### Changed
> \### Removed
> \### Repaired
> \### Deprecated

## 待办事项
- 模型加载方式还是有待商榷
- 可视化这部分，Engine中还要装入和返回上一动作相关的代码（当playerid=-1时代表是摸牌的情况）

## [2026-06-14-01] Hsia
### Added
- Engine中添加了players_type来确认display的默认视角
- Engine中添加了各处可视化函数
- Engine中添加了上一动作的actionid和playerid
- 添加了ModelList中示例模型的路径信息（Example）
- 添加了人类玩家显示选项的代码
### Changed
- 修改了Engine中自动选择唯一可用选项的逻辑，现在人类玩家会持续被询问（即使只有一个选项）
### Repaired
- 修复了导入CNN模型时info对应的是Model_List字典而非一个列表的情况
- 修复了当前玩家在弃牌后能对自己的弃牌进行响应的bug

## [2026-06-13-01] Hsia
### Added
- 添加了Visualization中显示牌桌的相关函数：
  - 添加了按顺序显示玩家的代码（目前进度是可以显示全部牌型，尚缺少玩家可选动作、上一玩家动作）
- 针对可视化函数，对Engine中获取状态的函数：
  - 添加了可见信息：每个人的暗杠次数
  - 添加了不可见信息：每个人的弃牌指针
  - 添加了当前庄家id
- 添加了draw_card函数的返回值：当前摸到的牌的编号
### Changed
- 修改了MahjongVisualization的位置到MahjongTool
- 修改了MahjongVisualization的名称为Visualization
### Repaired
- 修正了Players的overwrite_last_line函数中缺失self的bug

## [2026-06-07-02] Hsia
### Added
- 添加了按照结构MahjongMain所需的各类状态标志
- 添加了MahjongMain的状态机结构（尚未完成）
- 添加了重置状态机以及相关代码
### Changed
- 更新了Rules.md中的信息表示
- 修改了存档格式从csv -> json
- 修改了Characters的格式从csv -> json
- 修改了Rules的名称为ConfigRules
- 修改ConfigRules位置到ProgramStructure文件夹下

## [2026-06-07-01] Hsia
### Added
- 添加了SaveStru.py并明确了单存档状态机的结构
### Changed
- 修改ProgramStructure名称为EngineStru
- 修改EngineStru位置到ProgramStructure文件夹下
- 更新了ChangeLog的格式内容

## [2026-06-05-01] Hsia
### Added
- 添加了可视化相关的文件MahjongVisualization[Todo]
- 添加了Players中Human玩家的逻辑
  - 使用键盘输入合法动作编号对应的序号以做出动作
  - 输入非法/错误内容则会刷新该行

## [2026-06-04-01] Hsia
### Added
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