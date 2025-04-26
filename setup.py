import os
import subprocess
import sys
import venv

def create_and_activate_venv(venv_path):
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment at {venv_path}")
        venv.create(venv_path, with_pip=True)
    
    # Determine the pip executable path
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    return pip_path

def install_module(module_name, venv_path="venv"):
    print(f"Attempting to install '{module_name}' system-wide with pip...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", module_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Successfully installed '{module_name}' system-wide.")
        return True
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout if e.stdout else ""
        if "externally-managed-environment" in error_output.lower():
            print("Externally-managed-environment error detected. Switching to virtual environment...")
        else:
            print(f"Failed to install '{module_name}' system-wide: {error_output}")
            return False
    
    try:
        pip_path = create_and_activate_venv(venv_path)
        write_data = open("is_venv", 'w')
        write_data.write("OnEiEbLvOgD")
        write_data.close()
        print(f"Installing '{module_name}' in virtual environment at {venv_path}...")
        subprocess.check_call([pip_path, "install", module_name])
        print(f"Successfully installed '{module_name}' in virtual environment.")        
        return True
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout if e.stdout else ""
        print(f"Failed to install '{module_name}' in virtual environment: {error_output}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    create_file = open("is_venv",'w')
    create_file.close()
    read_module_names = open("modules.txt", 'r')
    data = read_module_names.readlines()
    read_module_names.close()
    for name in data:
        name = name.replace("\n", "")
        success = install_module(name)
        if not success:
            sys.ext(1)
    
