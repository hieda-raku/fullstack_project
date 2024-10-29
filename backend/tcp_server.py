# tcp_server.py - TCP Data Receiver Module
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from data_parser import process_umb_data
from crc_checksum import CRC16
import json
import yaml

# 配置日志系统
log_handler = RotatingFileHandler("./data/tcp_server.log", maxBytes=5*1024*1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)

DATA_TIMEOUT = 360  # 超时设置为6分钟

# 加载配置文件
def load_config():
    try:
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
            return config
    except FileNotFoundError:
        logging.critical("Configuration file not found. Please provide config.yaml.")
        raise
    except yaml.YAMLError as e:
        logging.critical(f"Error parsing configuration file: {e}")
        raise

CONFIG = load_config()
road_condition_mapping = CONFIG["road_condition_mapping"]
channel_to_field = CONFIG["channel_to_field"]

# 验证数据的CRC效验和
def validate_crc(data):
    """
    验证数据的CRC效验和。

    参数:
        data (bytes): 需要验证的数据。

    返回:
        bool: 如果CRC效验成功返回True，否则返回False。
    """
    # 提取CRC效验和
    received_crc = data[-3:-1]

    # 计算数据的CRC效验和
    calculated_crc = CRC16.calc_crc16(data[:-3]).to_bytes(2, byteorder="little")

    # 比较计算出的效验和与接收到的效验和
    return received_crc == calculated_crc

# 处理协议数据的函数定义
def process_json_data(data):
    """
    处理 JSON 格式的数据。

    参数:
        data (bytes): 接收到的字节数据。

    返回:
        dict: 解析后的数据。
    """
    try:
        json_data = json.loads(data.decode("utf-8"))
        logging.info(f"Processed JSON Data: {json_data}")
        return json_data
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON data: {e}")
        return None

# 添加协议处理函数映射表
def process_umb_data_wrapper(data):
    return process_umb_data(data, channel_to_field, road_condition_mapping)

PROTOCOL_HANDLERS = {
    "UMB": process_umb_data_wrapper,
    "JSON": process_json_data,
    # 在此处可以添加更多协议处理函数
}

# 处理客户端连接
async def handle_sensor_data(reader, writer):
    client_ip, client_port = writer.get_extra_info('peername')
    registration_packet = await reader.read(128)
    project_code = registration_packet[:2].decode("utf-8", errors="ignore")
    station_code = registration_packet[2:4].decode("utf-8", errors="ignore")
    station_number = registration_packet[4:7].decode("utf-8", errors="ignore")
    protocol_type = registration_packet[7:].decode("utf-8", errors="ignore").strip()
    
    station_id = f"{project_code}{station_code}{station_number}"
    
    if not station_id or not protocol_type:
        logging.warning(f"Invalid registration from {client_ip}, closing connection.")
        writer.close()
        await writer.wait_closed()
        return
    
    logging.info(f"连接来自 {client_ip}:{client_port}, Project Code: {project_code}, Station Code: {station_code}, Station Number: {station_number}, Protocol: {protocol_type}")

    try:
        while True:
            try:
                # 接收原始字节数据，设置超时时间
                data = await asyncio.wait_for(reader.read(1024), timeout=DATA_TIMEOUT)
                if not data:
                    logging.info(f"Connection closed by {client_ip}")
                    break

                # 通过协议类型找到对应的处理函数
                handler = PROTOCOL_HANDLERS.get(protocol_type)
                if handler:
                    if protocol_type == "UMB":
                        # CRC 校验
                        if validate_crc(data):
                            byte_list = ['{:02x}'.format(byte) for byte in data]
                            vice_id, parsed_data = handler(" ".join(byte_list))
                            logging.info(f"Device ID: {vice_id}, data: {parsed_data}")
                        else:
                            logging.warning(f"CRC validation failed for data from {client_ip}")
                    else:
                        # 处理其他协议的数据（例如 JSON）
                        parsed_data = handler(data)
                        if parsed_data:
                            logging.info(f"Received JSON Data from {client_ip}: {data.decode('utf-8')}")
                else:
                    logging.error(f"Unsupported protocol type: {protocol_type} from {client_ip}")

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
