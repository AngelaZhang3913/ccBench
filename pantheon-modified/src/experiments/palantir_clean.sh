
ls -trlh ../../tmp/ | awk '{print $7" "$8" "$9}' | sed "s/:/ /g" | awk '{a=($1*24+$2)*60+$3; print a" "$4}' > files
now=`date | awk '{print $3" "$4}' | sed "s/:/ /g" | awk '{print ($1*24+$2)*60+$3}'`;
cat files | awk -v now="$now" '{if($1<(now-2))print $2}' > remove-them
for i in `cat remove-them`; do rm -f ../../tmp/$i;done
rm files remove-them

:<<"CMT"
for i in data/single-flow-scenario-*/tcpdatagen_mm_*.log;
do
    rm $i
done
for i in data/single-flow-scenario-*/*_mm_*.log;
do
    rm $i
done
CMT

# Rsync logs only if 'data/' exists

# Preserve only metadata and summary statistics; discard bulky packet logs.
if [ -d "data" ]; then
    mkdir -p /mydata/ccbench-logs

    if rsync -avm --remove-source-files \
        --include='*/' \
        --include='pantheon_metadata.json' \
        --include='*_stats_run*.log' \
        --exclude='*' \
        data/ /mydata/ccbench-logs/
    then
        # These remaining files are the bulky datalink, acklink, and mm logs.
        find data/ -type f -delete
        find data/ -depth -type d -empty -delete
    else
        echo "Error: failed to preserve metadata and statistics."
        exit 1
    fi
else
    echo "Warning: 'data/' directory does not exist. Skipping cleanup."
fi

# Move dataset files if they exist
if [ -d "../../third_party/tcpdatagen/dataset" ] && [ "$(ls -A ../../third_party/tcpdatagen/dataset)" ]; then
    mkdir -p /mydata/ccbench-traces  # Ensure destination exists
    mv ../../third_party/tcpdatagen/dataset/* /mydata/ccbench-traces/
else
    echo "Warning: '../../third_party/tcpdatagen/dataset/' does not exist. Skipping dataset move."
fi
