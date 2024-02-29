import argparse
import os
import sys
import time
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
import serial
from serial.tools import list_ports
from tqdm import tqdm

def convert_svg_to_gcode(svg_filename, gcode_filename):
    gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)
    curves = parse_file(svg_filename)
    gcode_compiler.append_curves(curves)
    gcode_compiler.compile_to_file(gcode_filename, passes=2)

def send_gcode_via_serial(gcode_filename, port, baudrate):
    try:
        f = open(gcode_filename, 'r')
        codes = [code for code in f]
        f.close()
        print(f"Код в файл {gcode_filename} был успешно загружен.")
    except:
        print(f"Программа не может открыть {gcode_filename}.")
        sys.exit()

    try:
        s = serial.Serial(port, baudrate)
        print(f"Порт {port} был успешно подключен.")
    except:
        print(f"Программа не может установить подключение к: {port}. Пожалуйста, проверьте порт.")
        print(f"Порт занят другой программой или скорость передачи данных (baud rate) неверна.")
        sys.exit()

    print("Трансляция кода на станок.")
    s.write(b"\r\n\r\n")  
    time.sleep(1)
    s.reset_input_buffer()

    tqdm4codes = tqdm(codes, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', unit=" codes", ncols=130)
    for code in tqdm4codes:
        tqdm4codes.set_postfix(gcode=code)  
        if code.strip().startswith(';') or code.isspace() or len(code) <= 0:
            continue
        else:
            s.write((code + '\n').encode())
            while True:  
                if s.readline().startswith(b'ok'):
                    break
    s.close()
    print()
    print("Весь код был успешно отправлен.")
    print("Примите поздравления!!!")

def main():
    parser = argparse.ArgumentParser(
        prog="CS",
        description="Удобная программа для конвертирования и отправки кода через COM порт на различные машины."
    )

    parser.add_argument("filename", help="svg файл необходимый для конвертации и трансляции")
    parser.add_argument("-p", "--port", default=None, help="порт соединения", metavar="port name")
    parser.add_argument("-b", "--baudrate", default=115200, type=int, help="baudrate (скорость передачи данных), по умолчанию 115200", metavar="baud rate")

    args = parser.parse_args()

    if os.path.exists(args.filename): 
        if os.path.isfile(args.filename): 
            if args.filename.strip().lower().endswith(".svg"):
                pass
            else:
                print(f"{args.filename} не является svg файлом (end with .svg). Проверьте импортируемый файл.")
                sys.exit()
        else:
            print(f"{args.filename} не является файлом. Пожалуйста, проверьте импортируемые данные.")
            sys.exit()
    else:
        print(f"{args.filename} не существует. Пожалуйста, проверьте импортируемые данные.")
        sys.exit()

    gcode_filename = os.path.splitext(args.filename)[0] + ".gcode"
    convert_svg_to_gcode(args.filename, gcode_filename)

    if args.port is None:
        ports = [p.device for p in list_ports.comports()]
        if len(ports) == 1:
            args.port = ports[0]
        else:
            print("Существует более одного свободного порта. Пожалуйста, выберите желаемый порт.")
            print("Свободные порты:")
            for p in list_ports.comports():
                print(p.device)
            sys.exit()

    send_gcode_via_serial(gcode_filename, args.port, args.baudrate)

if __name__ == "__main__":
    main()
