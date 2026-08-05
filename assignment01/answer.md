# 0
## prob 0.2 

```C++
printf("GPU 型号            : %s\n", prop.name);
    printf("compute capability  : %d.%d\n", prop.major, prop.minor);

    // ====== 空 1：SM 数量（提示：字段名以 multiProcessor 开头） ======
    printf("SM 数量             : %d\n", prop.multiProcessorCount);

    // ====== 空 2：warp 大小 ======
    printf("warp 大小           : %d\n", prop.warpSize);

    // ====== 空 3：每个 block 可用的 shared memory 上限（字节） ======
    printf("shared mem / block  : %zu\n", (size_t) prop.sharedMemPerBlock);

    // ====== 空 4：每个 SM 的最大常驻线程数 ======
    printf("max threads / SM    : %d\n", prop.maxThreadsPerMultiProcessor);

    // ====== 空 5：全局显存总量（字节） ======
    printf("global mem          : %zu\n", (size_t) prop.totalGlobalMem);

    printf("max threads / block : %d\n", prop.maxThreadsPerBlock);
```

GPU 型号            : NVIDIA GeForce RTX 4060 Laptop GPU

compute capability  : 8.9

SM 数量             : 24

warp 大小           : 32

shared mem / block  : 49152

max threads / SM    : 1536

global mem          : 8585216000

max threads / block : 1024

# 1 Why GPU？
## prob 1.1 

判断对错，可以顺带补一句理由。

(a) 一块标称 100 TFLOPS 的 GPU，执行单条指令的延迟一定低于 5 GHz 的 CPU。

(b) HBM 的“高带宽”指大块连续访问时的吞吐，零散的随机访问达不到标称值。

(c) 严格串行的迭代算法（每步依赖上一步的结果），即使换一块算力更强的 GPU 也快不了多少。

(d) “算力 1000 TFLOPS”意味着每次运算的延迟是 $10^{-15}$ 秒。

答：
(a) 错。5 GHz 单核GPU吞吐约几十到几百 GFLOPS，显然CPU的峰值吞吐是远低于GPU的。但是吞吐量不仅仅由单条指令延迟所决定，GPU具有大量ALU，通过大规模并行和多流水线来提高算术吞吐，所以GPU单条指令的延迟反而可能更高。

(b) 对。HBM——High Bandwidth Memory 峰值带宽是基于突发连续传输测量的，靠的是高带宽和高频的数据传输；而零散的随机访问会触发行缓冲冲突和地址切换，导致总线闲置，所以达不到标称值。

(c) 对。此处的严格串行是指该算法只能通过单线程计算，完全无法多线程并行。算力一般指吞吐，在（a）中我们表明吞吐不单单依赖于单条指令的延迟，它由多种因素决定，对于串行任务，GPU的单线程延迟要比CPU大。同时Amdahl定律指出，程序串行部分的比例决定了加速比的上限，如果串行部分占99%，无论GPU并行能力多强，整体性能上限的限制使得程序无法变得更高效。

(d) 错。1000 TFLOPS 指每秒执行1000T次浮点运算，其倒数只能表明两条指令完成的平均时间间隔。而单条指令的延迟指的是从指令发出到结果写回所需的时间，它受限于流水线深度和时钟周期，而且现代GPU通常一个时钟周期能够发射多条指令如8条，所以实际的指令延迟要大得多。

## prob 1.2 

Session 1 讲座里提过“N 方过百万”这个例子。总计算量 $10^{12}$ FLOP 在当代 GPU 上的运算时间大概是毫秒级，那为什么一个严格在线的串行算法仍然做不到几秒内跑完？（从“延迟”和“吞吐”的角度考虑）

答：以A100为例，FP32 (单精度)峰值吞吐为 19.5 TFLOPS，则执行计算量 $10^{12}$ FLOP 的程序约需50ms，但是这个吞吐量是通过大规模并行获得的，实际的单线程的吞吐要低很多。假设A100的核心频率为 1.5GHz，对于一条简单的浮点加法指令，其延迟约为5个时钟周期，则单步耗时 5 * 1/1.5G约3.3ns，如果严格串行$10^{12}$步，约需55min，这远远超过“几秒内”。

## prob 1.3

补全下表（thread 一行已填好作为示例）
执行层次    软件含义                对应硬件              直接可用的存储      同步与通信手段

thread      kernel 的最小执行单位   计算单元上的一个 lane  自己的寄存器       （自身天然有序）

warp        线程并行的最小执行单位   SM内的Warp调度器      线程的寄存器       线程束内同步

block/CTA   线程块                   SM               共享内存  块内同步，不同块间无法显式同步

