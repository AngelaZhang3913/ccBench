
time=30
./system_setup.sh
./palantir_clean.sh
pids=""
sys_cpu_cnt=`lscpu | grep "^CPU(s):" | awk '{print $2}'`
cnt=0

schemes=($@)  # Read schemes assigned to this node
smaller_schemes="reno cubic vegas bbr"
test_schemes="vegas"

loss_list="0"
# bw_list="12 24 48 96 192"
test_bw_list="12"
# del_list="5 10 20 40 80"
test_del_list="5"

bw_list=`echo $(seq 6 6 192) | xargs`
del_list="2 5 10 20 25 40 50 75 80 100 150 200"
real_trace_dir="$HOME/ccBench/mahimahi_traces/real"
real_bw=30

for cc in "${schemes[@]}"
do
    for loss in $loss_list
    do
        ## Pantheon and Mahimahi have problem with links higher than 300Mbps!
        ## For now, avoid using any link BW>300Mbps. But, stay tuned! A new patch is on the way! ;)
        for bw in $bw_list
        do
            real_trace_flag="false"
            if [ $bw -gt 100 ]
            then
                cpu_num=$((sys_cpu_cnt/12))
            else
                cpu_num=$((sys_cpu_cnt/6))
            fi
            for del in $del_list
            do
                bdp=$((del*bw/6))
                for qs in $((bdp/2)) $bdp $((2*bdp)) $((4*bdp)) $((5*bdp)) $((8*bdp)) $((16*bdp))
                do
                    for dl_post in ""
                    do
                        link="$bw$dl_post"
                        # scheme [kernel based TCPs: vegas bbr reno cubic ...] [log comment] [num of flows] [num of runs] [interval bw flows] [one-way delay] [qs] [loss] [down link] [duration] [BW (Mbps)] [BW2 (Mbps)]
                        echo "./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw $real_trace_flag"
                        ./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw $real_trace_flag &
                        cnt=$((cnt+1))
                        pids="$pids $!"
                        sleep 2
                    done

                    if [ $bw -lt 50 ]
                    then
                        scales="2 4"
                    elif [ $bw -lt 100 ]
                    then
                        scales="2"
                    elif [ $bw -lt 200 ]
                    then
                        scales=""
                    else
                        scales=""
                    fi
                    for scale in $scales
                    do
                        dl_post="-${scale}x-u-7s-plus-10"
                        bw2=$((bw*scale))
                        link="$bw$dl_post"
                        echo "./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw2 $real_trace_flag"
                        ./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw2 $real_trace_flag &
                        cnt=$((cnt+1))
                        pids="$pids $!"
                        sleep 2
                    done
                    scales="2 4"
                    for scale in $scales
                    do
                        dl_post="-${scale}x-d-7s-plus-10"
                        bw2=$((bw/scale))
                        link="$bw$dl_post"
                        echo "./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw2 $real_trace_flag &"
                        ./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $link $time $bw $bw2 $real_trace_flag &
                        cnt=$((cnt+1))
                        pids="$pids $!"
                        sleep 2
                    done
                    if [ $cnt -gt $cpu_num ]
                    then
                        for pid in $pids
                        do
                            wait $pid
                        done
                        cnt=0
                        pids=""
                        ./palantir_clean.sh
                    fi
                done
            done
        done
        # Process real traces
        if [ -d "$real_trace_dir" ]; then
            cpu_num=$((sys_cpu_cnt/6))
            real_trace_flag="true"
            for trace in $(ls $real_trace_dir)
            do
                real_link="real/$trace"
                for del in $del_list
                do
                    bdp=$((del*real_bw/6))
                    for qs in $((bdp/2)) $bdp $((2*bdp)) $((4*bdp)) $((5*bdp)) $((8*bdp)) $((16*bdp))
                    do
                        echo "./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $real_link $time $real_bw $real_bw $real_trace_flag"
                        ./cc_dataset_gen_solo.sh $cc single-flow-scenario 1 1 0 $del $qs "$loss" $real_link $time $real_bw $real_bw $real_trace_flag &
                        cnt=$((cnt+1))
                        pids="$pids $!"
                        sleep 2
                        if [ $cnt -gt $cpu_num ]
                        then
                            for pid in $pids
                            do
                                wait $pid
                            done
                            cnt=0
                            pids=""
                            ./palantir_clean.sh
                        fi
                    done
                done
            done
        fi
    done
done
sleep 30
