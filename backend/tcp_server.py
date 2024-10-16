# tcp_server.py - TCP 数据接收模块
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from data_parser import process_umb_data
from database import store_sensor_data

# 配置日志系统
log_handler = RotatingFileHandler("./data/tcp_server.log", maxBytes=5*1024*1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)

DATA_TIMEOUT = 360  # 超时时间设置为 6 分钟

# 定义协议处理函数 - 映射协议名称到相应的解析函数
PROTOCOL_HANDLERS = {
    "UMB": process_umb_data,
    # "JSON": process_json_data,  # 示例：如果需要，可以添加 JSON 协议处理函数
}

# 处理客户端连接
async def handle_sensor_data(reader, writer):
    client_ip, client_port = writer.get_extra_info('peername')
    # 读取注册包（例如，传感器发送的初始包以识别自身）
    registration_packet = await reader.read(128)
    # 从注册包中提取站点 ID 和协议类型
    station_id = registration_packet[:6].decode("utf-8", errors="ignore")
    protocol_type = registration_packet[6:].decode("utf-8", errors="ignore").strip()
    
    if not station_id or not protocol_type:
        # 如果注册包无效，关闭连接
        writer.close()
        await writer.wait_closed()
        return

    # 根据协议类型确定正确的数据处理函数
    process_data = PROTOCOL_HANDLERS.get(protocol_type)
    if not process_data:
        # 如果协议不受支持，记录错误并关闭连接
        logging.error(f"Unsupported protocol: {protocol_type}")
        writer.close()
        await writer.wait_closed()
        return

    logging.info(f"来自 {client_ip}:{client_port} 的连接, 站点 ID: {station_id}, 协议: {protocol_type}")

    try:
        while True:
            try:
                # 接收原始字节数据，设置超时时间
                data = await asyncio.wait_for(reader.read(100), timeout=DATA_TIMEOUT)
                if not data:
                    # 如果未收到数据，客户端可能已关闭连接
                    logging.info(f"连接已由 {client_ip} 关闭")
                    break

                # 将接收到的字节数据转换为十六进制字符串列表
                byte_list = ['{:02x}'.format(byte) for byte in data]
                # 使用相应的处理函数解析数据
                vice_id, parsed_data = process_data(" ".join(byte_list))
                logging.info(f"设备 ID: {vice_id}, 数据: {parsed_data}")

                # 将解析后的数据存储到数据库中
                store_sensor_data(station_id, vice_id, parsed_data)

                # 向客户端发送确认消息
                writer.write(b"Data received")
                await writer.drain()

            except asyncio.TimeoutError:
                # 如果连接由于不活动超时，记录警告
                logging.warning(f"来自 {client_ip} 的连接因超过 {DATA_TIMEOUT / 60} 分钟无响应而超时。")
                break

    except Exception as e:
        # 记录处理数据过程中发生的任何意外错误
        logging.error(f"与客户端 {client_ip} 的连接出现错误: {e}")
    
    finally:
        # 确保连接被正确关闭
        writer.close()
        await writer.wait_closed()
        logging.info(f"与 {client_ip} 的连接已关闭。")

# 启动 TCP 服务器
async def start_tcp_server():
    try:
        # 启动 TCP 服务器，绑定到所有可用 IP 地址的 18120 端口
        server = await asyncio.start_server(handle_sensor_data, '0.0.0.0', 18120)
        logging.info("TCP 服务器已启动，监听端口 18120")
        # 无限期提供服务请求
        async with server:
            await server.serve_forever()
    except Exception as e:
        # 记录任何导致服务器无法运行的严重错误
        logging.critical(f"服务器遇到严重错误: {e}")

if __name__ == "__main__":
    # 运行 TCP 服务器
    asyncio.run(start_tcp_server())
