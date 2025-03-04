import importlib.util
import subprocess
import sys

def check_module(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True
        else:
            return False
    except ImportError:
        return False
    except Exception as e:
        print(f"Error checking {module_name}: {str(e)}")
        return False

def install_module(module_name, package_name):
    try:
        print(f"Attempting to install {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"Error during installation of {package_name}: {str(e)}")
        return False

def install_each_module():
    flag=True
    module_packages = {
        'git': 'gitpython',
        'werkzeug': 'werkzeug',
        'flask': 'flask'
    }

    modules_to_check = list(module_packages.keys()) 

    for module in modules_to_check:
        is_present = check_module(module)
        
        if not is_present:
            package_name = module_packages[module]
            print(f"Module {module} is missing. Attempting to install...")
            success = install_module(module, package_name)
            if success:
                    print(f"{module:<15} : ✓ Successfully installed")
            else:
                print(f"{module:<15} : ✗ Installation failed")
                print(f"{module:15} : Please install it manually")
                flag=False
    return flag                

