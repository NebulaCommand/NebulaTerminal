import tkinter as tk
import os

class TerminalEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nebula Terminal")
        self.geometry("800x600")  # Size similar to Windows 11 terminal
        self.configure(bg='black')
        self.attributes('-alpha', 0.8)  # Set transparency

        # Create a text widget to simulate terminal output
        self.text_widget = tk.Text(self, bg='black', fg='white', insertbackground='white')
        self.text_widget.pack(expand=True, fill='both')
        self.current_directory = os.path.expanduser("~/Downloads")
        self.text_widget.bind("<Return>", self.process_command)
        self.text_widget.bind("<KeyRelease>", self.update_prompt_on_newline)
        self.initial_prompt()

    def initial_prompt(self):
        prompt = f"{self.current_directory}> "
        self.text_widget.insert(tk.END, prompt)
        self.text_widget.see(tk.END)

    def update_prompt_on_newline(self, event):
        if event.keysym == "Return":
            self.update_prompt()

    def update_prompt(self):
        prompt = f"{self.current_directory}> "
        self.text_widget.delete("insert linestart", "insert lineend")
        self.text_widget.insert("insert", prompt)
        self.text_widget.see(tk.END)

    def process_command(self, event):
        line_index = self.text_widget.index("insert linestart")
        line_text = self.text_widget.get(line_index, "insert lineend")
        command_parts = line_text.strip().split("> ")[-1].split()
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
                self.text_widget.insert(tk.END, f"\nDirectory not found: {new_path}\n")
                return  # Avoid updating the prompt after showing error message
        elif command == "cls" or command == "clear":
            self.text_widget.delete("1.0", tk.END)
        elif command == "help":
            help_text = (
                "exit: Go to a previous directory\n"
                "go <path>: Navigate to a directory\n"
                "cls, clear: Clear the terminal screen\n"
                "help: Show this help message\n"
            )
            self.text_widget.insert(tk.END, "\n\n" + help_text)
            return  # Avoid updating the prompt after showing help
        self.text_widget.delete(line_index, "insert lineend")
        self.update_prompt()

def initialize_terminal():
    terminal_app = TerminalEmulator()
    terminal_app.mainloop()

if __name__ == "__main__":
    initialize_terminal()