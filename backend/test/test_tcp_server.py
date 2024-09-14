#此为测试tcp服务器的模块
#---------------------------------

import socket
import threading

# 模拟客户端发送数据
def simulate_client(data, server_ip="localhost", server_port=18120):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        s.sendall(data.encode())
        response = s.recv(1024)
        print(f"Received from server: {response.decode()}")

# 创建多个客户端线程
def test_multiple_clients():
    client_data = [
        "sensor_data: temperature=22.5, humidity=60%",
        "sensor_data: temperature=21.8, humidity=58%",
        "sensor_data: temperature=23.0, humidity=62%",
        "sensor_data: temperature=20.5, humidity=55%",

    ]

    threads = []
    for data in client_data:
        t = threading.Thread(target=simulate_client, args=(data,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    test_multiple_clients()


