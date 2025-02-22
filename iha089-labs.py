from git import Repo
import os, socket, sys, time, threading, subprocess
from werkzeug.serving import make_server
from shutil import rmtree
from json import load
import importlib.util
from flask import Flask, request, jsonify
import ssl


class FlaskThread:
    def __init__(self, app, host="127.0.0.1", port=5000, certfile=None, keyfile=None):
        self.app = app
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile

        self.ssl_context = None
        if certfile and keyfile:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        self.server = make_server(host, port, app)

        if self.ssl_context:
            self.server.socket = self.ssl_context.wrap_socket(self.server.socket, server_side=True)

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.running = False

    def start(self):
        if self.port==443:
            print(f"{self.app.name} Lab is running...")
            print("Access your lab ::: https://iha089-labs.in")
            print("Type 'close' to stop.")
        self.running = True
        self.thread.start()

    def stop(self):
        print(f"\rStopping {self.app.name} Lab...", end="")
        if self.running:
            self.server.shutdown()
            self.thread.join()
            self.running = False
        print(f"\r{self.app.name} Lab stopped.")

def is_admin():
    if os.name == 'nt':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.getuid() == 0

def run_as_admin(func_name):
    if os.name == 'nt':
        try:
            import ctypes
            params = " ".join(sys.argv)
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
        except Exception as e:
            print(f"Failed to gain administrator privileges: {e}")
            sys.exit(1)
    else:
        try:
            command = ["sudo", sys.executable, __file__, func_name]
            subprocess.check_call(command)
        except Exception as e:
            print(f"Failed to gain root privileges: {e}")
            sys.exit(1)

def update_host_file():
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        os.system("certutil -addstore Root \"rootCA.pem\"")
        
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        print("unknown OS. Mail on contact@iha089.org")
    
    with open(host_path, 'r') as ff:
        data = ff.read()
    
    if not "127.0.0.1   iha089-labs.in" in data:
        with open(host_path, 'a') as dd:
            dd.write("127.0.0.1   iha089-labs.in")

def check_for_host_path():
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    
    with open(host_path, 'r') as ff:
        data = ff.read()
    
    if "127.0.0.1   iha089-labs.in" in data:
        return True
    else:
        return False
        
def check_ineternet_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8",80))
        return True
    except OSError:
        print("No internet connection")
        return False

flask_thread = None

mail_server_addr=""


def run_vulnerable_lab(file_path, app_name, u_port):
    global flask_thread
    try:
        spec = importlib.util.spec_from_file_location(app_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        flask_app = getattr(module, app_name)

        if not isinstance(flask_app, Flask):
            raise ValueError(f"The object '{app_name}' is not a Flask instance.")
        app_dir = os.path.dirname(file_path)
        flask_app.template_folder = os.path.join(app_dir, "templates")
        flask_app.static_folder = os.path.join(app_dir, "static")

        flask_thread = FlaskThread(
            flask_app,
            host="127.0.0.1",
            port=u_port,
            certfile="iha089-labs.in.crt",
            keyfile="iha089-labs.in.key"
        )
        flask_thread.start()

    except Exception as e:
        print(f"Error: {e}")

def stop_flask_app():
    global flask_thread
    if flask_thread:
        flask_thread.stop()
        flask_thread = None
    else:
        print("No Vulnerable Lab is currently running.")
    
def get_lab_info():
    lab_info_url = "https://github.com/IHA089/iha089_lab_info.git"
    dirname="iha089_lab_info"

    to_path = os.getcwd()+'/'+dirname
    if os.path.isdir(to_path):
        if os.name == "posix":
            os.system("rm -rf iha089_lab_info")
        elif os.name == "nt":
            os.system("rmdir /s /q \"iha089_lab_info\"")

    os.mkdir(dirname)

    try:
        print(f"\rFetch all available labs...", end="")
        Repo.clone_from(lab_info_url, to_path)
        print(f"\rfetch success{' '*20}")
    except Exception as e:
        print("An error occur: "+e)

def get_mail_server():
    url = "https://github.com/IHA089/IHA089-Mail.git"
    dirname = "IHA089-Mail"
    dir_path = os.getcwd()+'/'+dirname

    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
        try:
            print(f"\rGetting mail server files...", end="")
            Repo.clone_from(url, dir_path)
            print(f"\rsuccess{' '*40}")
        except Exception as e:
            print("An error occur: "+e)
            sys.exit()

def check_lab_is_present(lab_url, cat_name, nname, mailserver):
    global mail_server_addr
    lab_path = os.getcwd()+"/"+cat_name+lab_url

    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)
        try:
            print(f"\rFetching {lab_url.replace('/','')} lab....", end="")
            lab_git_url = "https://github.com/IHA089"+lab_url+".git"
            Repo.clone_from(lab_git_url, lab_path)
            print(f"\rfetching success{' '*30}")
        except Exception as e:
            print("An error occur: "+e)
            sys.exit()
    else:
        pass
    ff_path = lab_path+lab_url.replace('Lab','')+".py"
    
    if mail_server_addr == "":
        mail_app_name = "MailServerIHA089"
        mail_file_path = os.getcwd()+"/IHA089-Mail/MailServerIHA089.py"
        run_vulnerable_lab(mail_file_path, app_name=mail_app_name, u_port=7089)
        mail_server_addr = "https://127.0.0.1:7089"

    if mailserver == "yes":
        print("Access mail system::: "+mail_server_addr)

    appName = lab_url.replace("/",'')
    appName = appName.replace('Lab','')
    run_vulnerable_lab(ff_path, app_name=appName, u_port=443)
    
    while True:
        user_input = input(nname).strip().lower()
        if user_input in ('stop', 'close'):
            stop_flask_app()
            break
        else:
            print("Unknown command. Type 'stop' or 'close' to stop the lab.")