grid        线程网格               GPU设备                 全局内存      原子操作，或主机同步

## prob 1.4 

SIMD 与 SIMT 的区别？另：判断正误——Nvidia GPU 在 Volta 之后每个线程有独立的 program
counter，所以 branch divergence 不再有性能代价。

答：1）SIMD——Single Instruction Multiple Data 单指令多数据，一条指令操作一个向量，是数据级并行，如果遇到分支如if-else，两个分支都将串行执行，用掩码屏蔽当前不执行的通道；SIMT——Single Instruction Multiple Thread，一个warp（32 threads）执行同一条指令，是线程级并行，遇到分支时，不同路径的线程会分叉执行（warp divergence），执行完后自动收敛回同一条路径。

2）错。Volta架构引入独立线程调度确实为每个线程赋予了独立的程序计数器和栈，但是并没有消除 branch divergence 的性能代价。一个 Warp 中的 32 个线程共享同一个调度器，在每个时钟周期只能执行同一条指令。独立PC带来的优势是：假设发散路径 A 中先执行完的线程可以先行执行后续公共代码，不必死等 B 路径执行完，从而减少了闲置等待（Stall）时间。

## prob 1.5
回答：(a) GPU 单线程为什么比 CPU 慢这么多？(b) 从单 block 到铺满 grid 的提速，说明 GPU 加速计算靠的是什么？

CPU 单线程      :     22.498 ms  (  5.36 ns/元素)

GPU <<<1, 1>>>  :    258.608 ms  ( 61.66 ns/元素)

GPU <<<1, 256>>>:      5.494 ms  (  1.31 ns/元素)

GPU 铺满 grid   :      0.382 ms  (  0.09 ns/元素, 16384 blocks x 256 threads)

a）从数据上来说，GPU单线程比CPU单线程慢约11.5倍。首先，CPU核心频率通常在4~5 GHz，而GPU核心（CUDA Core）运行频率通常在1.5 GHz左右；其次GPU为了堆砌数千个核心，GPU的单条指令流水线极深，单条指令从发射到写回需要几十甚至上百个周期，而CPU具有乱序执行和分支预测器，单条指令延迟极低；最后，GPU不像CPU支持单线程的乱序存取，导致单线程在发生 Cache Miss 时极易产生气泡。GPU的线程切换几乎无代价（每个 Warp 的状态在硬件中是常驻的），通过切换到其他线程执行来掩盖全局内存访问延迟。

b）GPU 加速计算靠的是大规模并行 + 延迟隐藏（通过大量活跃线程填满流水线）

## prob 1.6 (Optimal)

```Python
def run(program):
    # raise NotImplementedError("从这里开始写")
    regs = list(range(32))          
    cycles = 0

    def execute(prog, mask):
        nonlocal cycles
        for inst in prog:
            op = inst[0]
            if op == "add":
                k = inst[1]
                for i in range(32):
                    if mask[i]:
                        regs[i] += k
                cycles += 1
            elif op == "mul":
                k = inst[1]
                for i in range(32):
                    if mask[i]:
                        regs[i] *= k
                cycles += 1
            elif op == "if_lt":
                t, then_prog, else_prog = inst[1], inst[2], inst[3]

                then_mask = [mask[i] and regs[i] < t for i in range(32)]
                else_mask = [mask[i] and regs[i] >= t for i in range(32)]

                if any(then_mask):
                    execute(then_prog, then_mask)
                if any(else_mask):
                    execute(else_prog, else_mask)

    execute(program, [True] * 32)
    return regs, cycles
```

# 2 First Kernel
## prob 2.1

```C++
// 问题 2.1：向量加法（填空）
// 六个空各考一个概念，填完编译运行，"PASS"即可。
// 填完之前这个文件无法通过编译。
#include "common.h"

// ====== 空 1：kernel 需要什么函数修饰符？ ======
__global__ void vectorAdd(const float *a, const float *b, float *c, int n) {
    // ====== 空 2：这个线程负责的全局下标 ======
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    // ====== 空 3：边界保护——总线程数可能多于元素个数 ======
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

int main() {
    const int n = 1000003;  // 故意取一个不是 256 整数倍的数
    size_t bytes = (size_t)n * sizeof(float);

    float *h_a = (float *)malloc(bytes);
    float *h_b = (float *)malloc(bytes);
    float *h_c = (float *)malloc(bytes);
    float *h_ref = (float *)malloc(bytes);
    fill_random(h_a, n, 1);
    fill_random(h_b, n, 2);
    for (int i = 0; i < n; i++) h_ref[i] = h_a[i] + h_b[i];

    float *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, bytes));
    CUDA_CHECK(cudaMalloc(&d_b, bytes));
    CUDA_CHECK(cudaMalloc(&d_c, bytes));

    // ====== 空 4：把 h_a、h_b 拷到 device（注意最后一个方向参数） ======
    CUDA_CHECK(cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice));

    int threadsPerBlock = 256;
    // ====== 空 5：block 数——向上取整，保证覆盖全部 n 个元素 ======
    int blocksPerGrid = (n + threadsPerBlock - 1) / threadsPerBlock;

    // ====== 空 6：启动 kernel（执行配置写在哪里？） ======
    vectorAdd<<<blocksPerGrid, threadsPerBlock>>>(d_a, d_b, d_c, n);
    CUDA_CHECK_KERNEL();

    CUDA_CHECK(cudaMemcpy(h_c, d_c, bytes, cudaMemcpyDeviceToHost));
    REPORT(check_close(h_c, h_ref, n));
    return 0;
}

```

