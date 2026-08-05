"""问题 7.7（压轴）：softmax in TileLang（FROM-SCRATCH）。

contract：
- softmax(x) 接收形状 (M, N) 的 float32 CUDA tensor，返回同形状结果，
  对每一行独立做 softmax；
- kernel 用 TileLang 自己写，一个 block 处理一行（或一小批行）；
- 为了确保数值稳定，要求行内先减最大值，再做 exp 与求和。测试里有一行
  数值巨大的输入，不稳定的实现会得到 inf/nan；
- 行宽 N 任意，可以假设 N <= 4096。TileLang 的 kernel 按形状编译，
  用 make_xxx(M, N) 针对形状生成、在 wrapper 里按形状缓存编译结果
  是常见做法（结构可以参考 7.3、7.4）；
- 归约用 T.reduce_max / T.reduce_sum，逐元素部分用 T.Parallel 加 T.exp；
- fragment 的宽度建议取不小于 N 的 2 的幂（类比 Triton 的
  next_power_of_2），不足的位置补 -inf（T.if_then_else 加 T.infinity），
  否则布局推断可能报 no available layout；
- 通过 pytest tests/test_tilelang_softmax.py 即为完成。

(Optional) 将你的实现和 torch.softmax 比较一下性能（行宽取 256/1024/4096），
Tip: elementwise + 行内归约的 kernel 大概率是带宽瓶颈，可以想想理论上限是多少。
"""

import torch
import tilelang
import tilelang.language as T

_softmax_kernel_cache = {}


def _next_power_of_2(n: int) -> int:
    if n <= 1:
        return 1
    if n & (n - 1) == 0:
        return n
    return 1 << (n - 1).bit_length()


def make_softmax_kernel(M: int, N: int):
    cache_key = (M, N)
    if cache_key in _softmax_kernel_cache:
        return _softmax_kernel_cache[cache_key]

    padded_N = _next_power_of_2(N)
    threads = 128

    @T.prim_func
    def kernel(X: T.Tensor((M, N), T.float32), Y: T.Tensor((M, N), T.float32)):
        with T.Kernel(M, threads=threads) as row:
            x = T.alloc_fragment((1, padded_N), T.float32)
            exp_vals = T.alloc_fragment((1, padded_N), T.float32)
            row_max = T.alloc_fragment((1,), T.float32)
            row_sum = T.alloc_fragment((1,), T.float32)

            # 1) 读入一行：有效位置读 X，越界位置补 -inf
            # 必须用 if/else 语句，不能用 T.if_then_else 表达式，
            # 否则 j>=N 时 X[row, j] 仍可能被求值导致越界读。
            for _, j in T.Parallel(1, padded_N):
                if j < N:
                    x[0, j] = X[row, j]
                else:
                    x[0, j] = -T.infinity(T.float32)

            # 2) 行内求 max（数值稳定）
            T.reduce_max(x, row_max, dim=1, clear=True)

            # 3) 逐元素 exp(x - max)
            for _, j in T.Parallel(1, padded_N):
                exp_vals[0, j] = T.exp(x[0, j] - row_max[0])

            # 4) 行内求和
            T.reduce_sum(exp_vals, row_sum, dim=1, clear=True)

            # 5) 归一化写回：迭代数取 padded_N 保证是 threads 的整数倍，
            # 再用 if j < N 跳过无效位置，避免 T.Parallel(1, N) 的静默错误。
            for _, j in T.Parallel(1, padded_N):
                if j < N:
                    Y[row, j] = exp_vals[0, j] / row_sum[0]

    compiled = tilelang.compile(kernel, out_idx=[1], target="cuda")
    _softmax_kernel_cache[cache_key] = compiled
    return compiled


def softmax(x: torch.Tensor) -> torch.Tensor:
    if not x.is_cuda:
        raise ValueError("Input tensor must be on CUDA")
    if x.dtype != torch.float32:
        raise ValueError("Input tensor must be float32")

    M, N = x.shape
    x = x.contiguous()

    kernel = make_softmax_kernel(M, N)
    return kernel(x)
