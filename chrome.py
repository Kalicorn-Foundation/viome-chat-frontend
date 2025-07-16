import tkinter as tk
from tkinter import ttk
import asyncio
import websockets
import threading
from pynput import keyboard
import json
from datetime import datetime
import pytz
import uuid
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import subprocess
import os

INPUT_METHOD_KOREAN = 'K'
INPUT_METHOD_ENGLISH = 'E'

MAP_KEYBOARD = {
    'r': 'ㄱ', 'R': 'ㄲ', 's': 'ㄴ', 'e': 'ㄷ', 'E': 'ㄸ',
    'f': 'ㄹ', 'a': 'ㅁ', 'q': 'ㅂ', 'Q': 'ㅃ', 't': 'ㅅ',
    'T': 'ㅆ', 'd': 'ㅇ', 'w': 'ㅈ', 'W': 'ㅉ', 'c': 'ㅊ',
    'z': 'ㅋ', 'x': 'ㅌ', 'v': 'ㅍ', 'g': 'ㅎ',
    'k': 'ㅏ', 'o': 'ㅐ', 'i': 'ㅑ', 'O': 'ㅒ',
    'j': 'ㅓ', 'p': 'ㅔ', 'u': 'ㅕ', 'P': 'ㅖ',
    'h': 'ㅗ', 'y': 'ㅛ', 'n': 'ㅜ', 'b': 'ㅠ',
    'm': 'ㅡ', 'l': 'ㅣ',
}

