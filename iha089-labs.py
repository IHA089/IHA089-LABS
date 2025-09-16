from git import Repo
import os, socket, sys, threading, multiprocessing, time
from json import load
from flask import Flask
import ssl
from werkzeug.serving import run_simple

current_lab = None
mail_enabled = True
smtp_proc = None
MailServerIHA089 = None
run_server = None

def get_venv_python(venv_path="venv"):
    if not os.path.exists(venv_path):
        print(f"Virtual environment at {venv_path} does not exist.")
        sys.exit(1)
    
    if sys.platform == "win32":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
    
    if not os.path.exists(python_path):
        print(f"Python interpreter not found in virtual environment at {python_path}.")
        sys.exit(1)
    
    return python_path


def run_with_venv(venv_path="venv"):
    try:
        python_path = get_venv_python(venv_path)
        os.execv(python_path, [python_path] + [os.path.abspath(sys.argv[0])] + sys.argv[1:])
    except Exception as e:
        print("Error re-executing in venv:", e)
        sys.exit(1)


def application(environ, start_response):
    global current_lab, mail_enabled, MailServerIHA089

    host = environ.get("HTTP_HOST", "").split(":")[0]

    if host == "iha089-labs.in" and current_lab:
        return current_lab.wsgi_app(environ, start_response)
    elif host == "mail.iha089-labs.in" and mail_enabled and MailServerIHA089:
        return MailServerIHA089.wsgi_app(environ, start_response)

    resp = b"No lab is running. Select one from the menu."
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
    return [resp]


def is_admin():
    if os.name == 'nt':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.getuid() == 0

def update_host_file():
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        os.system("certutil -addstore Root \"rootCA.pem\"")
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        print("Unknown OS")
        return
    
    with open(host_path, 'r') as ff:
        data = ff.read()
    
    if "127.0.0.1   iha089-labs.in" not in data:
        with open(host_path, 'a') as dd:
            dd.write("\n127.0.0.1   iha089-labs.in")
    if "127.0.0.1   mail.iha089-labs.in" not in data:
        with open(host_path, 'a') as dd:
            dd.write("\n127.0.0.1   mail.iha089-labs.in")

def check_for_host_path():
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        return False
    
    with open(host_path, 'r') as ff:
        data = ff.read()
    
    return (
        "127.0.0.1   iha089-labs.in" in data
        and "127.0.0.1   mail.iha089-labs.in" in data
    )

def check_internet_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8",80))
        return True
    except OSError:
        print("No internet connection")
        return False


