# rdma_bench_tools

## NCCL二分查找

NCCL_IB_HCA=mlx5_gdr_0,mlx5_gdr_1,mlx5_gdr_2,mlx5_gdr_3,mlx5_gdr_4,mlx5_gdr_5,mlx5_gdr_6,mlx5_gdr_7 python3 nccl-bisearch.py hostfile 360

## RDMA

# 延迟测试

```
python3 rdma-bench.py server --cmd=ib_write_lat
python3 rdma-bench.py client --remote=10.207.67.3 --cmd=ib_write_lat
```

# 单流测试

```
python3 rdma-bench.py server
python3 rdma-bench.py client --remote=10.207.67.3
```

# 多流测试

```
python3 rdma-bench.py server --args="-q 16"
python3 rdma-bench.py client --remote=10.207.67.3 --args="-q 16"
```

# 指定NUMA测试

```
python3 rdma-bench.py server --numa=0
python3 rdma-bench.py client --remote=10.207.67.3 --numa=0
```

# 指定devices测试

```
python3 rdma-bench.py server --devices=mlx5_0,mlx5_1
python3 rdma-bench.py client --remote=10.207.67.3 --devices=mlx5_0,mlx5_1
```

# 指定多卡之间并发测试

默认为-1，即所有卡都并发压测

```
python3 rdma-bench.py server --concurrency=2
python3 rdma-bench.py client --remote=10.207.67.3 --concurrency=2
```

# 筛选400G网卡

```
python3 rdma-bench.py server --rate=400
python3 rdma-bench.py client --remote=10.207.67.3 --rate=400
```

# ib_read_bw测试

```
python3 rdma-bench.py server --cmd=ib_read_bw --args="--report_gbits"
python3 rdma-bench.py client --remote=10.207.67.3 --cmd=ib_read_bw --args="--report_gbits"
```
