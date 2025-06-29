import struct

def calculate_checksum(data: bytes) -> int:
    return sum(data) & 0xFFFF

def build_packet(network_id: int, card_id: int, command_code: int, payload: bytes, need_confirmation: bool = True) -> bytes:
    id_code = struct.pack('>I', network_id)
    reserved = b'\x00\x00'
    packet_type = b'\x68'
    card_type = b'\x32'
    card_id_byte = card_id.to_bytes(1, 'big')
    protocol_code = b'\x7B'
    confirm_flag = b'\x01' if need_confirmation else b'\x00'
    packed_data = command_code.to_bytes(1, 'big') + payload
    packed_length = len(packed_data).to_bytes(2, 'little')
    packet_number = b'\x00'
    last_packet_number = b'\x00'
    checksum_data = packet_type + card_type + card_id_byte + protocol_code + confirm_flag + packed_length + packet_number + last_packet_number + packed_data
    checksum = calculate_checksum(checksum_data).to_bytes(2, 'little')
    network_data_length = len(checksum_data) + 2
    network_data_length_bytes = network_data_length.to_bytes(2, 'big')
    full_packet = id_code + network_data_length_bytes + reserved + checksum_data + checksum
    return full_packet

def make_send_text_payload(window_no: int, mode: int, alignment: int, speed: int, stay_time: int, text: str) -> bytes:
    payload = bytearray()
    payload.append(window_no & 0xFF)
    payload.append(mode & 0xFF)
    payload.append(alignment & 0xFF)
    payload.append(speed & 0xFF)
    payload += stay_time.to_bytes(2, 'big')
    for char in text:
        payload.append(0x23)
        payload.append(0x00)
        payload.append(ord(char))
    return bytes(payload)