def each_info(lab_info, cat_name, nname, mailserver):
    lab_desc = lab_info['description']
    lab_url = lab_info['laburl']
    blog_url = lab_info['blogurl']

    check_lab_is_present(lab_url, cat_name, nname, mailserver)

def chech_main_lab_name(name):
    lab_path = os.getcwd()+'/'+name
    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)
    
def show_labs():
    json_path = "iha089_lab_info/manage_labs.json"
    with open(json_path, "r") as file:
        data = load(file)

    print("Available Lab Categories:")
    categories = list(data['labs'].keys())
    for idx, category in enumerate(categories, 1):
        print(f"{idx}. {category}")
    print("press `ctrl+c` for exit")
    
    flag=True
    while flag:
        try:
            choice = int(input("\nIHA089-LABS#>"))
            flag=False
        except KeyboardInterrupt:
            print("Exit by user")
            sys.exit()
        except ValueError:
            flag=True

        if flag is False and 1 <= choice <= len(categories):
            selected_category = categories[choice - 1]
            cat_name = data['labs'][selected_category]['name']
            chech_main_lab_name(cat_name)
            sub_cat = list(data['labs'][selected_category]['labs'].keys())

            flag2=True
            while flag2:
                print("0. go to back")
                for idx, sub in enumerate(sub_cat, 1):
                    print(f"{idx}. {sub}")
                print("press `ctrl+c` for exit")
                try:
                    nname= "\nIHA089-LABS/"+cat_name+"#>"
                    sub_choice = int(input(nname))
                    flag2=False
                except KeyboardInterrupt:
                    print("Exit by user")
                    sys.exit()
                except ValueError:
                    flag2=True

                if flag2 is False and 1 <=sub_choice <= len(sub_cat):
                    selected_sub_cat = sub_cat[sub_choice - 1]
                    lab_name = data['labs'][selected_category]['labs'][selected_sub_cat]
                    mail_server = data['labs'][selected_category]['labs'][selected_sub_cat]['mailserver']
                    each_info(lab_name, cat_name, nname, mail_server)
                if flag2 is False and sub_choice == 0:
                    show_labs()
                else:
                    print("Please choose correct option!")
                    flag2=True
        else:
            print("Please choose correct option!")
            flag=True

def perfrom_admin_task():
    if len(sys.argv) > 1:
        func_name = sys.argv[1]
        if func_name == "update_host_file":
            update_host_file()
        else:
            print(f"Unknown function: {func_name}")
            sys.exit(1)
    else:
        if not is_admin():
            run_as_admin("update_host_file")
        else:
            update_host_file()
        
if __name__ == "__main__":
    if not check_for_host_path:
        perfrom_admin_task()
        
    if check_ineternet_connection():
        get_lab_info()

    get_mail_server()
    update_host_file()
    show_labs()
