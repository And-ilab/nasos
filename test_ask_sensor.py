from pymodbus.client import ModbusSerialClient
import time


def modbus_master_test():
    client = ModbusSerialClient(
        port='COM1',
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )

    if client.connect():
        print("✓ Успешное подключение к COM1")
        while True:
            try:
                result = client.read_holding_registers(
                    address=0,
                    count=10,
                )

                if not result.isError():
                    print(f"✓ Успешный ответ: {result.registers}")
                else:
                    print(f"✗ Ошибка Modbus")

            except Exception as e:
                print(f"✗ Ошибка связи: {e}")

            time.sleep(2)

    else:
        print("✗ Не удалось подключиться к COM1")

    client.close()


if name == "main":
    modbus_master_test()