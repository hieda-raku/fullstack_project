import asyncio

# 处理接收到的传感器数据
async def handle_sensor_data(reader, writer):
    data = await reader.read(100)  # 每次读取100字节的数据
    if data:
        message = data.decode()
        print(f"Received data: {message}")
        # 在这里调用统一的数据处理函数
        process_sensor_data(message)

        writer.write(b"Data received")
        await writer.drain()
    writer.close()

# 启动TCP服务器
async def start_tcp_server():
    server = await asyncio.start_server(handle_sensor_data, '0.0.0.0', 8888)
    async with server:
        await server.serve_forever()

asyncio.run(start_tcp_server())
