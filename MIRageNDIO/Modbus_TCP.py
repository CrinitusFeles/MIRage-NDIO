import socket
import struct
import random
import select


class ModbusTCP(object):
    def __init__(self):
        self.__sock = None
        self.__connectionStatus = False
        self.__unit_id = 1
        self.__exchange_id = 0
        self.__debug = 0
        self.__timeout = 2

    def __log_print(self, text):
        if self.__debug:
            print(text)

    def connect(self, ip='', port=""):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.settimeout(self.__timeout)
        print("trying to connect to " + str(ip) + " : %d" % int(port))
        try:
            self.__sock.connect((ip, int(port)))
        except socket.error as exc:
            print('Caught exception socket.error : %s' % exc)
            self.__connectionStatus = False
            return False
        else:
            print('connected to server ' + ip + ':' + str(port))
            self.__connectionStatus = True
            return True

    def disconnect(self):
        self.__sock.close()
        print('disconnected')

    def _mbus_frame(self, cmd, data):
        # build frame protocol data unit
        pdu = struct.pack('B', cmd) + data

        # build frame ModBus Application Protocol header (mbap)
        self.__exchange_id = random.randint(0, 65535)
        protocol_id = 0
        length = len(pdu) + 1
        mpab = struct.pack('>HHHB', self.__exchange_id, protocol_id, length, self.__unit_id)
        return mpab + pdu

    def _recv_all(self, size):
        """Receive data over current socket, loop until all bytes is receive (avoid TCP frag)

        :param size: number of bytes to receive
        :type size: int
        :returns: receive data or None if error
        :rtype: str (Python2) or class bytes (Python3) or None
        """
        r_buffer = bytes()
        while len(r_buffer) < size:
            r_packet = self.__sock.recv(size - len(r_buffer))
            if not r_packet:
                return None
            r_buffer += r_packet

        return r_buffer

    def _recv_mbus(self):
        """Receive a modbus frame

        :returns: modbus frame body or None if error
        :rtype: str (Python2) or class bytes (Python3) or None
        """
        # 7 bytes header (mbap)
        rx_buffer = self._recv_all(7)
        # check recv
        if not (rx_buffer and len(rx_buffer) == 7):
            self.__log_print('_recv MBAP error')
            self.__log_print(rx_buffer)
            return None
        rx_frame = rx_buffer
        # decode header
        (rx_exchange_id, rx_protocol_id,
         rx_length, rx_unit_id) = struct.unpack('>HHHB', rx_frame)
        self.__log_print((rx_exchange_id, rx_protocol_id, rx_length, rx_unit_id))
        # check header
        if not ((rx_exchange_id == self.__exchange_id) and
                (rx_protocol_id == 0) and
                (rx_length < 256) and
                (rx_unit_id == self.__unit_id)):
            self.__log_print('MBAP format error')
            return None
        # end of frame
        rx_buffer = self._recv_all(rx_length - 1)
        if not (rx_buffer and
                (len(rx_buffer) == rx_length - 1) and
                (len(rx_buffer) >= 2)):
            self.__log_print('_recv frame body error')
            return None
        rx_frame += rx_buffer

        rx_bd_fc = struct.unpack('B', rx_buffer[0:1])[0]
        f_body = rx_buffer[1:]
        return rx_bd_fc, f_body

    def send_frame(self, frame):
        self.__sock.send(frame)
        cmd, data = self._recv_mbus()

        data_length = int(data[0])
        self.__log_print("data " + str(data))
        data_array = [int(c) for c in bytearray(data)][1:]
        self.__log_print("received: \n" + "cmd: " + str(cmd) + " \nbyte data:" +
                         str(data_array) + "\nbyte count: " + str(data_length))
        return cmd, data_length, data

    def read_mult_reg(self, reg_addr, reg_num=1):
        frame = self._mbus_frame(0x3, struct.pack('>HH', reg_addr, reg_num))
        cmd, data_length, data_array = self.send_frame(frame)
        registers = []
        # fill registers list with register items
        for i in range(reg_num):
            registers.append(struct.unpack('>H', data_array[i * 2 + 1:i * 2 + 3]))
        return [int(i[0]) for i in registers]

    def write_mult_reg(self, reg_addr, data):
        regs_nb = len(data)
        # check params
        if not (0x0000 <= int(reg_addr) <= 0xffff):
            self.__log_print('write_multiple_registers(): regs_addr out of range')
            return None
        if not (0x0001 <= int(regs_nb) <= 0x007b):
            self.__log_print('write_multiple_registers(): number of registers out of range')
            return None
        if (int(reg_addr) + int(regs_nb)) > 0x10000:
            self.__log_print('write_multiple_registers(): write after ad 65535')
            return None
        # build frame
        # format reg value string
        regs_val_str = b""
        for reg in data:
            # check current register value
            if not (0 <= int(reg) <= 0xffff):
                self.__log_print('write_multiple_registers(): regs_value out of range')
                return None
            # pack register for build frame
            regs_val_str += struct.pack('>H', reg)
        bytes_nb = len(regs_val_str)
        # format modbus frame body
        body = struct.pack('>HHB', reg_addr, regs_nb, bytes_nb) + regs_val_str
        tx_buffer = self._mbus_frame(0x10, body)
        # send request
        s_send = self.send_frame(tx_buffer)
        # check error
        if not s_send:
            return None
        # receive
        # f_body = [bytes([c]) for c in bytearray(s_send[2])]
        f_body = s_send[2]
        # check error
        if not f_body:
            return None
        # check fix frame size
        if len(f_body) != 4:
            self.__log_print('write_multiple_registers(): rx frame size error')
            return None
        # register extract
        (rx_reg_addr, rx_reg_nb) = struct.unpack('>HH', f_body[:4])
        # check regs write
        is_ok = (rx_reg_addr == reg_addr)
        return True if is_ok else None

    def debug(self, mode=False):
        self.__debug = mode


if __name__ == "__main__":
    client = ModbusTCP()
    client.connect(ip="10.6.1.101", port="502")
    print("RX: " + str(client.read_mult_reg(0x450, 24)))
    if client.write_mult_reg(0x3E8, [0x00 for i in range(22)]):
        print("ok")
