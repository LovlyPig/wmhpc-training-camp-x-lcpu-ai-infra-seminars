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

# 1
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

# 2
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

02_vector_add_um.cu 代码完整，但目前是“显式内存管理”的版本。改之前先按原样编译运行
一次，记下耗时——这一版会被你的改动覆盖掉，下面 (b) 要拿它做对照。然后按文件头的说明改
成 unified memory 版（cudaMallocManaged），并保持文件头写明的计时窗口不变。

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

05_grid_stride.cu 的launch 被固定成<<<64, 256>>>，线程总数远小于n，当前FAIL。在launch
配置不变的前提下，把 kernel 改成 grid-stride loop，让任意 n都能 PASS。
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

