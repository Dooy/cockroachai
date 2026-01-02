import json
from mitmproxy import http, tls

def tls_clienthello(data: tls.ClientHelloData):
    """
    实现 --ignore-hosts 效果：
    如果 SNI 域名不是 studio-api.prod.suno.com，则直接透传 TCP 流，不进行 TLS 握手。
    """
    server_name = data.context.client_hello.server_name
    if server_name != "studio-api.prod.suno.com":
        data.ignore_connection = True

def request(flow: http.HTTPFlow):
    # 逻辑 1: Mock 返回指定接口
    if flow.request.method == "POST" and "studio-api.prod.suno.com/api/c/check" in flow.request.url:
        response_data = {"required": True, "f": 2028}
        flow.response = http.Response.make(
            200,
            json.dumps(response_data),
            {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        return  # 既然已经 Mock 返回了，就不再走后面的转发逻辑

    # 逻辑 2: 转发特定请求到另一个服务器
    if flow.request.method == "POST" and "studio-api.prod.suno.com/api/generate/v2-web/" in flow.request.url:
        # 修改目标地址
        flow.request.url = "https://hc.open-hk.com/test/proxyman/push"
        # 如果目标服务器需要正确的 Host 头，可以取消下面这一行的注释
        # flow.request.host = "hc.open-hk.com"