## prob 2.2

prob 2.2 （CONCEPT）
为下列五个场景选择正确的修饰符（如 __global__ 等）。
(a) 在 GPU 上执行、由 CPU 侧启动的 kernel 函数。
(b) 只会被 kernel 调用的辅助函数。
(c) host 和 device 代码都要调用的小工具函数。
(d) 整个 kernel 运行期间不变、所有线程都要读的系数表。
(e) block 内线程共享的暂存数组。

答：
a）__global__
b）__device__
c）__host__ __device__
d）__const__
e）__shared__

## prob 2.3

02_vector_add_um.cu 代码完整，但目前是“显式内存管理”的版本。改之前先按原样编译运行一次，记下耗时——这一版会被你的改动覆盖掉，下面 (b) 要拿它做对照。然后按文件头的说明改成 unified memory 版（cudaMallocManaged），并保持文件头写明的计时窗口不变。

```
cd assignment01/cuda
make run/m2_first_kernel/02_vector_add_um
```

然后请回答如下问题：(a) kernel 启动之后、CPU 读结果之前，为什么必须有一次同步？在原
先的版本里这次同步发生在哪个调用里？(b) 对比两版“搬运 + kernel + 读回”的耗时，分析差距
的原因（谁快谁慢都有可能，与使用的卡有关）。

a）CUDA kernel 启动是非阻塞的，kernel启动后CPU线程会立即返回host端，所以CPU读结果需要等待Device端执行结束，则必须有一次同步。这个同步发生在函数`CUDA_CHECK_KERNEL()`中的`CUDA_CHECK(cudaDeviceSynchronize())`。

b）原版：搬运 + kernel + 读回: 114.6 ms
   um版：搬运 + kernel + 读回: 45.8 ms
NIVIDIA 的卡有一种内存机制叫做统一虚拟内存，即CPU和GPU访问的虚拟地址空间是一致的。使用`cudaMallocManaged`就是在统一的虚拟地址空间分配内存，那么这块内存无论是host端还是device端都可以直接访问。`cudaMalloc + cudaMemcpy`是显式、同步、整块搬运；而`cudaMallocManaged`在一开始并没有搬运数据，当kernel在GPU上访问某个内存页时产生缺页异常，GPU 的迁移引擎会按需将当前需要的页面从 Host 搬过去，CPU 读结果时，又把被修改过的页面搬回来。
综上，um版更快的原因一是减少了同步时间，二是数据搬运和GPU计算存在重叠。

## prob 2.4

判断对错，可以顺带补一句理由。
(a) vectorAdd<<<...>>>(...) 这条语句返回时，kernel 一定已经执行完毕。
(b) 同一个 stream 里，cudaMemcpy（device 到 host）会等它前面的 kernel 全部完成后才开始拷
贝。
(c) kernel 内部的非法访存，会在启动语句处同步地报出来。

答：
a）错。CUDA kernel 启动是非阻塞的，kernel启动后CPU线程会立即返回host端。

b）对。在同一个流中，所有操作遵循顺序一致性，cudaMemcpy是隐式同步。

c）错。Kernel 内部的非法访存（如越界、访问未映射地址）属于异步错误，不会在启动语句 <<<>>> 处报出来。cudaGetLastError() 如果在启动语句后立即调用，只能捕获到同步错误，例如启动参数配置错误（如网格/块维度超限）；而 Kernel 执行期间发生的非法访存错误，必须等到后续某个显式或隐式的同步点（如 cudaDeviceSynchronize() 或阻塞性的 cudaMemcpy）时才会被主机端捕获并返回。

## prob 2.5

修 bug：03_bug_launch.cu
```
cd assignment01/cuda
make run/m2_first_kernel/03_bug_launch
```