def compose_hg_with_node(jamo_string):
    try:
        result = subprocess.run(
            ['node', 'compose_hg.js', jamo_string], creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True, text=True, timeout=5, encoding='utf-8'
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return jamo_string  # fallback to original string
    except Exception:
        return jamo_string  # fallback to original string

class TransparentWindow:
    def __init__(self, root):
        self.root = root
        self.websocket = None
        self.loop = asyncio.new_event_loop()
        self.secret = self.load_config_data()["secret"]
        self.input_method = INPUT_METHOD_ENGLISH  # Default to English
        self.has_unread_messages = False

        self.key = self.generate_key()
        self.uri = self.load_config_data()["backend"]
        
        # Initialize pynput listener
        self.listener = None

        threading.Thread(target=self.start_event_loop, daemon=True).start()

        self.setup_window()
        self.setup_hotkeys()
        self.setup_dragging()
        self.setup_widgets()
        self.setup_user()

    def load_config_data(self):
        try:
            with open("config.json", "r") as f:
                data = json.load(f)
                return data
        except Exception as e:
            self.insert_text("config.json not found.")

    def generate_key(self):
        mac = str(uuid.getnode())
        return hashlib.sha256(mac.encode()).hexdigest()[:16]

    def format_timestamp(self):
        time_zone = "Asia/Tokyo"
        format_string = "%m-%d %H:%M:%S"
        current_time = datetime.utcnow().astimezone(pytz.timezone(time_zone))
        return current_time.strftime(format_string)

    def encrypt_data(self, data):
        byte_key = self.secret.encode("utf-8")
        cipher = AES.new(byte_key, AES.MODE_ECB)
        encrypted_bytes = cipher.encrypt(pad(data.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted_bytes).decode("utf-8")

    def decrypt_data(self, data):
        byte_key = self.secret.encode("utf-8")
        encrypted_bytes = base64.b64decode(data)
        cipher = AES.new(byte_key, AES.MODE_ECB)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        return decrypted_bytes.decode("utf-8")

    def setup_window(self):
        # Set icon BEFORE overrideredirect to ensure it shows in taskbar
        self.set_normal_icon()
        
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.transparency = 0.01
        self.root.attributes("-alpha", self.transparency)
        self.root.geometry("400x120+30-80")
        self.root.title("New Tab - Google Chrome")

    def set_normal_icon(self):
        """Set the normal icon (icon1.ico)"""
        try:
            if os.path.exists("icon1.ico"):
                # For Windows, use iconbitmap with proper path
                self.root.iconbitmap("icon1.ico")
                # Force update the taskbar icon
                self.root.update_idletasks()
                # Additional Windows-specific icon update
                self._force_icon_update("icon1.ico")
            else:
                print("icon1.ico not found")
        except Exception as e:
            print(f"Could not load icon1.ico: {e}")

    def set_notification_icon(self):
        """Set the notification icon (icon2.ico)"""
        try:
            if os.path.exists("icon2.ico"):
                # For Windows, use iconbitmap with proper path
                self.root.iconbitmap("icon2.ico")
                # Force update the taskbar icon
                self.root.update_idletasks()
                # Additional Windows-specific icon update
                self._force_icon_update("icon2.ico")
            else:
                print("icon2.ico not found")
        except Exception as e:
            print(f"Could not load icon2.ico: {e}")

    def _force_icon_update(self, icon_path):
        """Force update the window icon using Windows-specific methods"""
        try:
            # Try to force a window update to refresh the icon
            self.root.update()
            # Additional method to ensure icon change is applied
            if hasattr(self.root, 'wm_iconbitmap'):
                self.root.wm_iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not force icon update: {e}")

    def mark_as_read(self):
        """Mark messages as read and reset icon"""
        self.has_unread_messages = False
        self.set_normal_icon()
        self.read_button.config(state=tk.DISABLED)  # Hide read button

    def setup_hotkeys(self):
        # Create a keyboard listener with pynput
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+z': self.toggle_visibility,
            '<ctrl>+<alt>+=': self.up_transparency,
            '<ctrl>+<alt>+-': self.down_transparency,
            '<ctrl>+<shift>+r': self.mark_as_read,
            '<alt_gr>': self.toggle_input_method,  # Right Alt key to toggle input methods
        })
        self.listener.start()

    def toggle_input_method(self):
        """Toggle between Korean and English input methods"""
        if self.input_method == INPUT_METHOD_KOREAN:
            self.switch_to_einput()
        else:
            self.switch_to_kinput()

    def switch_to_kinput(self):
        self.input_method = INPUT_METHOD_KOREAN
        self.update_input_method_label()

    def switch_to_einput(self):
        self.input_method = INPUT_METHOD_ENGLISH
        self.update_input_method_label()

    def update_input_method_label(self):
        self.input_method_label.config(text=self.input_method)

    def setup_dragging(self):
        self.root.bind("<Button-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.on_release)
        self.drag_start_x = 0
        self.drag_start_y = 0

    def setup_widgets(self):
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Text display area
        self.text_display = tk.Text(self.frame, wrap=tk.WORD, height=6, width=50)
        self.text_display.pack(fill=tk.BOTH, expand=True)
        self.text_display.config(state=tk.DISABLED)
        
        # Read button (initially disabled)
        self.read_button = tk.Button(self.frame, text="✓", width=2, command=self.mark_as_read, 
                                    state=tk.DISABLED)
        self.read_button.pack(side=tk.RIGHT, padx=0, pady=0)
        
        # Input area with method indicator
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Input method label
        self.input_method_label = tk.Label(input_frame, text=self.input_method, width=2)
        self.input_method_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Entry input
        self.entry_input = tk.Entry(input_frame, width=47)
        self.entry_input.pack(fill=tk.X, side=tk.LEFT)
        self.entry_input.bind("<Return>", self.send_data)

    def on_press(self, event):
        self.entry_input.focus_set()
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def on_drag(self, event):
        delta_x = event.x_root - self.drag_start_x
        delta_y = event.y_root - self.drag_start_y
        self.root.geometry(
            f"+{self.root.winfo_x() + delta_x}+{self.root.winfo_y() + delta_y}"
        )
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def on_release(self, event):
        pass

    def toggle_visibility(self):
        if self.root.state() == "normal":
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.entry_input.focus_set()

    def up_transparency(self):
        self.transparency += 0.01
        self.root.attributes("-alpha", self.transparency)

    def down_transparency(self):
        self.transparency -= 0.01
        self.root.attributes("-alpha", self.transparency)

    def setup_user(self):
        config = self.load_config_data()
        data = {"code": "setup", "userId": config["userId"], "data": self.key}
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(self.encrypt_data(json.dumps(data))), self.loop
            )

    def send_data(self, event):
        text = self.entry_input.get()
        if text == "clear":
            self.delete_text()
            self.entry_input.delete(0, tk.END)
        elif text == "exit":
            self.root.destroy()
        elif text == "users":
            config = self.load_config_data()
            data = {"code": "users", "userId": config["userId"], "key": self.key}
            self.entry_input.delete(0, tk.END)
            if self.websocket:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(self.encrypt_data(json.dumps(data))), self.loop
                )
        else:
            # Convert text based on input method
            if self.input_method == INPUT_METHOD_KOREAN:
                converted_text = self.convert_input(text)
            else:
                converted_text = text
            
            # Send converted text to websocket
            config = self.load_config_data()
            data = {"code": "message", "userId": config["userId"], "text": converted_text, "key": self.key}
            self.entry_input.delete(0, tk.END)
            if self.websocket:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(self.encrypt_data(json.dumps(data))), self.loop
                )

    async def websocket_handler(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    self.setup_user()
                    while True:
                        message = await websocket.recv()
                        self.root.after(
                            0,
                            self.display_message,
                            self.decrypt_data(message.encode("utf-8")),
                        )
            except (
                websockets.exceptions.ConnectionClosedError,
                ConnectionRefusedError,
            ) as e:
                self.root.after(0, self.display_message, f"Connection error: {e}")
                self.websocket = None
                await asyncio.sleep(5)  # Wait before retrying

    def display_message(self, message):
        print(message.split(" ")[1][:3], self.load_config_data()["userId"].startswith(message.split(" ")[1][:3]))
        self.insert_text(f"{message}\n")
        self.text_display.see(tk.END)
        
        # Set notification icon and enable read button for new messages
        if not self.has_unread_messages and not self.load_config_data()["userId"].startswith(message.split(" ")[1][:3]):
            self.has_unread_messages = True
            # Change icon immediately for new messages
            self.set_notification_icon()
            self.read_button.config(state=tk.NORMAL)  # Show read button
            # Force a window update to ensure icon change is visible
            self.root.after(100, self.root.update_idletasks)

    def insert_text(self, text):
        # Temporarily enable the Text widget to insert text
        self.root.deiconify()
        self.entry_input.focus_set()
        self.text_display.config(state=tk.NORMAL)
        self.text_display.insert(tk.END, text)
        self.text_display.config(state=tk.DISABLED)

    def delete_text(self):
        # Temporarily enable the Text widget to insert text
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.config(state=tk.DISABLED)

    def start_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_handler())

    def cleanup(self):
        """Clean up resources when the application is closing"""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def convert_input(self, emulated_input: str) -> str:
        jamos = []
        for ch in emulated_input:
            if ch in MAP_KEYBOARD:
                jamos.append(MAP_KEYBOARD[ch])
            else:
                jamos.append(ch)  # Keep non-mapped characters like space, punctuation
        try:
            result = compose_hg_with_node(''.join(jamos))
        except Exception:
            result = ''.join(jamos)  # fallback in case compose fails
        return result

def main():
    root = tk.Tk()
    app = TransparentWindow(root)
    
    # Set up cleanup when the window is closed
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
