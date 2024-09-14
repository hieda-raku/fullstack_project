import asyncio
import logging
from logging.handlers import RotatingFileHandler

# 配置日志系统
log_handler = RotatingFileHandler("data/tcp_server.log", maxBytes=5*1024*1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)

# 定义超时时间，假设客户端每5分钟发送一次数据，设置为6分钟的超时时间
DATA_TIMEOUT = 360  # 6分钟没有数据则关闭连接

async def handle_sensor_data(reader, writer):
    client_ip, client_port = writer.get_extra_info('peername')
    logging.info(f"Received connection from {client_ip}:{client_port}")

    try:
        while True:
            try:
                # 等待客户端发送数据，超时设定为DATA_TIMEOUT
                data = await asyncio.wait_for(reader.read(100), timeout=DATA_TIMEOUT)
                if not data:
                    logging.info(f"Connection closed by {client_ip}")
                    break

                message = data.decode().strip()
                logging.info(f"Received TCP data from {client_ip}: {message}")
                # process_sensor_data(message)

                # 发送确认消息给客户端
                writer.write(b"Data received")
                await writer.drain()

            except asyncio.TimeoutError:
                # 超时则关闭连接
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
        logging.info("TCP server started on port 8888")
        async with server:
            await server.serve_forever()
    except Exception as e:
        logging.critical(f"Server encountered a critical error: {e}")

if __name__ == "__main__":
    asyncio.run(start_tcp_server())
