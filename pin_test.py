import serial
import time

PORT = "COM3"  # Change to your serial port
BAUD = 115200

port = serial.Serial(PORT, BAUD, timeout=1)

print(f"Reading input pins on {PORT} — press Ctrl+C to stop\n")
print(f"{'CTS':<8} {'DSR':<8} {'CD':<8} {'RI':<8}")
print("-" * 32)

try:
    while True:
        print(f"{port.getCTS()!s:<8} {port.getDSR()!s:<8} {port.getCD()!s:<8} {port.getRI()!s:<8}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    port.close()