def run_vulnerable_lab(file_path, app_name):
    global current_lab
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(app_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        flask_app = getattr(module, app_name)

        if not isinstance(flask_app, Flask):
            raise ValueError(f"The object '{app_name}' is not a Flask instance.")

        app_dir = os.path.dirname(file_path)
        flask_app.template_folder = os.path.join(app_dir, "templates")
        flask_app.static_folder = os.path.join(app_dir, "static")

        current_lab = flask_app
        print(f"\n{app_name} is now active at https://iha089-labs.in")
        print(f"\nMail Service is active at https://mail.iha089-labs.in")

    except Exception as e:
        print(f"Error running lab: {e}")

def get_lab_info():
    lab_info_url = "https://github.com/IHA089/iha089_lab_info.git"
    dirname="iha089_lab_info"

    to_path = os.path.join(os.getcwd(), dirname)
    if os.path.isdir(to_path):
        if os.name == "posix":
            os.system("rm -rf iha089_lab_info")
        elif os.name == "nt":
            os.system("rmdir /s /q \"iha089_lab_info\"")

    os.mkdir(dirname)

    try:
        print(f"\rFetching all available labs...", end="")
        Repo.clone_from(lab_info_url, to_path)
        print(f"\rfetch success{' '*20}")
    except Exception as e:
        print("Error fetching labs: "+str(e))

def check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, adf="Fetching"):
    lab_path = os.path.join(os.getcwd(), cat_name, lab_url)
    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)
        try:
            print(f"\r{adf} {lab_url} lab....", end="")
            lab_git_url = "https://github.com/IHA089/"+lab_url+".git"
            Repo.clone_from(lab_git_url, lab_path)
            print(f"\r{adf} success{' '*30}")
        except Exception as e:
            print("An error occur: "+str(e))
            sys.exit()
    else:
        version_path = os.path.join(lab_path, "version")
        try:
            with open(version_path, 'r') as file:
                data = file.read().strip()
            if version != data:
                if os.name == "posix":
                    os.system("rm -rf "+lab_path)
                elif os.name == "nt":
                    os.system("rmdir /s /q \""+lab_path+"\"")
                check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, adf="Updating")
        except FileNotFoundError:
            if os.name == "posix":
                os.system("rm -rf "+lab_path)
            elif os.name == "nt":
                os.system("rmdir /s /q \""+lab_path+"\"")
            check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, adf="Fetching")

    py_path = lab_url.replace('Lab','.py')
    ff_path = os.path.join(lab_path, py_path)

    appName = lab_url.replace('Lab','')
    run_vulnerable_lab(ff_path, app_name=appName)

    print("\n")
    print(description)
    print("Hint: "+blog_url)
    
    while True:
        user_input = input(nname).strip().lower()
        if user_input in ('stop', 'close'):
            print("Lab stopped.")
            global current_lab
            current_lab = None
            break
        else:
            print("Unknown command. Type 'stop' or 'close' to stop the lab.")


def each_info(lab_info, cat_name, nname, mailserver):
    lab_desc = lab_info['description']
    lab_url = lab_info['laburl']
    blog_url = lab_info['blogurl']
    version = lab_info['version']
    check_lab_is_present(lab_url, cat_name, nname, mailserver, version, lab_desc, blog_url)

def chech_main_lab_name(name):
    lab_path = os.path.join(os.getcwd(),name)
    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)

def show_labs():
    json_path = "iha089_lab_info/manage_labs.json"
    with open(json_path, "r") as file:
        data = load(file)

    print("Available Lab Categories:")
    categories = list(data['labs'].keys())
    for idx, category in enumerate(categories, 1):
        print(f"{idx}. >>>  {category}")
    print("\npress `ctrl+c` for exit")
    
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
                print("0. >>>  go to back")
                for idx, sub in enumerate(sub_cat, 1):
                    name = data['labs'][selected_category]['labs'][sub]['labname']
                    print(f"{idx}. >>>  {name}")
                print("\npress `ctrl+c` for exit")
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

def start_smtp_process():
    global smtp_proc, mail_enabled, run_server
    if smtp_proc and smtp_proc.is_alive():
        print("SMTP already running.")
        mail_enabled = True
        return
    smtp_proc = multiprocessing.Process(target=run_server, daemon=True)
    smtp_proc.start()
    time.sleep(0.5)
    mail_enabled = True

if __name__ == "__main__":
    if not os.path.isfile("check_venv"):
        with open("check_venv", "w") as f:
            f.write("0")
        run_with_venv("IHA089_Labs_venv")
        sys.exit()
    else:
        os.system("del check_venv") if os.name == "nt" else os.system("rm -rf check_venv")
    
    from IHA089_Mail.MailServerIHA089 import MailServerIHA089
    from IHA089_Mail.smtp_server import run_server

    if not is_admin():
        print("Please run this script with root permission")
        sys.exit()

    if not check_for_host_path():
        update_host_file()

    if check_internet_connection():
        print()
        get_lab_info()

    start_smtp_process()
    mail_enabled = True

    threading.Thread(target=show_labs, daemon=True).start()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="iha089-labs.crt", keyfile="iha089-labs.key")

    run_simple("127.0.0.1", 443, application, ssl_context=context)
