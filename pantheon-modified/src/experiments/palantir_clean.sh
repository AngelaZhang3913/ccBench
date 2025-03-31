
ls -trlh ../../tmp/ | awk '{print $7" "$8" "$9}' | sed "s/:/ /g" | awk '{a=($1*24+$2)*60+$3; print a" "$4}' > files
now=`date | awk '{print $3" "$4}' | sed "s/:/ /g" | awk '{print ($1*24+$2)*60+$3}'`;
cat files | awk -v now="$now" '{if($1<(now-20))print $2}' > remove-them
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
if [ -d "data" ]; then
    mkdir -p /mydata/ccbench-logs  # Ensure destination exists
    rsync -av --remove-source-files data/ /mydata/ccbench-logs/
    find data/ -type d -empty -delete  # Remove empty directories
else
    echo "Warning: 'data/' directory does not exist. Skipping rsync."
fi

# Move dataset files if they exist
if [ -d "../../third_party/tcpdatagen/dataset" ]; then
    mkdir -p /mydata/ccbench-traces  # Ensure destination exists
    mv ../../third_party/tcpdatagen/dataset/* /mydata/ccbench-traces/
else
    echo "Warning: '../../third_party/tcpdatagen/dataset/' does not exist. Skipping dataset move."
fi