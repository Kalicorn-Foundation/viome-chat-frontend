import pytest
import json
import os
from unittest.mock import MagicMock, patch
from chrome import TransparentWindow, compose_hg_with_node, MAP_KEYBOARD, INPUT_METHOD_KOREAN, INPUT_METHOD_ENGLISH

class DummyRoot:
    def overrideredirect(self, *a, **kw): pass
    def attributes(self, *a, **kw): pass
    def geometry(self, *a, **kw): pass
    def title(self, *a, **kw): pass
    def iconbitmap(self, *a, **kw): pass
    def update_idletasks(self): pass
    def update(self): pass
    def wm_iconbitmap(self, *a, **kw): pass
    def bind(self, *a, **kw): pass
    def state(self): return "normal"
    def withdraw(self): pass
    def deiconify(self): pass
    def winfo_x(self): return 0
    def winfo_y(self): return 0

@pytest.fixture(scope="module", autouse=True)
def setup_config():
    config = {"userId": "test", "backend": "ws://localhost", "secret": "a"*16}
    with open("config.json", "w") as f:
        json.dump(config, f)
    yield
    os.remove("config.json")

@pytest.fixture
def window():
    # Patch tkinter widgets to avoid GUI errors
    with patch("tkinter.ttk.Frame", MagicMock()), \
         patch("tkinter.Text", MagicMock()), \
         patch("tkinter.Button", MagicMock()), \
         patch("tkinter.Label", MagicMock()), \
         patch("tkinter.Entry", MagicMock()):
        win = TransparentWindow(DummyRoot())
        # Patch widget attributes for label and entry
        win.input_method_label = MagicMock()
        win.read_button = MagicMock()
        win.text_display = MagicMock()
        win.entry_input = MagicMock()
        return win

def test_generate_key(window):
    key = window.generate_key()
    assert len(key) == 16

def test_encrypt_decrypt(window):
    data = "hello world"
    encrypted = window.encrypt_data(data)
    decrypted = window.decrypt_data(encrypted)
    assert decrypted == data

def test_format_timestamp(window):
    ts = window.format_timestamp()
    assert len(ts) == 14  # MM-DD HH:MM:SS
    assert ts[2] == '-' and ts[5] == ' '

def test_input_method_switch(window):
    window.input_method = INPUT_METHOD_ENGLISH
    window.switch_to_kinput()
    assert window.input_method == INPUT_METHOD_KOREAN
    window.switch_to_einput()
    assert window.input_method == INPUT_METHOD_ENGLISH

def test_toggle_input_method(window):
    window.input_method = INPUT_METHOD_ENGLISH
    window.toggle_input_method()
    assert window.input_method == INPUT_METHOD_KOREAN
    window.toggle_input_method()
    assert window.input_method == INPUT_METHOD_ENGLISH

def test_compose_hg_with_node_fallback():
    # Should fallback to original string if node is not available
    result = compose_hg_with_node("test")
    assert isinstance(result, str)

def test_convert_input(window):
    # Test with a simple English string
    result = window.convert_input("hello")
    assert isinstance(result, str)
    # Test with a string containing mapped keys
    mapped = ''.join(MAP_KEYBOARD.keys())
    result2 = window.convert_input(mapped)
    assert isinstance(result2, str)

def test_mark_as_read(window):
    window.has_unread_messages = True
    window.read_button = MagicMock()
    window.mark_as_read()
    assert not window.has_unread_messages
    window.read_button.config.assert_called_with(state='disabled')

def test_update_input_method_label(window):
    window.input_method_label = MagicMock()
    window.input_method = "X"
    window.update_input_method_label()
    window.input_method_label.config.assert_called_with(text="X")

def test_insert_and_delete_text(window):
    window.text_display = MagicMock()
    window.insert_text("test")
    # Check that config was called with state='normal' and state='disabled'
    calls = [call.kwargs for call in window.text_display.config.call_args_list]
    assert any(c.get('state') == 'normal' for c in calls)
    assert any(c.get('state') == 'disabled' for c in calls)
    window.text_display.insert.assert_called()
    window.delete_text()
    window.text_display.delete.assert_called()

def test_set_normal_icon_and_notification_icon(window):
    # Should not raise even if icon files are missing
    window.set_normal_icon()
    window.set_notification_icon()

def test_force_icon_update(window):
    window._force_icon_update("icon1.ico") 