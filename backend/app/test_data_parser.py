from data_parser import process_umb_data
def test_process_umb_data():
    # 提供的示例数据
    umb_raw_data = b'\x01\x10\x01\xf0\x01\x901\x02/\x11\x00\x07\x08\x00e\x00\x16S\x06\x05B\x03U\x97\x00\x08\x00Y\x02\x16\x00\x00\x00\x00\x03U!\x03\x03U*\x03\x08\x004\x03\x16\x85\xebQ?\x05\x00\x84\x03\x10\n\x03M\xcd\x04'
    
    # 将二进制数据转换为十六进制字符串列表，模拟真实的 UMB 数据格式
    byte_list = ['{:02x}'.format(byte) for byte in umb_raw_data]
    
    # 调用解析函数
    device_id, parsed_data = process_umb_data(" ".join(byte_list))
    
    # 打印测试结果
    print(f"Device ID: {device_id}")
    print("Parsed Data:")
    for data in parsed_data:
        print(data)

# 运行测试
test_process_umb_data()
