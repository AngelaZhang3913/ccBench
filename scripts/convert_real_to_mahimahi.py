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
    
    # Convert bandwidth values to packets per millisecond
    packet_times = []
    for i, timestamp in enumerate(timestamps):
        if i == 0:
            continue  # Skip the first timestamp as there's no interval
        
        time_interval = (timestamps[i] - timestamps[i-1]) * MILLISECONDS_IN_SECOND
        num_packets = int((bandwidths[i] * 1e6) / (BITS_IN_BYTE * BYTES_PER_PKT))
        
        packet_times.extend([int(timestamp * MILLISECONDS_IN_SECOND)] * num_packets)
    
    # Write Mahimahi trace file
    with open(output_file, 'w') as out_f:
        for time in packet_times:
            out_f.write(f"{time}\n")
    
    print(f"Converted {json_file} -> {output_file}")

# Process all JSON traces recursively
for root, _, files in os.walk(TRACE_DIR):
    for file in files:
        if file.endswith(".json"):
            input_path = os.path.join(root, file)
            relative_path = os.path.relpath(input_path, TRACE_DIR)  # Maintain directory structure
            output_path = os.path.join(OUTPUT_DIR, relative_path.replace(".json", ""))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            convert_json_to_mahimahi(input_path, output_path)