运行输出：MISMATCH at 0: got 0.000000, want 6.730000
cudaGetLastError输出：CUDA error cudaErrorInvalidConfiguration at m2_first_kernel/03_bug_launch.cu:34: invalid configuration argument

问题：为什么不加这一行时程序一声不吭？

答：CUDA kernel 启动是非阻塞的，kernel启动后CPU线程会立即返回host端，由于没有使用cudaDeviceSynchronize()进行显示同步，下一行代码正好是cudaMemcpy，则会隐式同步。由错误报告可知kernel并没能成功启动，代码没有主动调用 cudaGetLastError() 去检查前序启动的返回值，并且后续的 cudaMemcpy 虽然隐式同步了，但它不会把 kernel 的启动错误“抛”出来

代码中int threads = 2048;
实际我的设备支持的 maxThreadsPerBlock 是1024所以会启动失败，改成小于1024的值就行。

## prob 2.6

```C++
// 问题 2.6：二维矩阵加法（填空）。
// 用二维的 block 和 grid 处理 M x N 矩阵，四个空都和二维索引有关。
// 填完之前这个文件无法通过编译。
#include "common.h"

__global__ void matrixAdd(const float *a, const float *b, float *c, int M, int N) {
    // ====== 空 1：这个线程负责的行号（用 y 方向的内建变量） ======
    int row = threadIdx.y + blockIdx.y * blockDim.y;
    // ====== 空 2：这个线程负责的列号（用 x 方向的内建变量） ======
    int col = threadIdx.x + blockIdx.x * blockDim.x;
    // ====== 空 3：二维边界保护 ======
    if (row < M && col < N) {
        int idx = row * N + col;  // 行优先展开成一维下标
        c[idx] = a[idx] + b[idx];
    }
}

int main() {
    const int M = 1000, N = 700;  // 都不是 16 的整数倍
    const long total = (long)M * N;
    size_t bytes = total * sizeof(float);

    float *h_a = (float *)malloc(bytes);
    float *h_b = (float *)malloc(bytes);
    float *h_c = (float *)malloc(bytes);
    float *h_ref = (float *)malloc(bytes);
    fill_random(h_a, total, 1);
    fill_random(h_b, total, 2);
    for (long i = 0; i < total; i++) h_ref[i] = h_a[i] + h_b[i];

    float *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, bytes));
    CUDA_CHECK(cudaMalloc(&d_b, bytes));
    CUDA_CHECK(cudaMalloc(&d_c, bytes));
    CUDA_CHECK(cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice));

    dim3 threads(16, 16);  // x 方向 16 列，y 方向 16 行
    // ====== 空 4：二维 grid——两个方向都要向上取整 ======
    dim3 blocks((N+15)/16, (M+15)/16);  // 注意 x 和 y
    matrixAdd<<<blocks, threads>>>(d_a, d_b, d_c, M, N);
    CUDA_CHECK_KERNEL();

    CUDA_CHECK(cudaMemcpy(h_c, d_c, bytes, cudaMemcpyDeviceToHost));
    REPORT(check_close(h_c, h_ref, total));
    return 0;
}

```

## prob 2.7

05_grid_stride.cu 的launch 被固定成<<<64, 256>>>，线程总数远小于n，当前FAIL。在launch配置不变的前提下，把 kernel 改成 grid-stride loop，让任意 n都能 PASS。
``` C++
__global__ void vectorAdd(const float *a, const float *b, float *c, int n) {
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    for (int i = idx; i < n; i += blockDim.x * gridDim.x) {
        c[i] = a[i] + b[i];
    }
}
```
然后请回答——这种写法的价值在哪里？launch 只有 16384 个线程时，性能上要付出什么代价？

答：价值：首先kernel配置和数据规模解耦；其次如果n极大，能减少 Block/Grid 启动开销。

代价：首先占用率极低，无法隐藏内存延迟，A100具有108个SM，64个block导致大量SM闲置；其次单个线程执行的任务较多，每个线程要执行 1<<24 / 1<< 14 = 1024次循环，这种串行化计算没能充分利用GPU并行能力；最后跨步访问无法充分利用缓存，同一个线程下一轮访问的地址与上一轮相距 64KB（16384*4B）。

## prob 2.8

第一次输出：
block 5 报到
block 11 报到
block 14 报到
block 8 报到
block 2 报到
block 4 报到
block 10 报到
block 13 报到
block 7 报到
block 1 报到
block 15 报到
block 9 报到
block 3 报到
block 12 报到
block 0 报到
block 6 报到

