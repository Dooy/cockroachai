source ./mitm/bin/activate
nohup mitmdump --set listen_host=0.0.0.0 -p 8080 --set block_global=false --set flow_detail=0 --proxyauth suno:Aa112211  > /dev/null 2>&1 &