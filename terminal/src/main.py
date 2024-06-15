import tkinter as tk
import os
import subprocess
import getpass  # Import getpass to get the username
from config import settings  # Import settings from config.py
import time
import glob  

class TerminalEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.apply_settings()
        self.text_widget = tk.Text(self, bg=self.bg_color, fg=self.font_color, insertbackground=self.cursor_color, font=(self.font_family, self.font_size))
        self.text_widget.tag_configure("bold", font=(self.font_family, self.font_size, "bold"))  # Configure bold tag for directory lines
        self.text_widget.tag_configure("command", foreground="blue")  # Syntax highlighting for commands
        self.text_widget.tag_configure("path", foreground="green")  # Syntax highlighting for paths
        self.text_widget.pack(expand=True, fill='both')
        self.current_directory = os.path.expanduser("~/Downloads")
        self.text_widget.bind("<Return>", self.process_command)
        self.text_widget.bind("<KeyRelease>", self.update_prompt_on_newline)
        self.initial_prompt()

    def apply_settings(self):
        self.title("Nebula Terminal")
        self.geometry("800x600")  # Size similar to Windows 11 terminal
        self.bg_color = settings['background_color']
        self.font_color = settings['font_color']
        self.cursor_color = settings.get('cursor_color', self.font_color)  # Use font color as default if cursor_color is not set
        self.font_family = settings['font_family']
        self.font_size = settings['font_size']
        self.configure(bg=self.bg_color)
        self.attributes('-alpha', settings['transparency_level'] if settings['transparency'] else 1.0)  # Set transparency
        self.resizable(True, True)  # Allow the window to be resizable

    def initial_prompt(self):
        # Display initializing messages
        self.text_widget.insert(tk.END, "Initializing Terminal...\n", "bold")
        self.text_widget.insert(tk.END, f"User: {getpass.getuser()}\n", "bold")
        self.text_widget.insert(tk.END, "Access Granted\n", "bold")
        
        def countdown(i):
            if i > 0:
                self.text_widget.delete("end-2l", "end-1l")
                self.text_widget.insert(tk.END, f"Continuing in {i}...\n", "bold")
                self.text_widget.update()
                self.after(1000, countdown, i-1)
            else:
                self.text_widget.delete("1.0", tk.END)
                prompt = f"{self.current_directory}> "
                self.text_widget.insert(tk.END, prompt, "bold")  # Apply bold tag to prompt
                self.text_widget.see(tk.END)
        
        countdown(5)

    def handle_unknown_command(self, command):
        self.text_widget.insert(tk.END, f"Command '{command}' not recognized. Type 'help' for a list of available commands.\n", "bold")

    def autocomplete(self, event):
        line_index = self.text_widget.index("insert linestart")
        line_text = self.text_widget.get(line_index, "insert lineend").strip()
        if line_text:
            parts = line_text.split()
            if len(parts) == 1:
                # Command autocomplete
                commands = ["exit", "go", "cls", "clear", "help", "code", "dir", "echo", "mkdir", "settings", "tasklist", "systeminfo", "edit", "open"]
                matches = [c for c in commands if c.startswith(parts[0])]
                if matches:
                    self.text_widget.delete(line_index, "insert lineend")
                    self.text_widget.insert(line_index, matches[0] + " ", "command")
            else:
                # File path autocomplete
                path = parts[-1]
                expanded_path = os.path.expanduser(path)
                if '*' not in expanded_path and not expanded_path.endswith(os.sep):
                    expanded_path += '*'
                files = glob.glob(expanded_path)
                if files:
                    common_prefix = os.path.commonprefix(files)
                    if common_prefix != path:
                        self.text_widget.delete(f"{line_index}+{len(parts[0])}c", "insert lineend")
                        self.text_widget.insert(f"{line_index}+{len(parts[0])}c", common_prefix, "path")
        return "break"  # Prevent default tab behavior

    def update_prompt_on_newline(self, event):
        if event.keysym == "Return":
            self.update_prompt()

    def update_prompt(self):
        prompt = f"{self.current_directory}> "
        self.text_widget.delete("insert linestart", "insert lineend")
        self.text_widget.insert("insert", prompt, "bold")  # Apply bold tag to prompt
        self.text_widget.see(tk.END)

    def process_command(self, event):
        line_index = self.text_widget.index("insert linestart")
        line_text = self.text_widget.get(line_index, "insert lineend")
        command_parts = line_text.strip().split("> ")
        if len(command_parts) > 1:
            command_parts = command_parts[-1].split()
        else:
            command_parts = []
        if len(command_parts) == 0:
            return  # No command entered, just update the prompt
        command = command_parts[0]
        if command == "exit":
            self.current_directory = os.path.expanduser("~")
        elif command == "go" and len(command_parts) > 1:
            target_dir = command_parts[1]
            if os.path.isabs(target_dir):
                new_path = target_dir
            else:
                new_path = os.path.join(self.current_directory, target_dir)
            if os.path.exists(new_path):
                self.current_directory = new_path
            else:
                self.text_widget.insert(tk.END, f"\nDirectory not found: {new_path}. Please check the path and try again.\n")
                return  # Avoid updating the prompt after showing error message
        elif command == "cls" or command == "clear":
            self.text_widget.delete("1.0", tk.END)
        elif command == "help":
            help_text = (
                "exit: Go to a previous directory\n"
                "go <path>: Navigate to a directory\n"
                "cls, clear: Clear the terminal screen\n"
                "help: Show this help message\n"
                "code: Open the current directory in Visual Studio Code\n"
                "dir: List the contents of the current directory\n"
                "echo <text>: Print the specified text\n"
                "mkdir <directory_name>: Create a new directory\n"
                "settings -<setting> <value>: Change the specified setting\n"
                "tasklist: Display all running processes\n"
                "systeminfo: Display system information\n"
                "edit <file>: Open and display the contents of a file\n"
                "open: Open the current directory in the system's default file manager\n"
                "issue <issue_text>: Submit an issue to the Nebula Terminal Development Community\n"
            )
            self.text_widget.insert(tk.END, "\n\n" + help_text)
            return  # Avoid updating the prompt after showing help
        elif command == "edit" and len(command_parts) > 1:
            file_path = os.path.join(self.current_directory, command_parts[1])
            try:
                with open(file_path, 'r') as file:
                    file_contents = file.read()
                self.text_widget.insert(tk.END, f"\n{file_contents}\n")
            except FileNotFoundError:
                self.text_widget.insert(tk.END, f"\nFile not found: {file_path}. Please verify the file path and try again.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nError opening file: {str(e)}\n")
            return  # Avoid updating the prompt after displaying file contents
        elif command == "code":
            try:
                subprocess.run(["code", self.current_directory])
            except FileNotFoundError:
                self.text_widget.insert(tk.END, "\nVisual Studio Code is not installed or not found in PATH. Please install it or check your PATH settings.\n")
        elif command == "dir":
            try:
                directory_contents = []
                for root, dirs, files in os.walk(self.current_directory):
                    for name in files:
                        if "__pycache__" not in name:
                            directory_contents.append(os.path.join(root, name))
                directory_contents_str = "\n".join(directory_contents)
                self.text_widget.insert(tk.END, f"\n\n{directory_contents_str}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nError listing directory contents: {str(e)}\n")
            return  # Avoid updating the prompt after showing directory contents
        elif command == "echo":
            echo_text = " ".join(command_parts[1:])
            self.text_widget.insert(tk.END, f"\n{echo_text}\n")
            return  # Avoid updating the prompt after echoing text
        elif command == "mkdir":
            if len(command_parts) > 1:
                new_dir = command_parts[1]
                try:
                    os.makedirs(os.path.join(self.current_directory, new_dir), exist_ok=True)
                    self.text_widget.insert(tk.END, f"\nDirectory created: {new_dir}\n")
                except Exception as e:
                    self.text_widget.insert(tk.END, f"\nError creating directory: {str(e)}\n")
            else:
                self.text_widget.insert(tk.END, "\nUsage: mkdir <directory_name>\n")
            return  # Avoid updating the prompt after mkdir operation
        elif command == "settings" and len(command_parts) > 2:
            setting_key = command_parts[1].lstrip('-')
            setting_value = command_parts[2]
            if setting_key in settings and isinstance(settings[setting_key], (int, float, str)):
                settings[setting_key] = type(settings[setting_key])(setting_value)
                self.apply_settings()  # Reapply settings to update the terminal
                self.text_widget.insert(tk.END, f"\nSetting updated: {setting_key} = {setting_value}\n")
                self.update_prompt()  # Update the prompt to reflect any changes in settings
            else:
                self.text_widget.insert(tk.END, f"\nInvalid setting or value type for: {setting_key}. Please check the setting name and value type.\n")
            return  # Avoid updating the prompt after settings change
        elif command == "tasklist":
            try:
                output = subprocess.check_output("tasklist", shell=True).decode()
                self.text_widget.insert(tk.END, f"\n{output}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to retrieve task list: {str(e)}. Please check your system permissions or configuration.\n")
            return  # Avoid updating the prompt after showing task list
        elif command == "systeminfo":
            try:
                output = subprocess.check_output("systeminfo", shell=True).decode()
                self.text_widget.insert(tk.END, f"\n{output}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to retrieve system information: {str(e)}. Please check your system permissions or configuration.\n")
            return  # Avoid updating the prompt after showing system info
        elif command == "open":
            try:
                subprocess.run(["explorer", self.current_directory], check=True)
                self.text_widget.insert(tk.END, f"\nOpened directory: {self.current_directory}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to open directory: {str(e)}. Please check your system settings or permissions.\n")
            return  # Avoid updating the prompt after opening directory
        elif command == "issue" and len(command_parts) > 1:
            try:
                import requests
                issue_text = " ".join(command_parts[1:])
                issue_count = getattr(self, 'issue_count', 0) + 1
                setattr(self, 'issue_count', issue_count)
                formatted_issue_text = f"**Community Issue #{issue_count}**:\n```{issue_text}```"
                discord_webhook_url = "https://discord.com/api/webhooks/1251500620989595659/-T8_pur4o5Nirj9mdTaXcvOzR6idR9FB0iWaiyW0WmjXSTVF-IXj6aJZRjgGKyUaHui8"
                data = {
                    "content": formatted_issue_text,
                    "username": "Nebula Terminal Community Issues",
                    #"avatar_url": "https://example.com/image.png"  # Optional: Add an avatar URL if desired
                }
                response = requests.post(discord_webhook_url, json=data)
                if response.status_code == 204:
                    self.text_widget.insert(tk.END, "\nIssue submitted to Discord. Thank you!\n")
                else:
                    self.text_widget.insert(tk.END, f"\nFailed to submit issue to Discord: HTTP {response.status_code}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to submit issue to Discord: {str(e)}\n")
            return  # Avoid updating the prompt after submitting issue
        else:
            self.handle_unknown_command(command)
            return
        self.update_prompt()

        
    def increase_font_size(self, event):
        self.font_size += 1
        self.text_widget.config(font=(self.font_family, self.font_size))
        return "break"

    def decrease_font_size(self, event):
        self.font_size -= 1
        self.text_widget.config(font=(self.font_family, self.font_size))
        return "break"

def initialize_terminal():
    terminal_app = TerminalEmulator()
    terminal_app.mainloop()

if __name__ == "__main__":
    initialize_terminal()
