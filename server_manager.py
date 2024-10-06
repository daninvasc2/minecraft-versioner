import os
import subprocess
import json
import tkinter as tk
import time
from tkinter import messagebox, filedialog

# Config file to store the Minecraft server path and RAM
CONFIG_FILE = "server_config.json"
server_process = None  # Global variable to store the server process

def load_config():
    """Load or create the config file with the Minecraft server path."""
    if not os.path.exists(CONFIG_FILE):
        # Create an empty config file if it doesn't exist
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'ram': '2048'}, f)  # Set a default RAM value of 1024 MB

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    # Ask for server path if not set
    if 'server_path' not in config or not config['server_path']:
        config['server_path'] = ask_for_path()
        save_config(config)

    return config


def save_config(config):
    """Save the current configuration to the file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def ask_for_path():
    """Ask the user to select the Minecraft server folder."""
    path = filedialog.askdirectory(title="Select Minecraft Server Folder")
    if not path:
        messagebox.showerror("Error", "You must select a folder.")
        return ask_for_path()
    return path


def git_pull(world_folder):
    """Run git pull in the world folder."""
    try:
        subprocess.check_call(['git', '-C', world_folder, 'pull', 'origin', 'master'])
        messagebox.showinfo("Git Sync", "World folder synced with Git repository.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", f"Git pull failed: {str(e)}")


def git_commit_push(world_folder):
    """Add all changes, commit and push to the master branch."""
    try:
        subprocess.check_call(['git', '-C', world_folder, 'add', '.'])
        subprocess.check_call(['git', '-C', world_folder, 'commit', '-m', 'World update after server stop'])
        subprocess.check_call(['git', '-C', world_folder, 'push', 'origin', 'master'])

        messagebox.showinfo("Git Sync", "World folder synced with Git repository.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", f"Git commit/push failed: {str(e)}")


def start_server(server_path, start_button, stop_button, ram_entry):
    """Start the Minecraft server and disable start button."""
    global server_process  # Use the global variable to store the server process

    config = load_config()
    world_folder = os.path.join(server_path, 'world')  # Assuming the world folder is inside the server path

    # Perform git pull to keep the world folder up to date
    git_pull(world_folder)

    # Get the RAM value from the entry
    ram_value = ram_entry.get()

    # Check if the RAM value is valid (numeric and greater than zero)
    if not ram_value.isdigit() or int(ram_value) <= 0:
        messagebox.showerror("Invalid RAM", "Please enter a valid positive integer for RAM.")
        return

    # Update the RAM value in the config
    config['ram'] = ram_value
    save_config(config)

    # Check if a custom start command is present in the config
    start_command = config.get('start_command')

    # Default command if none is provided
    if not start_command:
        start_command = ['java', f'-Xmx{ram_value}M', f'-Xms{ram_value}M', '-jar', 'server.jar', 'nogui']

    try:
        # Disable the start button and enable the stop button when the server starts
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

        # Start the server in a subprocess with stdin
        server_process = subprocess.Popen(start_command, cwd=server_path, stdin=subprocess.PIPE)

        messagebox.showinfo("Server Started", "The Minecraft server has started successfully.")

    except Exception as e:
        messagebox.showerror("Server Error", f"Failed to start the server: {str(e)}")
        start_button.config(state=tk.NORMAL)  # Re-enable start button on failure


def stop_server(server_path, start_button):
    """Stop the Minecraft server using its PID and sync with Git."""
    global server_process  # Access the global variable

    try:
        if server_process:
            server_process.stdin.write(b'stop\n')  # Send stop command
            time.sleep(15)  # Wait for the server to save and stop
            server_process.stdin.flush()  # Flush the input buffer to ensure the command is sent
            
            # Gracefully stop the server
            server_process.terminate()  # Terminate the server process
            server_process = None  # Clear the process reference

            subprocess.call(['TASKKILL', '/F', '/IM', 'java.exe'])
            messagebox.showinfo("Server Stopped", "The Minecraft server has stopped.")
        
            # Commit and push world folder
            world_folder = os.path.join(server_path, 'world')
            git_commit_push(world_folder)

            # Enable the start button and disable the stop button after stopping the server
            start_button.config(state=tk.NORMAL)

    except Exception as e:
        messagebox.showerror("Server Error", f"Failed to stop the server: {str(e)}")


def configure_ram(config, ram_entry):
    """Update the RAM entry field with the current value in the config."""
    ram_entry.delete(0, tk.END)  # Clear the current entry
    ram_entry.insert(0, config.get('ram', '1024'))  # Set to current RAM value


def main():
    # Load or initialize config
    config = load_config()
    server_path = config['server_path']
    
    # Create the GUI
    root = tk.Tk()
    root.title("Minecraft Server Manager")
    root.geometry("400x200")

    # Create RAM configuration section
    ram_label = tk.Label(root, text="RAM (MB):")
    ram_label.pack(pady=5)

    ram_entry = tk.Entry(root)
    configure_ram(config, ram_entry)  # Set current RAM value in the entry
    ram_entry.pack(pady=5)

    # Create start and stop buttons
    start_button = tk.Button(root, text="Start Server", command=lambda: start_server(server_path, start_button, stop_button, ram_entry))
    start_button.pack(pady=10)
    
    stop_button = tk.Button(root, text="Stop Server", command=lambda: stop_server(server_path, start_button))
    stop_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
