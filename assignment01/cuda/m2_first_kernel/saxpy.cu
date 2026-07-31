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