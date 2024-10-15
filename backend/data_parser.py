# data_parser.py - Data Parsing Module
import struct
import time
import yaml
import logging

# Load configuration file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
road_condition_mapping = config["road_condition_mapping"]
channel_to_field = config["channel_to_field"]

# Parse channel data
def parse_channel(byte_list, idx, device_channel_mapping, road_condition_mapping):
    try:
        data_len = int(byte_list[idx], 16)
        idx += 1
        error_code = byte_list[idx]
        idx += 1

        # Reverse channel index bytes
        channel_dex = int("".join(byte_list[idx:idx + 2][::-1]), 16)
        idx += 2
        data_type = byte_list[idx]
        idx += 1

        # Error handling
        if error_code != "00":
            error_code_int = int(error_code, 16)
            field_name = device_channel_mapping.get(channel_dex, f"UnknownField_{channel_dex}")
            return idx + data_len - 4, {field_name: f"errorcode{error_code_int}"}

        field_name = device_channel_mapping.get(channel_dex)
        if data_type in ["10", "11"]:
            # Simple data type
            value_dex = road_condition_mapping.get(int(byte_list[idx], 16), "Unknown")
            idx += 1
        else:
            # Floating point data type
            value_bytes = bytes.fromhex("".join(byte_list[idx:idx + 4][::-1]))
            try:
                value_dex = round(struct.unpack("!f", value_bytes)[0], 2)
            except struct.error as e:
                logging.error(f"Error unpacking float: {e}")
                value_dex = "InvalidFloat"
            idx += 4

        return idx, {field_name: value_dex}

    except Exception as e:
        logging.error(f"Error parsing channel data: {e}")
        return idx, {}

# Process UMB data
def process_umb_data(data):
    try:
        byte_list = data.split()
        idx = 12
        device_id = int(byte_list[5][0], 16)
        channel_number = int(byte_list[11], 16)

        timestamp = int(time.time() * 1000)
        parsed_data = [{"timestamp": timestamp}]

        device_channel_mapping = channel_to_field.get(device_id, {})
        
        for _ in range(channel_number):
            idx, channel_data = parse_channel(byte_list, idx, device_channel_mapping, road_condition_mapping)
            parsed_data.append(channel_data)

        return device_id, parsed_data

    except Exception as e:
        logging.error(f"Error parsing UMB data: {e}")
        return None