第二次输出：
block 5 报到
block 11 报到
block 14 报到
block 8 报到
block 2 报到
block 4 报到
block 10 报到
block 13 报到
block 7 报到
block 1 报到
block 15 报到
block 3 报到
block 9 报到
block 12 报到
block 6 报到
block 0 报到

第三次输出：
block 5 报到
block 11 报到
block 14 报到
block 8 报到
block 2 报到
block 10 报到
block 13 报到
block 4 报到
block 1 报到
block 7 报到
block 15 报到
block 3 报到
block 9 报到
block 12 报到
block 6 报到
block 0 报到

(a) 顺序由谁决定？(b) 程序的正确性可以依赖 block 的执行顺序吗？这条限制和Guide 1.1 说
的 scalable programming model 有什么关系？

答：a）block被调度的顺序由硬件调度器决定，是不可预测的
b）不可以。Block 在 SM 之间完全解耦，使得硬件可以无序并行分发，从而保证程序无需改动即可适配任意数量的 SM，这就是 CUDA Scalable Programming Model。

## prob 2.9

```C++
#include <iostream>
#include <cstdio>
#include <cuda_runtime.h>
#include <vector>

#define CUDA_CHECK(code) checkCuda((code), __FILE__, __LINE__)
inline void checkCuda(cudaError_t result, const char *file, int line) {
    if (result != cudaSuccess) {
        std::cerr << "CUDA Runtime Error: " << cudaGetErrorString(result)
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}

void init_data(std::vector<float> &x, std::vector<float> &y, int n) {
    for (int i = 0; i < n; ++i) {
        x[i] = ((i % 2048) - 1024) * 0.5f;
        y[i] = (i % 1024) - 512;
    }
}

__global__ void saxpy_kernel(const float *x, float *y, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        y[idx] += 2.0f * x[idx];
    }
}

int main(int argc, char **argv) {
    int n = 1<<20;
    if (argc > 1) {
        n = atoi(argv[1]);
    }   

    double sum = 0.0;

    if (n <= 0) {
        printf("SUM=%.0f\n", sum);
        return 0;
    }

    std::vector<float> h_x(n), h_y(n);
    init_data(h_x, h_y, n);

    float *d_x, *d_y;
    CUDA_CHECK(cudaMalloc((void**)&d_x, n * sizeof(float)));
    CUDA_CHECK(cudaMalloc((void**)&d_y, n * sizeof(float)));

    CUDA_CHECK(cudaMemcpy(d_x, h_x.data(), n * sizeof(float), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_y, h_y.data(), n * sizeof(float), cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    cudaEventRecord(start);
    saxpy_kernel<<<(n + 255) / 256, 256>>>(d_x, d_y, n);
    CUDA_CHECK(cudaGetLastError());
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float milliseconds = 0;
    CUDA_CHECK(cudaEventElapsedTime(&milliseconds, start, stop));

    CUDA_CHECK(cudaMemcpy(h_y.data(), d_y, n * sizeof(float), cudaMemcpyDeviceToHost));

    for (int i = 0; i < n; ++i) {
        sum += h_y[i];
    }

    printf("SUM=%.0f\n data size: %d, kernel time: %.0f\n", sum, n, milliseconds);

    return 0;
}
```

# 3 SIMT
## prob 3.1

设 blockDim = (8, 8, 1)。（x，y，z）
(a) threadIdx = (3, 5, 0) 的线性编号是多少？它在第几个 warp、warp 内第几个 lane？
(b) 这个 block 一共占多少个 warp？
(c) 若 blockDim = (33, 1, 1)，占几个 warp？这样配置浪费在哪里？

答：a）threadIdx = (3, 5, 0) 的线性编号是3 + 5 * 8 + 0 = 43；在第 2 个 warp， 第 12 个 lane；
b）block 共 8 * 8 * 1 = 64 个 threads，共占2个warp；
c）共 33 * 1 * 1  = 33 个 threads，占 2个warp，这样配置warp1 仅有 1 个 active thread，浪费资源调度。

## prob 3.2

m3_simt/01_divergence.cu 的两个 kernel 每线程计算量相同，分支划分不同——一个按 thread编号的奇偶分（同一个 warp 里一半一半），一个按 warp 边界对齐分。请先预测一下哪个版本运行会更快一点，大概快几倍.

答：显然第二种会更快，第二种策略没有 warp divergence。当发生 warp divergence 时，分支通过mask分别执行，所以第二种策略大概快 2 倍。

请解释实测比值，并回答——若两个分支的计算量一大一小，按 thread 编号奇偶分的 kernel和按 warp 边界对齐分的 kernel 的运行时间分别由什么决定？

warp 内分支 (tid % 2)    :    2.205 ms
按 warp 分支 (tid/32 % 2):    1.109 ms
比值: 1.99

