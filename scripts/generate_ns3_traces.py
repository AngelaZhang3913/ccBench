"""
Generate network traces in NS3 format.

NS3 format: Each line contains "timestamp bandwidth" where timestamp is in ms and bandwidth is in bps.
"""

import numpy as np
import os

# Constants
MILLISECONDS_IN_SECOND = 1000
TRACE_DURATION_SECONDS = 60  # Duration of each trace
STABLE_PERIOD_SECONDS = 10  # Initial stable period (no bandwidth changes)
STEP_CHANGE_START_SECONDS = 17  # Bandwidth changes start at this time
STEP_CHANGE_INTERVAL_SECONDS = 7  # Bandwidth change interval
MULTIPLIERS = {0.25: "4x-d", 0.5: "2x-d", 2: "2x-u", 4: "4x-u"}  # Naming for scaling factors
MAX_BANDWIDTH_MBPS = 200  # Upper limit to prevent overhead
OUTPUT_DIR = "ns3_traces"


def convert_to_ns3_format(bandwidth: float, output_file: str):
    """Convert a fixed bandwidth to NS3 format and write to output file."""
    with open(output_file, 'w') as nf:
        bps = int(bandwidth * 1e6)  # Convert Mbps to bps
        for millisec_time in range(0, TRACE_DURATION_SECONDS * MILLISECONDS_IN_SECOND, MILLISECONDS_IN_SECOND):
            nf.write(f"{millisec_time} {bps}\n")


def convert_to_ns3_step_traces(initial_bw: float, base_filename: str):
    """Generate NS3 step traces for all feasible multipliers, starting at 17s."""
    for multiplier, name in MULTIPLIERS.items():
        current_bw = initial_bw

        # Check if the multiplier is feasible (new BW must be ≤ 200 Mbps)
        if current_bw * multiplier > MAX_BANDWIDTH_MBPS:
            continue  # Skip this multiplier

        output_file = os.path.join(OUTPUT_DIR, f"{base_filename}-{name}-7s-plus-10")
        with open(output_file, 'w') as nf:
            for second in range(TRACE_DURATION_SECONDS):
                millisec_time = second * MILLISECONDS_IN_SECOND
                
                # Keep stable for the first 10s
                if second >= STABLE_PERIOD_SECONDS:
                    # Calculate which step change cycle we're in
                    seconds_since_changes_started = second - STABLE_PERIOD_SECONDS
                    cycle_number = seconds_since_changes_started // STEP_CHANGE_INTERVAL_SECONDS
                    
                    # Apply scale change but revert every 2 cycles
                    if cycle_number % 2 == 1:
                        scaled_bw = initial_bw * multiplier
                        if scaled_bw <= MAX_BANDWIDTH_MBPS:
                            current_bw = scaled_bw
                        else:
                            current_bw = initial_bw
                    else:
                        current_bw = initial_bw  # Revert to original bandwidth

                bps = int(current_bw * 1e6)  # Convert Mbps to bps
                nf.write(f"{millisec_time} {bps}\n")

        print(f"Generated NS3 trace: {output_file}")


# Generate NS3 traces
bw_list = list(range(6, 198, 6))  # Equivalent to `seq 6 6 192`

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for bw in bw_list:
    # Generate flat trace
    base_filename = f"wired{bw}"
    
    # NS3 flat trace
    ns3_output_file = os.path.join(OUTPUT_DIR, base_filename)
    convert_to_ns3_format(bw, ns3_output_file)
    print(f"Generated NS3 trace: {ns3_output_file}")

    # Generate step traces for all feasible multipliers
    convert_to_ns3_step_traces(bw, base_filename)

print(f"All NS3 traces generated in {OUTPUT_DIR} directory")
