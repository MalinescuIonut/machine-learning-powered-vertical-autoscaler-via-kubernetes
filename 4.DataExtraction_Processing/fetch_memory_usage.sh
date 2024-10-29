#!/bin/sh
end=$(date -u '+%s')
start=$(date -u -d "15 minutes ago" '+%s')

# Define the Prometheus server URL and API endpoint
prometheus_url='http://10.8.8.188:31628/api/v1/query_range'

# Define the query to fetch memory usage metrics for the specified pod and namespace
query='sum(container_memory_usage_bytes{namespace="stress-test", pod=~"stress-testing-deployment-.*"}) by (pod)'

# Fetch the memory usage metrics from Prometheus and save to output file
curl -G "$prometheus_url" \
     --data-urlencode "query=$query" \
     --data-urlencode "start=${start}" \
     --data-urlencode "end=${end}" \
     --data-urlencode 'step=20s' -o output-metrics.json

exit 0