答：实测比值：1.99。对于按 thread 编号奇偶分，在不考虑线程独立调度的情况下，完成分支 A 的 threads 需要等待 分支B的threads 执行完成，所以kernel时间仍由分支时间的和决定；对于按 warp 边界对齐分的 kernel，不同的warp执行不同的分支，运行时间由计算量大的分支决定。

## prob 3.3

02_sync_matters.cu 让每个 block 用 shared memory 把自己的 256 个元素倒序。请按文件开头的注释内容进行实验。

(a) 为什么注释掉 sync 后代码不能正确地运行？(b) (Optional) 注释掉 sync 后，翻转后的数组错的位置比较随机，但是有些位置一直是对的，试解释原因。（tip: 算一算 t与 255 −t有没有可能落在同一个 warp）

答：删除__syncthreads()后，共运行十次 Mismatch 位置：128 6次，96 2次，0 2次
a）代码设置的block大小是256，即有8个warp。因为不同线程的执行顺序未定义和全局内存访问的影响，所以共享内存的存取并不能在同一时间内完成，删除sync后，当线程t执行到写out数组时，线程BLOCK - 1 - t可能还没能读取全局内存将值存入共享内存，因此代码不能正确运行。

b）在没有同步时，warp 调度器以未定义的顺序执行 warp，所以错误位置随机。显然 t与 255 −t没有可能落在同一个 warp，所以一直对的这些位置可能恰好这些位置的写入 warp 每次都先于读取 warp 被调度。

## prob 3.4

__syncthreads 只能同步本 block 内的 threads，那需要全 grid 同步时，标准做法是什么？

答：隐式同步，CUDA内核启动是异步的，但两个内核之间隐式存在一个全局同步点，前一个内核的所有线程执行完毕后，后一个内核才会开始；显示同步，CUDA 9.0 引入 `Cooperative Group` 提供了全网格同步机制 `grid.sync()`.

## prob 3.5

在03_reduce.cu 里从零实现两个求和归约kernel（判测与计时的代码已经写好）。两个kernel的 contract 见文件头。PASS 后，试解释实测性能差距的原因。

答：
interleaved: PASS  平均 0.0806 ms; contiguous : PASS  平均 0.0482 ms; interleaved / contiguous = 1.67x

interleaved 全程warp分歧，以第1轮为例，同一个warp中，线程0，2，4，...，30 活跃，第二轮，线程0，4，8，16活跃，当s愈大时，空闲的线程愈多，每一轮循坏都存在严重的资源浪费。

contiguous ，前3轮活跃线程是0~127、0~63、0~32，这些活跃线程刚好填好一个或多个warp，而其他完全不执行，warp内线程不存在分歧，虽然后5轮开始出现warp内分歧，但此时只有一个warp工作，开销较小。

（contigous当s为32的倍数（128，64，32）时，buf[tid]和buf[tid+s]落在同一个bank上，会产生2-way bank conflict；而交错式不存在bank conflict。说明warp分歧导致的控制流序列化的开销远大于bank conflict的开销。）

（Optional）基于两点事实——(a) __shfl_down_sync 是warp 内寄存器级别的线程间数据交换指令，自带同步效果且延迟极小；(b) 归约到最后32 个元素后，活跃线程若都落在同一个warp里，就不再需要__syncthreads（可以想想为什么）——据此试写出第三版优化后的kernel。测试时只会跑前两版，第三版自己在 main 里照着加一次 run_one 调用即可。

答：最后32个元素在同一warp内进行归约，其他7个warp完全空闲，不需要参与同步，且同一warp内执行相同的指令，所以不需要同步。
```C++
__global__ void reduce_interleaved(const float *in, float *out) {
    // TODO：从这里开始写（交错配对版本）
    __shared__ float buf[BLOCK];
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + tid;
    buf[tid] = in[idx];
    __syncthreads();

    for (int s = 1; s < blockDim.x; s *= 2) {
        if (tid % (2*s) == 0)
            buf[tid] = buf[tid] + buf[tid + s];
        __syncthreads();
    }

    if (tid == 0)
        out[blockIdx.x] = buf[0];
}

__global__ void reduce_contiguous(const float *in, float *out) {
    // TODO：从这里开始写（连续配对版本）
    __shared__ float buf[BLOCK];
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + tid;
    buf[tid] = in[idx];
    __syncthreads();

    for (int s = blockDim.x / 2; s > 0; s /=2) {
        if (tid < s) {
            buf[tid] = buf[tid] + buf[tid + s];
        }
        __syncthreads(); // 这里可以从b）所说优化，此处就不写了
    }

    if (tid == 0)
        out[blockIdx.x] = buf[0];
}

__global__ void reduce_shfl(const float *in, float *out) {
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + tid;
    
    float val = in[idx];
    for (int s = 1; s < 32; s *= 2)
        val += __shfl_down_sync(0xffffffff, val, s);

    __shared__ float warp_sum[32];
    if ((tid & 31) == 0) // 注意 == 的优先级更高
        warp_sum[tid / 32] = val;
    __syncthreads();

    if (tid == 0) {
        float sum = 0.0;
        for (int i = 0; i < (blockDim.x + 31) / 32; ++i)
            sum += warp_sum[i];
        out[blockIdx.x] = sum;
    }
        
}
```

