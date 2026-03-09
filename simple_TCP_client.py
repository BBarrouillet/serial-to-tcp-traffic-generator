# Simple TCP Client
#
# Connects to a TCP server, displays received data,
# and can send packets of random data.
#
# Copyright (c) 2016-2018 4RF
#
# This file is subject to the terms and conditions of the GNU General Public
# License Version 3.  See the file "LICENSE" in the main directory of this
# archive for more details.

import socket
import random
import threading
import configparser
import os
import sys
import time

from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext


class SimpleTCPClient:
    def __init__(self):
        self.tcp_socket = None
        self.receive_thread = None
        self.connected = False
        self.stop_threads = False

        # Load config
        config = configparser.ConfigParser()
        config.read('simple_TCP_client.ini')
        if 'config' in config:
            confsection = config['config']
        else:
            confsection = None

        top = Tk()
        top.geometry("550x500")
        top.title("Simple TCP Client")

        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        try:
            top.iconbitmap(os.path.join(base_path, 'serialtrafficgenerator.ico'))
        except:
            pass

        top.columnconfigure(0, weight=0)
        top.columnconfigure(1, weight=1)

        currentrow = 0

        # --- TCP Host ---
        Label(top, text="TCP Host").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        self.tcp_host = StringVar()
        self.tcp_host.set("192.168.1.100")
        if confsection:
            self.tcp_host.set(confsection.get('tcp_host', '192.168.1.100'))
        Entry(top, textvariable=self.tcp_host).grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        # --- TCP Port ---
        Label(top, text="TCP Port").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        self.tcp_port = IntVar()
        self.tcp_port.set(5000)
        if confsection:
            self.tcp_port.set(int(confsection.get('tcp_port', '5000')))
        Entry(top, textvariable=self.tcp_port).grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        # --- Display format ---
        Label(top, text="Display As").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        self.display_format = StringVar()
        self.display_format.set("Hex")
        if confsection:
            self.display_format.set(confsection.get('display_format', 'Hex'))
        combo = ttk.Combobox(top, textvariable=self.display_format, state='readonly')
        combo['values'] = ("Hex", "ASCII", "Both")
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        # --- Packet Size for sending ---
        Label(top, text="Send Packet Size\n(bytes)").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        self.packet_size = IntVar()
        self.packet_size.set(64)
        if confsection:
            self.packet_size.set(int(confsection.get('packet_size', '64')))
        Entry(top, textvariable=self.packet_size, width=10).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        # --- Buttons row ---
        btn_frame = Frame(top)
        btn_frame.grid(row=currentrow, column=0, columnspan=2, pady=5)

        self.connect_button = Button(btn_frame, text="Connect", bd=4, width=12,
                                     command=self.connect_click)
        self.connect_button.pack(side=LEFT, padx=5)

        self.send_button = Button(btn_frame, text="Send Random", bd=4, width=14,
                                  command=self.send_random_click, state=DISABLED)
        self.send_button.pack(side=LEFT, padx=5)

        self.clear_button = Button(btn_frame, text="Clear", bd=4, width=8,
                                   command=self.clear_click)
        self.clear_button.pack(side=LEFT, padx=5)
        currentrow += 1

        # --- Status label ---
        self.status_var = StringVar()
        self.status_var.set("Disconnected")
        Label(top, textvariable=self.status_var, fg="red", font=("Arial", 9, "bold")).grid(
            row=currentrow, column=0, columnspan=2, pady=2)
        currentrow += 1

        # --- Result box ---
        self.result_box = scrolledtext.ScrolledText(top, wrap="word", font=("Consolas", 9))
        self.result_box.grid(row=currentrow, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        top.rowconfigure(currentrow, weight=1)

        self.tktop = top
        top.protocol("WM_DELETE_WINDOW", self.on_closing)

    def save_config(self):
        config = configparser.ConfigParser()
        config['config'] = {
            'tcp_host': self.tcp_host.get(),
            'tcp_port': self.tcp_port.get(),
            'display_format': self.display_format.get(),
            'packet_size': self.packet_size.get(),
        }
        with open('simple_TCP_client.ini', 'w') as configfile:
            config.write(configfile)

    def connect_click(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        host = self.tcp_host.get()
        port = self.tcp_port.get()
        self.save_config()

        self.log(f"Connecting to {host}:{port}...\n")

        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(5)
            self.tcp_socket.connect((host, port))
            self.tcp_socket.settimeout(None)
        except Exception as e:
            self.log(f"Connection failed: {e}\n")
            self.tcp_socket = None
            return

        self.connected = True
        self.stop_threads = False
        self.connect_button.config(text="Disconnect")
        self.send_button.config(state=NORMAL)
        self.status_var.set(f"Connected to {host}:{port}")
        self.tktop.nametowidget(self.status_var._name if hasattr(self.status_var, '_name') else '').config(fg="green")
        # Update status label color
        for widget in self.tktop.winfo_children():
            if isinstance(widget, Label):
                try:
                    if widget.cget('textvariable') == str(self.status_var):
                        widget.config(fg="green")
                except:
                    pass

        self.log(f"Connected.\n")

        # Start receive thread
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()

    def disconnect(self):
        self.stop_threads = True
        self.connected = False

        if self.tcp_socket:
            try:
                self.tcp_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None

        self.connect_button.config(text="Connect")
        self.send_button.config(state=DISABLED)
        self.status_var.set("Disconnected")
        for widget in self.tktop.winfo_children():
            if isinstance(widget, Label):
                try:
                    if widget.cget('textvariable') == str(self.status_var):
                        widget.config(fg="red")
                except:
                    pass

        self.log("Disconnected.\n")

    def receive_loop(self):
        """Background thread that reads from the TCP socket and displays received data."""
        while not self.stop_threads and self.connected:
            try:
                data = self.tcp_socket.recv(4096)
                if not data:
                    # Server closed the connection
                    self.tktop.after(0, self._handle_server_disconnect)
                    return
                self.tktop.after(0, self.display_received, data)
            except socket.timeout:
                continue
            except OSError:
                # Socket was closed
                if not self.stop_threads:
                    self.tktop.after(0, self._handle_server_disconnect)
                return

    def _handle_server_disconnect(self):
        self.log("Server closed the connection.\n")
        self.disconnect()

    def display_received(self, data):
        fmt = self.display_format.get()
        timestamp = time.strftime("%H:%M:%S")
        length = len(data)

        self.log(f"[{timestamp}] RX ({length} bytes): ")

        if fmt == "Hex":
            self.log(data.hex(' ') + "\n")
        elif fmt == "ASCII":
            text = data.decode('ascii', errors='replace')
            self.log(text + "\n")
        else:  # Both
            self.log(data.hex(' ') + "\n")
            text = data.decode('ascii', errors='replace')
            self.log(f"           ASCII: {text}\n")

    def send_random_click(self):
        if not self.connected or not self.tcp_socket:
            return

        size = self.packet_size.get()
        if size < 1:
            self.log("Packet size must be at least 1 byte.\n")
            return

        data = bytes(random.randint(0, 255) for _ in range(size))

        try:
            self.tcp_socket.sendall(data)
            timestamp = time.strftime("%H:%M:%S")
            self.log(f"[{timestamp}] TX ({size} bytes): {data.hex(' ')}\n")
        except Exception as e:
            self.log(f"Send failed: {e}\n")
            self.disconnect()

    def clear_click(self):
        self.result_box.delete('1.0', END)

    def log(self, text):
        self.result_box.insert(END, text)
        self.result_box.see(END)

    def on_closing(self):
        if self.connected:
            self.disconnect()
        self.tktop.destroy()

    def run(self):
        self.tktop.mainloop()


if __name__ == "__main__":
    app = SimpleTCPClient()
    app.run()
