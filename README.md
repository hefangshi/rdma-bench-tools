# rdma_bench_tools

## NCCL

NCCL_IB_HCA=mlx5_gdr_0,mlx5_gdr_1,mlx5_gdr_2,mlx5_gdr_3,mlx5_gdr_4,mlx5_gdr_5,mlx5_gdr_6,mlx5_gdr_7 python3 bi_test.py hostfile 360

## RDMA

# 延迟测试
python3 rdma_test.py server --cmd=ib_write_lat
python3 rdma_test.py client --remote=10.207.67.3 --cmd=ib_write_lat

# 单流测试
python3 rdma_test.py server
python3 rdma_test.py client --remote=10.207.67.3

# 多流测试
python3 rdma_test.py server --args="-q 16"
python3 rdma_test.py client --remote=10.207.67.3 --args="-q 16"

# 筛选400G网卡
python3 rdma_test.py server --args="-q 16" --rate=400
python3 rdma_test.py client --remote=10.207.67.3 --args="-q 16" --rate=400

# ib_read_bw测试
python3 rdma_test.py server --cmd=ib_read_bw --args="--report_gbits"
python3 rdma_test.py client --remote=10.207.67.3 --cmd=ib_read_bw --args="--report_gbits"