# 4 Memory
## prob 4.1

空间        谁可见         生命周期    片上/片外        谁管理

register    单个线程        线程        片上            编译器

local       单个线程        线程        片外（但被缓存） 编译器

shared   同一线程块上的线程  线程块     片上            用户

global      所有线程        核函数      片外            用户

constant    所有线程（只读） 核函数     片外            用户

L1/L2 cache    所有线程     核函数      片上            硬件

## prob 4.2

1. `__shared__ float tile[BLOCK + 2 * RADIUS];`
2. ` __syncthreads();`
3. `out[g] = (tile[l - 1] + tile[l] + tile[l + 1]) / 3.f;`
4. `extern __shared__ float tile[];`
5. `stencil_dynamic<<<blocks, BLOCK, BLOCK + 2*RADIUS>>>(d_in, d_out, n);`

## prob 4.3

结果会包含两个版本的耗时（差距可能极小，甚至测不出来性能收益——想想为什么），回答constant cache 真正的优势在哪种访问模式。

答：基准 global  : PASS  平均 0.6381 ms

global  : PASS  平均 0.6334 ms; constant: PASS  平均 0.6225 ms; global / constant = 1.02x

```C++
__constant__ float COEF[8];
 CUDA_CHECK(cudaMemcpyToSymbol(COEF, h_coef, sizeof(h_coef)));
```

常量内存用于存储少数数据且全线程在每一轮计算中都读取同一个值的参数，比如卷积核的固定权重、物理方程的固定系数、数学常量（PI、e）等。因为正常读取global内存也可以通过L1/L2缓存，而且不同线程访问连续地址时，也能通过合并访问合并为一次访存事务，但常量内存则不然，如果warp内32个线程访问不同常量内存地址，则会序列化变成串行读取（常量内存只有广播模式）。

## prob 4.4

判断对错，可以顺带补一句理由。
(a) local memory 的“local”指作用域私有，它实际上在片外显存里。
(b) 对数组用运行期才知道的下标做索引，可能迫使它被放进 local memory。

答：a）对。b）对。编译器倾向于将数组元素映射到物理寄存器，但寄存器编号必须在编译期确定。当数组下标是运行期才能确定的变量时，编译器无法静态分配寄存器，因此通常会将该数组强制分配到 local 内存中。

## prob 4.5

```C++
atomicAdd(&hist[v], 1);
```
平均耗时 5.0198 ms  (3.34 GB/s)

## prob 4.6

测试结果包含与 naive 实现相比较的耗时、吞吐。试解释提速来自哪里。

答：
测试结果：

naive: PASS  平均 4.7454 ms  (3.54 GB/s)

priv : PASS  平均 0.0685 ms  (244.89 GB/s)

naive / priv = 69.27x

首先，naive版本所有线程竞争hist数组的写入，竞争激烈，导致写入过程几乎串行化，所以吞吐很低；优化版每个block的线程竞争自己的共享内存的写入，竞态相对减小。其次，每次将结果写入hist数组对于global memory的访问是随机的，不能合并访问；优化版先写入共享内存，再统一写入全局内存，一个warp内的线程写入地址是连续的可以合并写入。

```C++
__global__ void histogram_priv(const unsigned char *data, unsigned int *hist,
                               int n) {
    // TODO：从这里开始写（shared memory 私有化版本）
    __shared__ uint32_t local_hist[BINS];
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    local_hist[threadIdx.x] = 0;
    __syncthreads();

    int stride = blockDim.x * gridDim.x;
    for (; i < n; i += stride) {
        atomicAdd(&local_hist[data[i]], 1u);
    }

    __syncthreads();
    atomicAdd(&hist[threadIdx.x], local_hist[threadIdx.x]); 
}
```

## prob 4.7

stride           ms         GB/s

1       0.6612        203.0

2       1.0097        132.9

4       1.6114         83.3

8       2.9332         45.8

16       2.7606         48.6

32       2.7420         48.9

观察数据变化趋势，并简析趋势的成因。

