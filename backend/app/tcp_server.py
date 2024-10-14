import asyncio
import logging
from logging.handlers import RotatingFileHandler

from data_parser import process_umb_data

# 配置日志系统
log_handler = RotatingFileHandler("../data/tcp_server.log", maxBytes=5*1024*1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)

DATA_TIMEOUT = 360  # 超时设置为6分钟

# 处理客户端连接
async def handle_sensor_data(reader, writer):
    client_ip, client_port = writer.get_extra_info('peername')
    # 读取128字节的注册包
    registration_packet = await reader.read(128)
    # 解析注册包内容
    station_id = registration_packet[:6].decode("utf-8")
    protocol_type = registration_packet[6:].decode("utf-8").strip()  # 去除可能的额外空白字符

    logging.info(f"连接来自 {client_ip}:{client_port}, Station ID: {station_id}, Protocol: {protocol_type}")

    try:
        while True:
            try:
                # 接收原始字节数据，设置超时时间
                data = await asyncio.wait_for(reader.read(100), timeout=DATA_TIMEOUT)
                if not data:
                    logging.info(f"Connection closed by {client_ip}")
                    break

                byte_list =  ['{:02x}'.format(byte) for byte in data]
                vice_id, parsed_data = process_umb_data(" ".join(byte_list))
                logging.info(f"Device ID :{vice_id},data:{parsed_data}")
                # 发送确认消息给客户端
                writer.write(b"Data received")  # 发送字节类型的响应
                await writer.drain()

            except asyncio.TimeoutError:
                logging.warning(f"Connection from {client_ip} timed out after {DATA_TIMEOUT / 60} minutes of inactivity.")
                break

    except Exception as e:
        logging.error(f"Error with client {client_ip}: {e}")
    
    finally:
        writer.close()
        await writer.wait_closed()
        logging.info(f"Connection with {client_ip} closed.")

# 启动TCP服务器
async def start_tcp_server():
    try:
        server = await asyncio.start_server(handle_sensor_data, '0.0.0.0', 18120)
        logging.info("TCP server started on port 18120")
        async with server:
            await server.serve_forever()
    except Exception as e:
        logging.critical(f"Server encountered a critical error: {e}")

if __name__ == "__main__":
    asyncio.run(start_tcp_server())
