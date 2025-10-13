import os
import subprocess
import sys
try:
    import venv
except ModuleNotFoundError:
    print("Please install `venv` module")
    sys.exit(1)

try:
    from git import Repo
except ModuleNotFoundError:
    print("Please install `git` module")
    sys.exit(1)


def create_and_activate_venv(venv_path):
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment at {venv_path}")
        venv.create(venv_path, with_pip=True)

    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")

    return pip_path, python_path


def is_module_installed(module_name, python_path):
    try:
        subprocess.check_call(
            [python_path, "-m", "pip", "show", module_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_module(module_name, venv_path="venv"):
    try:
        pip_path, python_path = create_and_activate_venv(venv_path)

        if is_module_installed(module_name, python_path):
            return True

        print(f"Installing '{module_name}' in virtual environment at {venv_path}...", end="")
        subprocess.check_call(
            [pip_path, "install", module_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[success]")
        return True

    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout if e.stdout else ""
        print(f"Failed to install '{module_name}' in virtual environment: {error_output}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def load_module(module_file_path):
    with open(module_file_path, "r") as read_module_names:
        data = read_module_names.readlines()

    for name in data:
        name = name.strip()
        if not name:
            continue
        success = install_module(name, "IHA089_Labs_venv")
        if not success:
            sys.exit(1)

def create_lab_dir():
    if not os.path.isdir("Labs"):
        os.mkdir("Labs")
        
def get_mail_server():
    url = "https://github.com/IHA089/IHA089-Mail.git"
    dirname = "IHA089_Mail"
    dir_path = os.getcwd()+'/'+dirname
    create_lab_dir()
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
        try:
            print(f"\rGetting mail server files...", end="")
            Repo.clone_from(url, dir_path)
            print(f"\rsuccess{' '*40}")
        except Exception as e:
            print("An error occur: "+e)
            sys.exit()