stride从1至8，执行时间逐步上升，吞吐量逐步降低；从8至16、32，执行时间略有降低，吞吐量略微提升，但是16与32的数据可以认为是稳定的。

```C++
__global__ void strided_copy(const float *in, float *out, int n, int stride) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        int j = (long)i * stride & (n - 1);
        out[i] = in[j];
    }
}
```
观察核函数可以发现，stride改变的是同一warp内的线程访问的全局内存的地址。当stride为1时，warp内线程访问连续地址，可以合并为一次访存事务，所以速度最快；当stride依次增长为2、4、8；访存事务逐步变为2次、4次和8次，所以性能逐步降低。现代NVIDIA GPU的L2缓存行大小为32字节，当stride大于8时，一个warp的访问已经完全覆盖32个不同的缓存行，因此内存事务已达到硬件在此粒度下的最大值，所以性能没有继续恶化；stride=8显然会发生bank conflict，所有数据都落在同一个bank，而16、32分别是2-way和4-way相对更好，所以略快一点。

## prob 4.8

请回答：(a) 用程序开头打印的“shared memory / SM”和“最大常驻线程 / SM”，手算其中一个的驻留 block 数和 occupancy，和 API 的结果对照。(b) 带宽为什么随 occupancy 下降？用“延迟隐藏需要足够多的常驻 warp”组织你的解释。(c) 表中带宽随 occupancy 单调下降，但明显不成正比——从 100% 到 75% 带宽掉了多少？从 37.5% 到 12.5% 又掉了多少？试解释这个差别。

```
NVIDIA GeForce RTX 4060 Laptop GPU：shared memory 100 KB / SM，最大常驻 1536 线程 / SM

shared/block   理论 block/SM  occupancy   实测带宽
     0.0 KB          6          100.0%      156.9 GB/s
    13.2 KB          6          100.0%      157.1 GB/s
    15.0 KB          6          100.0%      160.1 GB/s
    18.0 KB          5           83.3%      172.8 GB/s
    29.0 KB          3           50.0%      195.9 GB/s
    55.0 KB          1           16.7%      129.0 GB/s

cudaOccupancyMaxPotentialBlockSize 建议（smem = 0 时）：blockSize = 768
```

答：
a）分配15KB shared/block，该设备 shared memory 100KB/SM，则理论 block/SM 为 100KB/15KB = 6，最大常驻 1536 线程/SM，目前最多有6 * 256 = 1536个线程正好满足所以100% occupancy。

b）当一部分warp在等待全局内存访存时，SM通过切换其他活跃warp来掩盖访存时间（零开销），所以足够多的驻留warp才能有效延迟隐藏。occupancy降低意味着驻留warp数降低，一旦所有活跃warp都陷入内存访问等待，SM就被迫stall，带宽自然就降低了。

理论上确实应该是这样，但是从实测数据发现并不是，occupancy在50%时带宽最大，，同时occupancy在83.3%时的带宽也大于occupancy 100%时。由此可见occupancy越大并不能一定代表性能越好。当为了延迟隐藏而切换warp时，过多的数据访存导致内存总线被过度拥挤，而适当的warp数是内存控制器能高效流水线化处理的最佳请求深度。

c）

# 5
## prob 5.1

回答下列问题：(a) 哪个数值可以当作 kernel 耗时写进报告？(b) 另外两个各具体测的是什么？

host 计时、不等 GPU :     0.0179 ms;
host 计时、等 GPU   :     0.6480 ms;
cudaEvent 计时      :     0.5601 ms;

答：a）cudaEvent 计时可以作为 kernel 耗时记录

b）host计时、不等GPU 测的是 核函数启动的时间；host计时、等GPU 测的是 kernel时间加上host和device的同步时间

## prob 5.2

判断对错，可以顺带补一句理由。

(a) 同一个 stream 里的操作按提交顺序执行。

(b) kernel 启动后，host 代码立刻继续往下执行。

(c) unified memory 下，CPU 访问一页正被 GPU 占用的内存，会触发缺页与页迁移。

答：a）对；b）对；c）对。因为页面在GPU端，所以会触发缺页，OS捕获到这个异常后，系统启动页迁移，通过PCIe等总线将数据从GPU显存拷贝回CPU。

# 6
## prob 6.1

判断对错，可以顺带补一句理由。

(a) tile 是显存里的一块可变区域，kernel 通过指针直接改写它。

(b) 对 tile 的一次运算（如两个 tile 相加）由编译器映射到 block 内的多个线程上执行。

(c) tile 模型与 SIMT 模型互斥，一个 CUDA 程序只能选一种。

答：a）

# 7

## prob 7.1


