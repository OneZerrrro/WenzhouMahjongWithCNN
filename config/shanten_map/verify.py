import numpy as np

# 加载查表
table = np.fromfile("wenzhou_v2_256.bin", dtype=np.uint16)

def decode(val):
    return val & 0x07, (val >> 3) & 0x07, (val >> 6) & 0x07, (val >> 9) & 0x03

def check(counts, name="Test"):
    key = 0
    for i, c in enumerate(counts):
        key |= (int(c) & 0x07) << (i * 3)
    
    mk, ms, p, d = decode(table[key])
    score = (mk + ms) * 2 + (p + d)
    groups = mk + ms + p + d
    print(f"{name} {counts}: Score={score}, Groups={groups} (M:{mk+ms} P:{p} D:{d})")

# 1. 验证基础
check([3, 3, 3, 0, 0, 0, 0, 0, 0], "3-刻子")
check([1, 1, 1, 1, 1, 1, 0, 0, 0], "2-顺子")
check([2, 2, 2, 0, 0, 0, 0, 0, 0], "3-对子")

# 2. 验证“温州麻将 16张”可能出现的极端多组数情况
# 比如 11 22 33 44 55 66 77 88 (8对子)
check([2, 2, 2, 2, 2, 2, 2, 2, 0], "8-对子")

# 3. 验证空牌
check([0]*9, "空手牌")