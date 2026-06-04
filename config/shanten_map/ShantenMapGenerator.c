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

int main() {
    printf("Allocating 256MB...\n");
    table = (uint16_t *)calloc(1 << 27, sizeof(uint16_t));
    if (!table) return 1;

    printf("Starting Ultra-Fast Generation (Multi-threaded)...\n");
    double t_start = omp_get_wtime();

    // 核心修改：双层嵌套循环并行化，产生更多任务块
    #pragma omp parallel for collapse(2) schedule(dynamic)
    for (int i = 0; i <= 4; i++) {
        for (int j = 0; j <= 4; j++) {
            int local_cards[9] = {0};
            local_cards[0] = i;
            local_cards[1] = j;
            generate_recursive(2, local_cards, i + j);
        }
    }

    double t_end = omp_get_wtime();
    printf("Finished! Time: %.2f seconds.\n", t_end - t_start);
    printf("Calculated combinations: %lld\n", progress_count);

    FILE *f = fopen("wenzhou_v2_256.bin", "wb");
    if (f) { fwrite(table, sizeof(uint16_t), 1 << 27, f); fclose(f); }
    free(table);
    return 0;
}