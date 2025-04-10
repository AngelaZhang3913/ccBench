import os
import pickle
import numpy as np
import random
from multiprocessing import Pool, cpu_count

def parse_one_way_delay(fname: str) -> float:
    parts = fname.split('_')
    return float(parts[-4])

def build_sample(lines, start_line, two_owd):
    lines_per_rtt = int(two_owd / 10.0)
    sample = []

    for rtt_idx in range(20):
        sub_start = start_line + rtt_idx * lines_per_rtt
        sub_end = sub_start + lines_per_rtt
        rtt_lines = lines[sub_start:sub_end]

        if len(rtt_lines) < lines_per_rtt:
            return None

        col3, col4, col8, col68, col77 = [], [], [], [], []

        for line in rtt_lines:
            cols = line.split()
            if len(cols) < 77:
                return None
            col3.append(float(cols[2]))
            col4.append(float(cols[3]))
            col8.append(float(cols[7]))
            col68.append(float(cols[67]))
            col77.append(float(cols[76]))

        sample.append([
            two_owd / 100.0,
            np.mean(col3),
            np.mean(col4),
            np.mean(col8),
            np.mean(col68),
            np.mean(col77)
        ])

    return np.array(sample, dtype=np.float32)

def process_one_file(filepath):
    fname = os.path.basename(filepath)
    with open(filepath, "r") as f:
        lines = f.readlines()

    two_owd = 2.0 * parse_one_way_delay(fname)
    lines_per_rtt = int(two_owd / 10.0)
    block_len = 20 * lines_per_rtt
    max_start = len(lines) - block_len

    if max_start <= 0:
        return None

    file_data = []
    attempts = 0
    max_attempts = 500
    seen = set()

    while len(file_data) < 50 and attempts < max_attempts:
        start = random.randint(0, max_start)
        if start in seen:
            attempts += 1
            continue
        seen.add(start)
        sample = build_sample(lines, start, two_owd)
        if sample is not None:
            # Check if the sample has any NaNs
            if not np.isnan(sample).any():
                file_data.append(sample)
        attempts += 1

    if file_data:
        print(f"[{fname}] Collected {len(file_data)} valid samples")
        return np.stack(file_data, axis=0)  # shape (≤50, 20, 6)
    else:
        print(f"[{fname}] Skipped (no valid samples)")
        return None

def build_dataset_rtt_50_sample(trace_dir, save_path):
    all_txt_files = [
        os.path.join(trace_dir, f) for f in os.listdir(trace_dir)
        if f.endswith(".txt")
    ]

    print(f"Found {len(all_txt_files)} .txt files. Starting parallel processing...")

    with Pool(processes=cpu_count()) as pool:
        results = pool.map(process_one_file, all_txt_files)

    real_data = []
    synthetic_data = []

    for result in results:
        if result is None:
            continue
        fname, data = result
        if "real" in fname.lower():
            real_data.append(data)
        else:
            synthetic_data.append(data)

    # Save real dataset
    if real_data:
        real_dataset = np.concatenate(real_data, axis=0)
    else:
        real_dataset = np.empty((0, 20, 6), dtype=np.float32)

    with open(f"{save_path}_real.p", "wb") as f:
        pickle.dump(real_dataset, f)
    print(f"Saved real dataset ({real_dataset.shape}) → {save_path}_real.p")

    # Save synthetic dataset
    if synthetic_data:
        synthetic_dataset = np.concatenate(synthetic_data, axis=0)
    else:
        synthetic_dataset = np.empty((0, 20, 6), dtype=np.float32)

    with open(f"{save_path}_synthetic.p", "wb") as f:
        pickle.dump(synthetic_dataset, f)
    print(f"Saved synthetic dataset ({synthetic_dataset.shape}) → {save_path}_synthetic.p")


if __name__ == "__main__":
    TRACE_DIR = "/mydata/ccbench-traces"
    OUTPUT_PATH = "/mydata/ccbench-dataset/6col-rtt-20"

    build_dataset_rtt_50_sample(TRACE_DIR, OUTPUT_PATH)