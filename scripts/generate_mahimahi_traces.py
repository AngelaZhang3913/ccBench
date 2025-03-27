import numpy as np
import os

# Constants
MILLISECONDS_IN_SECOND = 1000
TRACE_DURATION_SECONDS = 60  # Duration of each trace
STABLE_PERIOD_SECONDS = 10  # Initial stable period (no bandwidth changes)
STEP_CHANGE_START_SECONDS = 17  # Bandwidth changes start at this time
STEP_CHANGE_INTERVAL_SECONDS = 7  # Bandwidth change interval
MULTIPLIERS = {0.25: "4x-d", 0.5: "2x-d", 2: "2x-u", 4: "4x-u"}  # Naming for scaling factors
MAX_BANDWIDTH_MBPS = 200  # Upper limit to prevent Mahimahi overhead
OUTPUT_DIR = "mahimahi_traces"


def convert_to_mahimahi_format(bandwidth: float, output_file: str):
    """Convert a fixed bandwidth to Mahimahi format and write to output file."""
    BYTES_PER_PKT = 1500.0
    BITS_IN_BYTE = 8.0

    with open(output_file, 'w') as mf:
        millisec_time = 0
        millisec_count = 0
        pkt_count = 0

        mbps_to_bps = bandwidth * 1e6  # Convert Mbps to bps
        bps_to_Bps = mbps_to_bps / BITS_IN_BYTE  # Convert bps to Bps
        Bps_to_pkts = bps_to_Bps / BYTES_PER_PKT  # Convert Bps to packets per sec
        pkt_per_millisec = Bps_to_pkts / MILLISECONDS_IN_SECOND  # Convert to packets per ms

        while millisec_count < TRACE_DURATION_SECONDS * MILLISECONDS_IN_SECOND:
            to_send = int(np.floor((millisec_count + 1) * pkt_per_millisec)) - pkt_count
            for _ in range(to_send):
                mf.write(str(millisec_time) + '\n')
            pkt_count += to_send
            millisec_count += 1
            millisec_time += 1


def convert_to_step_traces(initial_bw: float, base_filename: str):
    """Generate Mahimahi step traces for all feasible multipliers, starting at 17s."""
    BYTES_PER_PKT = 1500.0
    BITS_IN_BYTE = 8.0

    for multiplier, name in MULTIPLIERS.items():
        current_bw = initial_bw
        millisec_time = 0
        millisec_count = 0
        pkt_count = 0

        # Check if the multiplier is feasible (new BW must be ≤ 200 Mbps)
        if current_bw * multiplier > MAX_BANDWIDTH_MBPS:
            continue  # Skip this multiplier

        output_file = os.path.join(OUTPUT_DIR, f"{base_filename}-{name}-7s-plus-10")
        with open(output_file, 'w') as mf:
            while millisec_count < TRACE_DURATION_SECONDS * MILLISECONDS_IN_SECOND:
                # Keep stable for the first 10s
                if millisec_count >= STABLE_PERIOD_SECONDS * MILLISECONDS_IN_SECOND and \
                        (millisec_count - STABLE_PERIOD_SECONDS * MILLISECONDS_IN_SECOND) % \
                        (STEP_CHANGE_INTERVAL_SECONDS * MILLISECONDS_IN_SECOND) == 0:
                    
                    # Apply scale change but revert every 2 cycles
                    if (millisec_count // (STEP_CHANGE_INTERVAL_SECONDS * MILLISECONDS_IN_SECOND)) % 2 == 1:
                        scaled_bw = current_bw * multiplier
                        if scaled_bw <= MAX_BANDWIDTH_MBPS:
                            current_bw = scaled_bw
                    else:
                        current_bw = initial_bw  # Revert to original bandwidth

                mbps_to_bps = current_bw * 1e6  # Convert Mbps to bps
                bps_to_Bps = mbps_to_bps / BITS_IN_BYTE  # Convert bps to Bps
                Bps_to_pkts = bps_to_Bps / BYTES_PER_PKT  # Convert Bps to packets per sec
                pkt_per_millisec = Bps_to_pkts / MILLISECONDS_IN_SECOND  # Convert to packets per ms

                to_send = int(np.floor((millisec_count + 1) * pkt_per_millisec)) - pkt_count
                for _ in range(to_send):
                    mf.write(str(millisec_time) + '\n')
                pkt_count += to_send
                millisec_count += 1
                millisec_time += 1

        print(f"Generated {output_file}")


# Generate Mahimahi traces
bw_list = list(range(6, 198, 6))  # Equivalent to `seq 6 6 192`

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for bw in bw_list:
    # Generate flat trace
    base_filename = f"wired{bw}"
    output_file = os.path.join(OUTPUT_DIR, base_filename)
    convert_to_mahimahi_format(bw, output_file)
    print(f"Generated {output_file}")

    # Generate step traces for all feasible multipliers
    convert_to_step_traces(bw, base_filename)
