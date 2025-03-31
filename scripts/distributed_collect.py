import paramiko
import yaml
import concurrent.futures
import argparse
import time
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Distribute congestion control collection across nodes")
args = parser.parse_args()

# Load node configuration from config.yaml
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

servers = config["servers"]
username = "janechen"

# List of congestion control schemes
cc_schemes = ["reno", "pure", "cubic", "vegas", "bbr", "cdg", "hybla", "highspeed", "illinois",
              "westwood", "yeah", "htcp", "bic", "veno"]

num_servers = len(servers)
schemes_per_server = len(cc_schemes) // num_servers
remainder = len(cc_schemes) % num_servers

# Assign schemes to each node
scheme_assignments = {}
start_idx = 0

for i, server in enumerate(servers):
    num_schemes = schemes_per_server + (1 if i < remainder else 0)
    scheme_assignments[server["hostname"]] = cc_schemes[start_idx:start_idx + num_schemes]
    start_idx += num_schemes

def run_remote_collection(server, schemes):
    """SSH into the server, install dependencies, update repo, and start collection in a tmux session."""
    print(f"Starting collection on {server} with schemes: {schemes}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(server, username=username)

        schemes_str = " ".join(schemes)

        commands = [
            "tmux kill-session -t collect || true",  # Kill existing session if any
            "cd ~/ccBench/ && git reset --hard && git fetch && git checkout dataset-collection && git pull",
            "cd ~/ccBench/pantheon-modified/third_party/tcpdatagen/ && chmod +x *.sh && ./build.sh",
            "chmod +x /users/janechen/ccBench/pantheon-modified/src/experiments/palantir_collect.sh",
            "rm -rf ~/ccBench/mahimahi_traces/*",
            "tmux new-session -d -s collect",
            "tmux send-keys -t collect 'source ~/venv/bin/activate' C-m",
            # "tmux send-keys -t collect 'python /users/janechen/ccBench/scripts/convert_real_to_mahimahi.py' C-m",
            # "tmux send-keys -t collect 'cd /users/janechen/ccBench/pantheon-modified/src/experiments' C-m",
            # "tmux send-keys -t collect 'python /users/janechen/ccBench/scripts/generate_mahimahi_traces.py' C-m",
            f"tmux send-keys -t collect './palantir_collect.sh {schemes_str}' C-m"
        ]

        for cmd in commands:
            print(f"[{server}] $ {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            time.sleep(1)  # Brief pause

            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()

            if out:
                print(f"[{server}] STDOUT:\n{out}")
            if err:
                print(f"[{server}] STDERR:\n{err}")

    except Exception as e:
        print(f"Error running commands on {server}: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Run collection on all servers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_servers) as executor:
        futures = {
            executor.submit(run_remote_collection, server["hostname"], scheme_assignments[server["hostname"]]): server["hostname"]
            for server in servers
        }
        for future in concurrent.futures.as_completed(futures):
            server = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error starting collection on {server}: {e}")

    print("Collection commands have been issued to all servers.")
