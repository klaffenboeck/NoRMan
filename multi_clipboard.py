import platform
import subprocess
import tkinter as tk

try:
    import win32clipboard  # Only available on Windows
except ImportError:
    win32clipboard = None  # Handle cases where it's not available

class MultiClipboard:
    """Base class for clipboard operations, to be implemented per OS."""

    def copy(self, text: str, format_type: str = "plaintext"):
        """
        Copies text to the clipboard.

        :param text: The text to copy.
        :param format_type: The format of the text ('plaintext', 'rtf', 'html').
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

class MacClipboard(MultiClipboard):
    """Clipboard handler for macOS, using pbcopy to support plaintext, RTF, and HTML."""

    def copy(self, text: str, format_type: str = "plaintext"):
        if format_type == "plaintext":
            # BUG: does not copy rft-links correctly
            process = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))

        elif format_type == "rtf":
            rtf_header = r"{\rtf1\ansi "
            full_rtf = rtf_header + text + "}"
            process = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
            process.communicate(full_rtf.encode("utf-8"))

        elif format_type == "html":
            process = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        print(f"Copied to clipboard as {format_type} (macOS).")

class WindowsClipboard(MultiClipboard):
    """Clipboard handler for Windows, using win32clipboard to support plaintext and RTF."""

    def copy(self, text: str, format_type: str = "plaintext"):
        if win32clipboard is None:
            raise RuntimeError("win32clipboard module is required for WindowsClipboard.")

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()

        if format_type == "plaintext":
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)

        elif format_type == "rtf":
            rtf_header = r"{\rtf1\ansi "
            full_rtf = rtf_header + text + "}"
            win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat("Rich Text Format"), full_rtf)

        elif format_type == "html":
            html_header = "Version:0.9\r\nStartHTML:00000097\r\nEndHTML:00000151\r\nStartFragment:00000129\r\nEndFragment:00000139\r\n<html><body><!--StartFragment-->"
            html_footer = "<!--EndFragment--></body></html>"
            full_html = html_header + text + html_footer
            win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat("HTML Format"), full_html)

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        win32clipboard.CloseClipboard()
        print(f"Copied to clipboard as {format_type} (Windows).")

class TkinterClipboard(MultiClipboard):
    """Fallback clipboard handler using Tkinter, supports only plaintext."""

    def copy(self, text: str, format_type: str = "plaintext"):
        if format_type != "plaintext":
            print("Warning: TkinterClipboard only supports plaintext. Copying as plain text.")

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()

        print("Text copied to clipboard (Tkinter fallback).")

class ClipboardFactory:
    """Factory to return the correct clipboard handler based on OS."""

    @staticmethod
    def get_clipboard():
        system_name = platform.system()

        if system_name == "Darwin":  # macOS
            return MacClipboard()
        elif system_name == "Windows" and win32clipboard:
            return WindowsClipboard()
        else:
            print(f"Warning: No OS-specific clipboard handler available for {system_name}. Using TkinterClipboard fallback.")
            return TkinterClipboard()
