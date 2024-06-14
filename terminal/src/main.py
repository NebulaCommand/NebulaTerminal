import tkinter as tk
import os
import subprocess

class TerminalEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Terminal Emulator")
        self.geometry("900x600")  # Adjusted to typical terminal size
        self.configure(bg='black')  # Set background color to black
        self.attributes('-alpha', 0.9)  # Set transparency to 90%
        self.current_dir = os.path.expanduser("~")  # Start at the user's home directory

        # Create a text widget for displaying output and capturing input
        self.output_text = tk.Text(self, font=("Consolas", 12), bg='black', fg='white', insertbackground='white')
        self.output_text.pack(fill='both', expand=True)
        self.output_text.bind("<Return>", self.process_command)
        self.display_current_dir()

    def display_current_dir(self):
        # Display the current directory as a prompt
        self.output_text.insert(tk.END, f"{os.getcwd()} $ ")
        self.output_text.mark_set(tk.INSERT, tk.END)
        self.output_text.insert(tk.END, "\n")
        self.output_text.see(tk.END)

    def process_command(self, event):
        # Prevent the default return key behavior
        event.widget.mark_set("insert", "end-1c linestart")
        line_index = event.widget.index("insert")
        line_content = event.widget.get(line_index, "insert lineend")
        command = line_content.strip()
        
        # Handle changing directory
        if command.startswith("cd "):
            new_dir = command[3:].strip()
            try:
                os.chdir(new_dir)
                self.current_dir = os.getcwd()
            except OSError as e:
                self.output_text.insert(tk.END, f"Error: {str(e)}\n")
        else:
            # Execute other system commands
            try:
                output = subprocess.check_output(command, shell=True, cwd=self.current_dir, stderr=subprocess.STDOUT, text=True)
                self.output_text.insert(tk.END, output)
            except subprocess.CalledProcessError as e:
                self.output_text.insert(tk.END, e.output)
        
        # Clear the command and display the new prompt
        self.output_text.delete(line_index, "insert lineend")
        self.display_current_dir()

def initialize_terminal():
    terminal_app = TerminalEmulator()
    terminal_app.mainloop()

if __name__ == "__main__":
    initialize_terminal()