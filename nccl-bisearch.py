import os
import sys
import subprocess
import hashlib

def run_mpirun(np_count, host_config):
    if np_count < 2:
        return
    print(f"SERVER: {np_count} => {host_config}")
    md5 = hashlib.md5(host_config.encode()).hexdigest()
    output_file = os.path.join(os.getcwd(), "nccl-log", f"temp_mpirun_{md5}.log")
    print(f"LOG: {output_file}")

    # 设置环境变量
    env = os.environ.copy()

    # 构造命令
    cmd = [
        "mpirun",
        "--allow-run-as-root",
        "--np", str(np_count),
        "--map-by", "node",
        "--bind-to", "none",
        "--mca", "btl", "self,tcp",
        "--mca", "btl_tcp_if_include", "bond0",
        "-H", host_config,
        "-x", "NCCL_NVLS_ENABLE=0",
        "-x", "NCCL_MAX_NCHANNELS=64",
        "-x", "NCCL_MIN_NCHANNELS=32",
        "-x", "NCCL_DEBUG=INFO",
        "-x", "NCCL_IB_HCA=", os.environ.get("NCCL_IB_HCA"),
        "-x", "NCCL_SOCKET_IFNAME=bond0",
        "all_reduce_perf",
        "-b", "16G",
        "-e", "16G",
        "-f", "2",
        "-g", "8"
    ]
    print("CMD:", " ".join(cmd))

    # 执行命令
    try:
        result = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("mpirun failed")
        print(e.output)
        sys.exit(1)

    # 写入日志文件
    with open(output_file, "w") as f:
        f.write(result.stdout)

    # 提取结果
    busbw = None
    for line in result.stdout.split("\n"):
        if line.startswith(" 17179869184"):
            parts = line.split()
            if len(parts) >= 9:
                busbw = float(parts[7])
                break
    print(f"BUSBW: {busbw}")
    return busbw


def recursive_bisection(machines, threshold):
    total = len(machines)
    if total <= 1:
        return
    half = total // 2
    first_half = machines[:half]
    second_half = machines[half:]

    first_busbw = run_mpirun(len(first_half), ",".join(first_half))
    second_busbw = run_mpirun(len(second_half), ",".join(second_half))

    if first_busbw is not None and first_busbw <= threshold:
        recursive_bisection(first_half, threshold)
    if second_busbw is not None and second_busbw <= threshold:
        recursive_bisection(second_half, threshold)


if __name__ == "__main__":
    # 检查参数
    if len(sys.argv) != 3:
        print("错误: 请提供 hostfile 文件和 busbw 阈值作为参数。")
        sys.exit(1)

    hostfile = sys.argv[1]
    try:
        threshold = float(sys.argv[2])
    except ValueError:
        print("错误: 阈值参数必须是一个有效的浮点数。")
        sys.exit(1)

    if not os.path.isfile(hostfile):
        print(f"错误: {hostfile} 文件不存在。")
        sys.exit(1)

    # 读取hostfile
    machines = []
    with open(hostfile, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                machines.append(line)

    # 创建日志目录
    os.makedirs("nccl-log", exist_ok=True)

    # 运行完整配置
    initial_config = ",".join(machines)
    total_busbw = run_mpirun(len(machines), initial_config)

    if total_busbw is not None and total_busbw <= threshold:
        # 开始递归二分
        recursive_bisection(machines, threshold)