from Modbus_TCP import *
import time
import csv


def calculate_current(field):
    return field * 0.35


class MIRageNDIO(object):
    def __init__(self):
        self.connectionStatus = False
        self.client = None
        self.__field_x = []
        self.__field_y = []
        self.__field_z = []
        self.__current_x = []
        self.__current_y = []
        self.__current_z = []

    Relay = ModbusTCP()

    def set_axis(self, path='', axis='x'):
        with open(path, "r") as f_obj:
            reader = csv.DictReader(f_obj, delimiter=';')
            current_list = []
            field_list = []
            for row in reader:
                current_list.append(float((row["Current"]).replace(",", ".")))
                field_list.append(float((row["Field"]).replace(",", ".")))
            f_obj.close()
        if axis == 'x':
            self.__current_x = current_list
            self.__field_x = field_list
            return self.__current_x, self.__field_x, axis
        elif axis == 'y':
            self.__current_y = current_list
            self.__field_y = field_list
            return self.__current_y, self.__field_y, axis
        elif axis == 'z':
            self.__current_z = current_list
            self.__field_z = field_list
            return self.__current_z, self.__field_z, axis
        else:
            return False

    def get_current_list(self, axis='x'):
        if axis == 'x':
            return self.__current_x
        elif axis == 'y':
            return self.__current_y
        elif axis == 'z':
            return self.__current_z
        else:
            return False

    def get_field_list(self, axis='x'):
        if axis == 'x':
            return self.__field_x
        elif axis == 'y':
            return self.__field_y
        elif axis == 'z':
            return self.__field_z
        else:
            return False

    def connect(self, ip, port):
        return self.Relay.connect(ip=ip, port=port)

    def positive_channel(self, ch):
        if ch == 1:
            self.Relay.write_mult_reg(0x3E8 + 17 - 1, [0x00])
            self.Relay.write_mult_reg(0x3E8 + 18 - 1, [0x00])
        elif ch == 2:
            self.Relay.write_mult_reg(0x3E8 + 19 - 1, [0x00])
            self.Relay.write_mult_reg(0x3E8 + 20 - 1, [0x00])
        elif ch == 3:
            self.Relay.write_mult_reg(0x3E8 + 21 - 1, [0x00])
            self.Relay.write_mult_reg(0x3E8 + 22 - 1, [0x00])
        return False

    def negative_channel(self, ch):
        if ch == 1:
            self.Relay.write_mult_reg(0x3E8 + 17 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 18 - 1, [0x01])
        elif ch == 2:
            self.Relay.write_mult_reg(0x3E8 + 19 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 20 - 1, [0x01])
        elif ch == 3:
            self.Relay.write_mult_reg(0x3E8 + 21 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 22 - 1, [0x01])
        return False

    def zero_channel(self, ch):
        if ch == 1:
            self.Relay.write_mult_reg(0x3E8 + 17 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 18 - 1, [0x00])
        elif ch == 2:
            self.Relay.write_mult_reg(0x3E8 + 19 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 20 - 1, [0x00])
        elif ch == 3:
            self.Relay.write_mult_reg(0x3E8 + 21 - 1, [0x01])
            self.Relay.write_mult_reg(0x3E8 + 22 - 1, [0x00])
        return False

    def turn_on_channels(self, channels):
        for i in channels:
            self.Relay.write_mult_reg(0x3E8 + i - 1, [0x01])

    def turn_off_channels(self, channels):
        for i in channels:
            self.Relay.write_mult_reg(0x3E8 + i - 1, [0x00])


def send_write_cmd(cmd):
    if cmd:
        print("write ok")
    else:
        print("write error")


if __name__ == "__main__":

    client = MIRageNDIO()
    current_, field_, axis_ = client.set_axis("table_x.csv", axis='x')
    print("current_" + axis_ + ": " + str(current_))
    print("field_" + axis_ + ": " + str(field_))

    client.connect(ip="10.6.1.101", port='502')
    client.turn_off_channels([17, 18, 19, 20, 21, 22])
    while True:
        for i_ in range(1, 4):
            client.negative_channel(i_)
            time.sleep(2)
            client.positive_channel(i_)
            time.sleep(2)
            client.zero_channel(i_)
            time.sleep(2)
