import subprocess
import re
import os
import sys
from multiprocessing import Pool
import argparse


def get_ib_device_rate(ib_device):
    """
    Get the rate of a specified IB device from ibstat -v output.
    :param ib_device: Name of the IB device.
    :return: Rate value, or None if an error occurs.
    """
    try:
        result = subprocess.run(['ibstat', '-v', ib_device], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        output = result.stdout
        match = re.search(r'Rate:\s+(\d+)', output)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error getting rate for {ib_device}: {e}")
    return -1


def get_ib_devices():
    """
    Get the list of IB devices in the system.
    :return: List of IB devices.
    """
    try:
        result = subprocess.run(['ibdev2netdev'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        output = result.stdout
        devices = []
        for line in output.splitlines():
            match = re.search(r'(\S+)\s+(\S+)', line)
            if match:
                devices.append(match.group(1))
        return devices
    except Exception as e:
        print(f"Error getting IB devices: {e}")
        return []


def get_cpu_topology():
    """
    Get CPU topology information as a dictionary with NUMA nodes as keys and CPU lists as values.
    :return: CPU topology dictionary.
    """
    try:
        result = subprocess.run(['lscpu', '--parse=NODE,CPU'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        output = result.stdout
        numa_nodes = {}
        for line in output.splitlines():
            if not line.startswith('#'):
                numa, cpu = line.strip().split(',')
                numa = int(numa)
                cpu = int(cpu)
                if numa not in numa_nodes:
                    numa_nodes[numa] = []
                numa_nodes[numa].append(cpu)
        return numa_nodes
    except Exception as e:
        print(f"Error getting CPU topology: {e}")
        return {}


def get_ib_device_numa(ib_device):
    """
    Get the NUMA node of a specified IB device.
    :param ib_device: Name of the IB device.
    :return: NUMA node number, or None if an error occurs.
    """
    numa_path = f"/sys/class/infiniband/{ib_device}/device/numa_node"
    if os.path.exists(numa_path):
        try:
            with open(numa_path, 'r') as f:
                numa = int(f.read().strip())
                return numa
        except Exception as e:
            print(f"Error reading NUMA node info for {ib_device}: {e}")
    return None


def run_ib_client(args):
    """
    Run the ib_write_bw client command.
    :param args: Tuple containing local device, remote IP, CPU number, additional args, and port.
    """
    cmd, local_device, remote_ip, cpu, append_args, port = args
    try:
        command = f"taskset -c {cpu} {cmd} -d {local_device} -p {port} {remote_ip} {append_args}"
        print(f"Exec: {command}")
        result = subprocess.run(command, bufsize=100000, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        if result.returncode != 0:
            print(f"Client command failed, error: {result.stderr}")
            return
        output = result.stdout
        match = re.search(
            r'#bytes\s+#iterations\s+BW peak\[Gb/sec\]\s+BW average\[Gb/sec\]\s+MsgRate\[Mpps\]\s*\n\s*\d+\s+\d+\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s*',
            output)
        if match:
            bw_avg = match.group(1)
            print(
                f"Local NIC: {local_device}, Rate: {get_ib_device_rate(local_device)}, Remote IP: {remote_ip}, Avg BW: {bw_avg} Gbps")
        else:
            match = re.search(
                r'#bytes\s+#iterations\s+t_min\[usec\]\s+t_max\[usec\]\s+t_typical\[usec\]\s+t_avg\[usec\]\s+t_stdev\[usec\]\s+99%\spercentile\[usec\]\s+99.9%\spercentile\[usec\]\s*\n\s*\d+\s+\d+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)',
                output)
            if match:
                lat = match.group(1)
                print(f"Local NIC: {local_device}, Remote IP: {remote_ip}, 99.9% Latency: {lat} us")
            else:
                print(f"No data found for {local_device}")
    except Exception as e:
        print(f"Error running client: {e}")


def run_ib_server(args):
    """
    Run the ib_write_bw server command.
    :param args: Tuple containing local device, CPU number, additional args, and port.
    """
    cmd, local_device, cpu, append_args, port = args
    try:
        command = f"taskset -c {cpu} {cmd} -d {local_device} -p {port} {append_args}"
        print(f"Exec: {command}")
        result = subprocess.run(command, bufsize=100000, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        if result.returncode != 0:
            print(f"Server command failed, error: {result.stderr}")
            return
        output = result.stdout
        match = re.search(
            r'#bytes\s+#iterations\s+BW peak\[Gb/sec\]\s+BW average\[Gb/sec\]\s+MsgRate\[Mpps\]\s*\n\s*\d+\s+\d+\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s*',
            output)
        if match:
            bw_avg = match.group(1)
            print(f"Server NIC {local_device}, Rate: {get_ib_device_rate(local_device)}, Avg BW: {bw_avg} Gbps")
        else:
            match = re.search(
                r'#bytes\s+#iterations\s+t_min\[usec\]\s+t_max\[usec\]\s+t_typical\[usec\]\s+t_avg\[usec\]\s+t_stdev\[usec\]\s+99%\spercentile\[usec\]\s+99.9%\spercentile\[usec\]\s*\n\s*\d+\s+\d+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)',
                output)
            if match:
                lat = match.group(1)
                print(f"Server NIC {local_device}, 99.9% Latency: {lat} us")
            else:
                print(f"No data found for {local_device}")

    except Exception as e:
        print(f"Error running server: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('role', type=str, help='role of the node', choices=['client', 'server'])
    parser.add_argument('--remote', type=str, help='remote ip')
    parser.add_argument('--cmd', type=str,
                        default='ib_write_bw --report_gbits',
                        help='exec cmd')
    parser.add_argument('--devices', type=lambda s: [item.strip() for item in s.split(',')], default=[],
                        help='bench devices')
    parser.add_argument('--numa', type=str,
                        default='',
                        help='bench numa')
    parser.add_argument('--concurrency', type=int,
                        default=-1,
                        help='bench concurrency')
    parser.add_argument('--args', type=str,
                        default='',
                        help='append args')
    parser.add_argument('--rate', type=int, help='Desired NIC rate')
    args = parser.parse_args()

    mode = args.role
    append_args = args.args
    remote_ip = args.remote
    cmd = args.cmd
    desired_rate = args.rate
    concurrency = args.concurrency
    bench_numa = args.numa
    bench_devices = args.devices

    local_ib_devices = get_ib_devices()
    if desired_rate is not None:
        local_ib_devices = [device for device in local_ib_devices if int(get_ib_device_rate(device)) == desired_rate]

    cpu_topology = get_cpu_topology()

    start_port = 18515

    if mode == "client":
        tasks = []
        cpu_index = {numa: 0 for numa in cpu_topology}
        for local_device in local_ib_devices:
            numa = get_ib_device_numa(local_device)
            if bench_numa and numa != int(bench_numa):
                continue
            if len(bench_devices) !=0 and local_device not in bench_devices:
                continue
            if numa is not None and numa in cpu_topology:
                cpu_list = cpu_topology[numa]
                if cpu_index[numa] < len(cpu_list):
                    cpu = cpu_list[cpu_index[numa]]
                    port = start_port + len(tasks)
                    tasks.append((cmd, local_device, remote_ip, cpu, append_args, port))
                    cpu_index[numa] += 1
                else:
                    print(f"No enough CPUs for NIC {local_device} in NUMA node {numa}")
            else:
                print(f"No valid NUMA node or CPU list found for {local_device}")
        if concurrency == -1:
            concurrency =  len(tasks)
        with Pool(processes=concurrency) as pool:
            pool.map(run_ib_client, tasks)

    elif mode == "server":
        tasks = []
        cpu_index = {numa: 0 for numa in cpu_topology}
        for local_device in local_ib_devices:
            numa = get_ib_device_numa(local_device)
            if bench_numa and numa != int(bench_numa):
                continue
            if len(bench_devices) !=0 and local_device not in bench_devices:
                continue
            if numa is not None and numa in cpu_topology:
                cpu_list = cpu_topology[numa]
                if cpu_index[numa] < len(cpu_list):
                    cpu = cpu_list[cpu_index[numa]]
                    port = start_port + len(tasks)
                    tasks.append((cmd, local_device, cpu, append_args, port))
                    cpu_index[numa] += 1
                else:
                    print(f"No enough CPUs for NIC {local_device} in NUMA node {numa}")
            else:
                print(f"No valid NUMA node or CPU list found for {local_device}")
        with Pool() as pool:
            pool.map(run_ib_server, tasks)

    else:
        print("Invalid mode. Use 'client' or 'server'.")
        sys.exit(1)
    