#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>

uint16_t *table;
long long progress_count = 0;

// 优先级判定：确保第一次比较时，任何有效的拆解都能胜过初始的“全0”状态
int is_better(int mk_n, int ms_n, int p_n, int d_n, int mk_o, int ms_o, int p_o, int d_o) {
    // 1. 分数（产出）
    int score_n = (mk_n + ms_n) * 2 + (p_n + d_n);
    int score_o = (mk_o + ms_o) * 2 + (p_o + d_o);
    if (score_n != score_o) return score_n > score_o;

    // 2. 总组数（占用坑位）
    int sum_n = mk_n + ms_n + p_n + d_n;
    int sum_o = mk_o + ms_o + p_o + d_o;
    if (sum_n != sum_o) return sum_n < sum_o;

    // 3. 兜底逻辑：如果上述都相同，根据你的推导 M 必然等于 P
    // 但为了代码严谨，可以加一个刻子优先（温州麻将碰碰胡权重高）
    return mk_n > mk_o;
}

void find_best(int cards[9], int mk, int ms, int p, int d, int *bmk, int *bms, int *bp, int *bd) {
    // 只有当当前方案确实更好时才更新
    if (is_better(mk, ms, p, d, *bmk, *bms, *bp, *bd)) {
        *bmk = mk; *bms = ms; *bp = p; *bd = d;
    }

    for (int i = 0; i < 9; i++) {
        if (cards[i] <= 0) continue;

        // A. 刻子
        if (cards[i] >= 3) {
            cards[i] -= 3; find_best(cards, mk + 1, ms, p, d, bmk, bms, bp, bd); cards[i] += 3;
        }
        // B. 顺子
        if (i <= 6 && cards[i] > 0 && cards[i+1] > 0 && cards[i+2] > 0) {
            cards[i]--; cards[i+1]--; cards[i+2]--;
            find_best(cards, mk, ms + 1, p, d, bmk, bms, bp, bd);
            cards[i]++; cards[i+1]++; cards[i+2]++;
        }
        // C. 对子
        if (cards[i] >= 2) {
            cards[i] -= 2; find_best(cards, mk, ms, p + 1, d, bmk, bms, bp, bd); cards[i] += 2;
        }
        // D. 搭子 AB
        if (i <= 7 && cards[i] > 0 && cards[i+1] > 0) {
            cards[i]--; cards[i+1]--; find_best(cards, mk, ms, p, d + 1, bmk, bms, bp, bd);
            cards[i]++; cards[i+1]++;
        }
        // E. 搭子 AC
        if (i <= 6 && cards[i] > 0 && cards[i+2] > 0) {
            cards[i]--; cards[i+2]--; find_best(cards, mk, ms, p, d + 1, bmk, bms, bp, bd);
            cards[i]++; cards[i+2]++;
        }
    }
}

void generate_recursive(int index, int cards[9], int sum) {
    if (index == 9) {
        int bmk = 0, bms = 0, bp = 0, bd = 0;
        find_best(cards, 0, 0, 0, 0, &bmk, &bms, &bp, &bd);
        
        uint32_t key = 0;
        for (int i = 0; i < 9; i++) key |= (uint32_t)(cards[i] & 0x07) << (i * 3);
        table[key] = (uint16_t)(((bd & 0x03) << 9) | ((bp & 0x07) << 6) | ((bms & 0x07) << 3) | (bmk & 0x07));

        #pragma omp atomic
        progress_count++;
        return;
    }
    for (int i = 0; i <= 4; i++) {
        if (sum + i <= 17) {
            cards[index] = i;
            generate_recursive(index + 1, cards, sum + i);
        }
    }
}

#include <stdio.h>

// 拷贝你的 is_better 和修正后的 find_best

int main() {
    int test_cards[9] = {2, 2, 0, 0, 0, 0, 0, 0, 0}; // 111 222 333
    int bmk=0, bms=0, bp=0, bd=0;
    
    // 运行拆解
    find_best(test_cards, 0, 0, 0, 0, &bmk, &bms, &bp, &bd);
    
    printf("Result for 111 222 333:\n");
    printf("Score: %d\n", (bmk+bms)*2 + (bp+bd));
    printf("Details: Mk=%d, Ms=%d, P=%d, D=%d\n", bmk, bms, bp, bd);
    
    if (bmk == 3) printf("SUCCESS!\n");
    else printf("FAILED: Still logic error.\n");
    
    return 0;
}