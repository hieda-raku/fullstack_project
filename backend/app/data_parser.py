import struct
import time

road_condition_mapping = {
    10: 33,  # 干
    15: 34,  # 潮
    20: 34,  # 湿
    25: 34,  # 潮
    30: 34,  # 湿
    35: 35,  # 冰
    40: 35,  # 雪
    45: 40,  # 霜
}

channel_to_field = {
    7: {
        100: "air_temperature",
        110: "dewpoint_temperature",
        200: "humidity",
        300: "atmospheric_pressure",
        401: "wind_speed",
        501: "wind_direction",
        620: "absolute_precipitation",
        625: "relative_precipitation",
        820: "rainfall_intensity",
    },
    9: {
        101: "road_surface_temperature",
        151: "freezing_point",
        601: "water_film_height",
        801: "saline_concentration",
        810: "ice_percentage",
        820: "friction",
        900: "road_condition",
    },
}

def process_umb_data(data):
    """
    处理并解析 UMB 协议的数据包，修复通道识别问题。
    """
    try:
        byte_list = data.split()
        idx = 12  # 跳过前面12个字节的头部信息
        device_id = int(byte_list[5][0], 16)
        channel_number = int(byte_list[11], 16)

        # 获取当前的时间戳（毫秒级）
        timestamp = int(time.time() * 1000)
        parsed_data = [{"timestamp": timestamp}]

        # 预先缓存通道映射表，减少多次查询
        device_channel_mapping = channel_to_field.get(device_id, {})

        # 解析每个通道的数据
        for _ in range(channel_number):
            data_len = int(byte_list[idx], 16)
            idx += 1
            error_code = byte_list[idx]
            idx += 1

            # 正确反转通道索引字节
            channel_dex = int("".join(byte_list[idx:idx + 2][::-1]), 16)
            idx += 2
            data_type = byte_list[idx]
            idx += 1

            # 如果有错误码，跳过该通道
            if error_code != "00":
                error_code_int = int(error_code, 16)
                field_name = device_channel_mapping.get(channel_dex, f"UnknownField_{channel_dex}")
                parsed_data.append({field_name: f"errorcode{error_code_int}"})
                idx += data_len - 4
                continue

            field_name = device_channel_mapping.get(channel_dex)
            if data_type in ["10", "11"]:
                # 处理简单数据类型
                value_dex = road_condition_mapping.get(int(byte_list[idx], 16), "Unknown")
                parsed_data.append({field_name: value_dex})
                idx += 1
            else:
                # 处理浮点数据类型，直接用字节反转，不使用字符串拼接
                value_bytes = bytes.fromhex("".join(byte_list[idx:idx + 4][::-1]))
                value_dex = round(struct.unpack("!f", value_bytes)[0], 2)
                parsed_data.append({field_name: value_dex})
                idx += 4

        return device_id, parsed_data

    except Exception as e:
        print(f"Error parsing UMB data: {e}")
        return None

    
