import difflib
import glob
import os
import shutil
import socket
import time
import tkinter as tk
from config import settings  # Import settings from config.py
import getpass  # Import getpass to get the username
import subprocess
import shlex  # Import shlex to safely handle command line parsing

class TerminalEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.apply_settings()
        self.text_widget = tk.Text(self, bg=self.bg_color, fg=self.font_color, insertbackground=self.cursor_color, font=(self.font_family, self.font_size))
        self.text_widget.tag_configure("bold", font=(self.font_family, self.font_size, "bold"))  # Configure bold tag for directory lines
        self.text_widget.tag_configure("command", foreground="blue")  # Syntax highlighting for commands
        self.text_widget.tag_configure("path", foreground="green")  # Syntax highlighting for paths
        self.text_widget.tag_configure("error", foreground="red")  # Syntax highlighting for error messages
        self.text_widget.tag_configure("success", foreground="green")  # Syntax highlighting for success messages
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
        # Get the IP address of the user
        user_ip = socket.gethostbyname(socket.gethostname())
        
        # Check if the user IP is in a previously stored list of IPs
        try:
            with open("user_ips.txt", "r+") as file:
                known_ips = file.read().splitlines()
                if user_ip not in known_ips:
                    # Display initializing messages if IP is not known
                    self.text_widget.insert(tk.END, "Initializing Terminal...\n", "bold")
                    self.text_widget.insert(tk.END, f"User: {getpass.getuser()}\n", "bold")
                    self.text_widget.insert(tk.END, "Access Granted\n", "bold")
                    file.write(user_ip + "\n")
                    
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
                else:
                    # If IP is known, just show the prompt
                    prompt = f"{self.current_directory}> "
                    self.text_widget.insert(tk.END, prompt, "bold")  # Apply bold tag to prompt
                    self.text_widget.see(tk.END)
        except FileNotFoundError:
            # If the file doesn't exist, create it and write the current IP
            with open("user_ips.txt", "w") as file:
                file.write(user_ip + "\n")
            # Display initializing messages if file is not found (first run)
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
        self.text_widget.insert(tk.END, f"Command '{command}' not recognized. Type 'help' for a list of available commands.\n", "error")

    def autocomplete(self, event):
        line_index = self.text_widget.index("insert linestart")
        line_text = self.text_widget.get(line_index, "insert lineend").strip()
        if line_text:
            parts = line_text.split()
            if len(parts) == 1:
                # Command autocomplete
                commands = [ "ping", "exit", "go", "cls", "clear", "help", "code", "dir", "echo", "mkdir", "settings", "tasklist", "systeminfo", "edit", "open"]
                matches = [c for c in commands if c.startswith(parts[0])]
                if matches:
                    self.show_autocomplete_dropdown(matches, line_index)
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
                        self.show_autocomplete_dropdown(files, line_index, len(parts[0]))
        return "break"  # Prevent default tab behavior

    def show_autocomplete_dropdown(self, options, line_index, prefix_len=0):
        # Calculate position for dropdown
        x, y, _, _ = self.text_widget.bbox(line_index)
        window_x = self.text_widget.winfo_rootx() + x
        window_y = self.text_widget.winfo_rooty() + y + self.text_widget.winfo_height()

        # Create dropdown menu
        menu = tk.Menu(self.text_widget, tearoff=0)
        for option in options:
            menu.add_command(label=option, command=lambda opt=option: self.insert_autocomplete(opt, line_index, prefix_len))
        menu.tk_popup(window_x, window_y, 0)

    def insert_autocomplete(self, text, line_index, prefix_len):
        self.text_widget.delete(line_index, "insert lineend")
        if prefix_len > 0:
            self.text_widget.insert(f"{line_index}+{prefix_len}c", text + " ", "path")
        else:
            self.text_widget.insert(line_index, text + " ", "command")
        self.text_widget.focus_set()  # Return focus to the text widget

    def suggest_correction(self, input_text):
        commands = ["ping", "exit", "go", "cls", "clear", "help", "code", "dir", "echo", "mkdir", "settings", "tasklist", "systeminfo", "edit", "open"]
        directories = [d for d in os.listdir(self.current_directory) if os.path.isdir(os.path.join(self.current_directory, d))]
        files = [f for f in os.listdir(self.current_directory) if os.path.isfile(os.path.join(self.current_directory, f))]
        suggestions = []

        # Check for command suggestions
        command_suggestions = difflib.get_close_matches(input_text, commands, n=1, cutoff=0.7)
        if command_suggestions:
            suggestions.extend(command_suggestions)

        # Check for directory suggestions
        directory_suggestions = difflib.get_close_matches(input_text, directories, n=1, cutoff=0.7)
        if directory_suggestions:
            suggestions.extend(directory_suggestions)

        # Check for file suggestions
        file_suggestions = difflib.get_close_matches(input_text, files, n=1, cutoff=0.7)
        if file_suggestions:
            suggestions.extend(file_suggestions)

        if suggestions:
            suggestion_text = f"Did you mean: {', '.join(suggestions)}?"
            self.text_widget.insert(tk.END, suggestion_text + "\n", "bold")
        else:
            self.text_widget.insert(tk.END, "No suggestions found.\n", "bold")

    def update_prompt_on_newline(self, event):
        if event.keysym == "Return":
            self.update_prompt()
    
    def optimize_terminal_performance(self):
        # Increase the text widget's performance by reducing redraws
        self.text_widget.configure(autoseparators=False, maxundo=-1)

        # Optimize the handling of large volumes of output
        self.text_widget.bind("<Configure>", self.handle_large_output)

    def handle_large_output(self, event=None):
        # Temporarily disable updates to handle large volumes of output efficiently
        self.text_widget.configure(state='disabled')
        self.text_widget.after(100, self.enable_text_widget_updates)

    def enable_text_widget_updates(self):
        # Re-enable updates after processing is complete
        self.text_widget.configure(state='normal')

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
            if len(command_parts) == 1:
                help_text = (
                    "General Commands:\n"
                    "  help: Show this help message\n"
                    "  date: Display the current date and time\n"
                    "  exit: Go to a previous directory\n"
                    "  go <path>: Navigate to a directory\n"
                    "  cls, clear: Clear the terminal screen\n"
                    "\nFile Management Commands:\n"
                    "  dir: List the contents of the current directory\n"
                    "  edit <file>: Open and display the contents of a file\n"
                    "  mkdir <directory_name>: Create a new directory\n"
                    "  open: Open the current directory in the system's default file manager\n"
                    "  openfile <file_path>: Open and display the contents of a file\n"
                    "  rename <old_file_path> <new_file_path>: Rename a file or directory.\n"
                    "  diff <file1> <file2>: Compare the contents of two files\n"
                    "\nUtility Commands:\n"
                    "  code: Open the current directory in Visual Studio Code\n"
                    "  echo <text>: Print the specified text\n"
                    "  settings -<setting> <value>: Change the specified setting\n"
                    "  tasklist: Display all running processes\n"
                    "  systeminfo: Display system information\n"
                    "  issue <issue_text>: Submit an issue to the Nebula Terminal Development Community\n"
                    "  ping <target>: Ping the specified target\n"
                    "  ssh <target>: Establish an SSH connection to the specified target\n"
                    "  listports: List all open ports on the system\n",
                    "  git <command>: Execute a git command.\n"
                )
                self.text_widget.insert(tk.END, "\n\n" + ''.join(help_text))
            elif len(command_parts) > 1:
                detailed_command = command_parts[1]
                detailed_help = {
                    "exit": "exit: Exit the terminal or go to the previous directory.\n",
                    "go": "go <path>: Navigate to the specified directory path.\n",
                    "cls": "cls, clear: Clear the terminal screen.\n",
                    "clear": "cls, clear: Clear the terminal screen.\n",
                    "help": "help: Show this help message or detailed help for a specific command.\n",
                    "code": "code: Open the current directory in Visual Studio Code.\n",
                    "dir": "dir: List all files and directories in the current directory.\n",
                    "echo": "echo <text>: Print the specified text to the terminal.\n",
                    "mkdir": "mkdir <directory_name>: Create a new directory with the specified name.\n",
                    "settings": "settings -<setting> <value>: Change the specified setting to the given value.\n",
                    "tasklist": "tasklist: Display all currently running processes.\n",
                    "systeminfo": "systeminfo: Display detailed system information.\n",
                    "edit": "edit <file>: Open and display the contents of the specified file.\n",
                    "open": "open: Open the current directory in the system's default file manager.\n",
                    "issue": "issue <issue_text>: Submit an issue to the Nebula Terminal Development Community.\n",
                    "openfile": "openfile <file_path>: Open and display the contents of the specified file.\n",
                    "ping": "ping <target>: Ping the specified target.\n",
                    "ssh": "ssh <target>: Establish an SSH connection to the specified target.\n",
                    "date": "date: Display the current date and time.\n",
                    "diff": "diff <file1> <file2>: Compare the contents of two files.\n",
                    "listports": "listports: List all open ports on the system.\n",
                    "rename": "rename <old_file_path> <new_file_path>: Rename a file or directory.\n",
                    "git": "git <command>: Execute a git command.\n"
                }
                help_message = detailed_help.get(detailed_command, f"No detailed help available for: {detailed_command}")
                self.text_widget.insert(tk.END, "\n\n" + help_message)
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
        
        elif command == "openfile" and len(command_parts) > 1:
            file_path = os.path.join(self.current_directory, command_parts[1])
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()
                self.text_widget.insert(tk.END, f"\nContents of {file_path}:\n{file_content}\n")
            except FileNotFoundError:
                self.text_widget.insert(tk.END, f"\nFile not found: {file_path}. Please check the file path and try again.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to open file: {str(e)}. Please check the file and try again.\n")
            return  # Avoid updating the prompt after opening file
        elif command == "ping" and len(command_parts) > 1:
            target = command_parts[1]
            try:
                output = subprocess.check_output(["ping", target], text=True)
                self.text_widget.insert(tk.END, f"\nPing results for {target}:\n{output}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to ping {target}: {str(e)}\n")
            return  # Avoid updating the prompt after pinging
        elif command == "ssh" and len(command_parts) > 1:
            target = command_parts[1]
            try:
                ssh_output = subprocess.check_output(["ssh", target], text=True)
                self.text_widget.insert(tk.END, f"\nSSH connection to {target} established:\n{ssh_output}\n")
            except subprocess.CalledProcessError as e:
                self.text_widget.insert(tk.END, f"\nSSH connection to {target} failed with error code {e.returncode}.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to establish SSH connection to {target}: {str(e)}\n")
            return  # Avoid updating the prompt after SSH command
        elif command == "date":
            try:
                current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.text_widget.insert(tk.END, f"\n\nCurrent date and time: {current_date}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to get current date and time: {str(e)}\n")
            return  # Avoid updating the prompt after displaying date and time
        elif command == "diskusage":
            try:
                disk_usage = shutil.disk_usage("/")
                total, used, free = disk_usage.total, disk_usage.used, disk_usage.free
                self.text_widget.insert(tk.END, f"\nDisk Usage: Total: {total} bytes, Used: {used} bytes, Free: {free} bytes\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to get disk usage: {str(e)}\n")
            return  # Avoid updating the prompt after displaying disk usage
        elif command == "diff" and len(command_parts) > 2:
            file1_path = os.path.join(self.current_directory, command_parts[1])
            file2_path = os.path.join(self.current_directory, command_parts[2])
            try:
                with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
                    file1_lines = file1.readlines()
                    file2_lines = file2.readlines()
                diff = difflib.unified_diff(file1_lines, file2_lines, fromfile=file1_path, tofile=file2_path)
                diff_output = ''.join(diff)
                if diff_output:
                    self.text_widget.insert(tk.END, f"\nDifferences between {file1_path} and {file2_path}:\n{diff_output}\n")
                else:
                    self.text_widget.insert(tk.END, f"\nNo differences found between {file1_path} and {file2_path}.\n")
            except FileNotFoundError as e:
                self.text_widget.insert(tk.END, f"\nFile not found: {str(e)}. Please check the file paths and try again.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to compare files: {str(e)}.\n")
            return  # Avoid updating the prompt after diff command
        elif command == "listports":
            try:
                import socket
                open_ports = []
                for port in range(1, 1025):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:
                        open_ports.append(port)
                    sock.close()
                if open_ports:
                    ports_str = ', '.join(map(str, open_ports))
                    self.text_widget.insert(tk.END, f"\nOpen ports: {ports_str}\n")
                else:
                    self.text_widget.insert(tk.END, "\nNo open ports found.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nFailed to list open ports: {str(e)}\n")
            return  # Avoid updating the prompt after listing ports
        elif command == "rename" and len(command_parts) > 2:
            old_file_path = os.path.join(self.current_directory, command_parts[1])
            new_file_path = os.path.join(self.current_directory, command_parts[2])
            try:
                os.rename(old_file_path, new_file_path)
                self.text_widget.insert(tk.END, f"\nFile renamed from {command_parts[1]} to {command_parts[2]}\n")
            except FileNotFoundError:
                self.text_widget.insert(tk.END, f"\nFile not found: {old_file_path}. Please verify the file path and try again.\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nError renaming file: {str(e)}\n")
            return  # Avoid updating the prompt after renaming file
        elif command.startswith("git clone"):
            try:
                #import subprocess
                git_command = command.split()
                if len(git_command) < 3:
                    self.text_widget.insert(tk.END, "\nUsage: git clone <repository-url>\n")
                else:
                    repo_url = git_command[2]
                    result = subprocess.run(["git", "clone", repo_url, self.current_directory], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.text_widget.insert(tk.END, f"\nSuccessfully cloned {repo_url} into {self.current_directory}\n")
                    else:
                        self.text_widget.insert(tk.END, f"\nFailed to clone repository: {result.stderr}\n")
            except Exception as e:
                self.text_widget.insert(tk.END, f"\nError executing git clone: {str(e)}\n")
            return  # Avoid updating the prompt after git clone command
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
