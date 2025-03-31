import os
import json
import numpy as np

# Constants
BYTES_PER_PKT = 1500.0  # Packet size in bytes
BITS_IN_BYTE = 8.0  # Bits per byte
MILLISECONDS_IN_SECOND = 1000  # Number of milliseconds in a second

# Directories
TRACE_DIR = os.path.expanduser("~/Genet/cc_trace")
OUTPUT_DIR = os.path.expanduser("~/ccBench/mahimahi_traces")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def convert_json_to_mahimahi(json_file, output_file):
    """Convert JSON time-bandwidth trace file to a Mahimahi trace."""
    print(f"Processing {json_file} -> {output_file}")
    
    with open(json_file, 'r') as f:
        trace_data = json.load(f)
    
    timestamps = trace_data.get("timestamps", [])
    bandwidths = trace_data.get("bandwidths", [])
    
    if not timestamps or not bandwidths:
        print(f"Skipping {json_file} due to missing data.")
        return
    
    with open(output_file, 'w') as mf:
        for i in range(len(timestamps) - 1):
            start_time = int(timestamps[i] * MILLISECONDS_IN_SECOND)
            end_time = int(timestamps[i + 1] * MILLISECONDS_IN_SECOND)
            bandwidth_mbps = bandwidths[i]
            
            mbps_to_bps = bandwidth_mbps * 1e6  # Convert Mbps to bps
            bps_to_Bps = mbps_to_bps / BITS_IN_BYTE  # Convert bps to Bps
            Bps_to_pkts = bps_to_Bps / BYTES_PER_PKT  # Convert Bps to packets per sec
            pkt_per_millisec = Bps_to_pkts / MILLISECONDS_IN_SECOND  # Convert to packets per ms
            
            for t in range(start_time, end_time):
                num_packets = int(np.floor((t + 1) * pkt_per_millisec)) - int(np.floor(t * pkt_per_millisec))
                for _ in range(num_packets):
                    mf.write(f"{t}\n")
    
    print(f"Converted {json_file} -> {output_file}")

if __name__ == "__main__":    
    # Process all JSON traces recursively
    for root, _, files in os.walk(TRACE_DIR):
        for file in files:
            if file.endswith(".json"):
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_path, TRACE_DIR)  # Maintain directory structure
                leaf_dir = os.path.basename(root)  # Get the leaf directory name
                output_filename = f"{leaf_dir}_{file.replace('.json', '')}"  # New naming format
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                convert_json_to_mahimahi(input_path, output_path)
