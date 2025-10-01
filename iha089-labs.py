from git import Repo
import mimetypes
from jinja2 import Environment, FileSystemLoader
import os, socket, sys, threading, multiprocessing, time, json
from json import load
from flask import Flask, render_template, jsonify, request
import ssl
from werkzeug.serving import run_simple

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

def serve_static(environ, start_response):
    path = environ.get("PATH_INFO", "")
    filepath = path.lstrip("/")

    if ".." in filepath or filepath.startswith("/"):
        start_response("403 Forbidden", [("Content-Type", "text/plain")])
        return [b"Forbidden"]

    full_path = f"{STATIC_DIR}/{filepath[len('static/'):]}"  
    try:
        with open(full_path, "rb") as f:
            content = f.read()
        content_type, _ = mimetypes.guess_type(full_path)
        content_type = content_type or "application/octet-stream"
        start_response("200 OK", [("Content-Type", content_type), ("Content-Length", str(len(content)))])
        return [content]
    except FileNotFoundError:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]

def url_for(endpoint, **values):
    if endpoint == "static":
        filename = values.get("filename", "")
        return f"/static/{filename}"
    return "/"

def render_template(template_name, environ=None, **kwargs):
    class DummyRequest:
        def __init__(self, environ):
            self.path = environ.get("PATH_INFO", "/") if environ else "/"
            self.method = environ.get("REQUEST_METHOD", "GET") if environ else "GET"
            self.host = environ.get("HTTP_HOST", "") if environ else ""

    if environ:
        kwargs['request'] = DummyRequest(environ)

    kwargs['url_for'] = lambda endpoint, **values: f"/static/{values.get('filename','')}" if endpoint == "static" else "/"

    template = env.get_template(template_name)
    return template.render(**kwargs).encode("utf-8")


def get_lab_data():
    json_path = os.path.join(os.getcwd(), "iha089_lab_info", "manage_labs.json")
    try:
        with open(json_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading lab data: {e}")
        return None

def run_with_venv(venv_path="venv"):
    try:
        python_path = get_venv_python(venv_path)
        os.execv(python_path, [python_path] + [os.path.abspath(sys.argv[0])] + sys.argv[1:])
    except Exception as e:
        print("Error re-executing in venv:", e)
        sys.exit(1)

def stop_lab():
    global current_lab
    remove_subdomain(current_lab.lab_name)
    current_lab = None

def application(environ, start_response):
    global current_lab, mail_enabled, MailServerIHA089

    host = environ.get("HTTP_HOST", "").split(":")[0]
    path = environ.get("PATH_INFO", "/")
    

    if host == "mail.iha089-labs.in" and mail_enabled and MailServerIHA089:
        return MailServerIHA089.wsgi_app(environ, start_response)
    
    if host == "iha089-labs.in":
        if path.startswith("/static/"):
            return serve_static(environ, start_response)
        lab_data = get_lab_data()

        if path == "/":
            resp = render_template("index.html", environ=environ)
            start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
            return [resp]

        if path == "/labs":
            if lab_data:
                global current_lab
                goto_url=""
                if current_lab == None:
                    current_running_lab=""
                    current_running_lab_url=""
                else:
                    current_running_lab=current_lab.real_name
                    try:
                        goto_url = f"https://iha089-labs.in/labs/{current_lab.cat_name}/{current_lab.lbname}"
                    except:
                        goto_url = ""
                    current_running_lab_url=f"https://{current_running_lab}.iha089-labs.in"
                resp = render_template("labs.html", environ=environ, labs=lab_data['labs'], lb_path="/labs/", cat_type="Category", cat_url="", current_running_lab=current_running_lab, current_running_lab_url=current_running_lab_url, goto_url=goto_url)
                start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
                return [resp]
            resp = b"Error loading labs."
            start_response("500 Internal Server Error", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
            return [resp]

        if path.startswith("/labs/"):
            parts = path.strip("/").split("/")

            if len(parts) == 2: 
                category = parts[1]
                category_labs = lab_data['labs'].get(category) if lab_data else None
                cat_name = category_labs.get('labname', 'Category') if category_labs else category
                if category_labs:
                    goto_url=""
                    if current_lab == None:
                        current_running_lab=""
                        current_running_lab_url=""
                    else:
                        current_running_lab=current_lab.real_name
                        try:
                            goto_url = f"https://iha089-labs.in/labs/{current_lab.cat_name}/{current_lab.lbname}"
                        except:
                            goto_url = ""
                        current_running_lab_url=f"https://{current_running_lab}.iha089-labs.in"
                    resp = render_template("labs.html", environ=environ, labs=category_labs['labs'], lb_path=f"/labs/{category}/", cat_type=cat_name, cat_url=category, current_running_lab=current_running_lab, current_running_lab_url=current_running_lab_url, goto_url=goto_url)
                    start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
                    return [resp]
                resp = b"Category not found."
                start_response("404 Not Found", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
                return [resp]

            if len(parts) == 3:  
                category, lab_name = parts[1], parts[2]
                lab_info = lab_data['labs'].get(category, {}).get('labs', {}).get(lab_name) if lab_data else None
                if lab_info:
                    goto_url=""
                    if current_lab == None:
                        current_running_lab=""
                    else:
                        current_running_lab=current_lab.real_name
                        try:
                            goto_url = f"https://iha089-labs.in/labs/{current_lab.cat_name}/{current_lab.lbname}"
                        except:
                            goto_url = ""
                    lab1_name = lab_data['labs'].get(category, {}).get('labname', 'Category')
                    lab2_name = lab_info.get('labname', 'Lab')
                    resp = render_template("slabs.html", environ=environ, labs=lab_info, lab1_url=category, lab2_url=lab_name, lab1_name=lab1_name, lab2_name=lab2_name, current_running_lab=current_running_lab, goto_url=goto_url)
                    start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
                    return [resp]
                resp = b"Lab not found."
                start_response("404 Not Found", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
                return [resp]

            if len(parts) == 4 and parts[3] == "start":  
                category, lab_name = parts[1], parts[2]
                lab_info = lab_data['labs'].get(category, {}).get('labs', {}).get(lab_name) if lab_data else None
                if not lab_info:
                    resp = b"Lab not found."
                    start_response("404 Not Found", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
                    return [resp]

                cat_name = lab_data['labs'].get(category, {}).get('name', category)
                nname = f"\nIHA089-LABS/{cat_name}#>"
                mailserver = lab_info.get('mailserver', False)
                try:
                    stop_lab()
                except:
                    pass
                each_info(lab_info, cat_name, nname, mailserver, category, lab_name)

                resp = json.dumps({"url": f"https://{lab_name.lower()}.iha089-labs.in", "name": lab_name}).encode("utf-8")
                start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(resp)))])
                return [resp]

        if path == "/stop":
            stop_lab()
            resp = b"Lab stopped."
            start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
            return [resp]

        if path == "/acceptable":
            resp = render_template("acceptable.html")
            start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
            return [resp]

        if path == "/term":
            resp = render_template("term.html")
            start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
            return [resp]

        if path == "/privacy":
            resp = render_template("privacy.html")
            start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(resp)))])
            return [resp]

        resp = b"404 - Page not found"
        start_response("404 Not Found", [("Content-Type", "text/plain"), ("Content-Length", str(len(resp)))])
        return [resp]

    if current_lab and host == f"{current_lab.lab_name}.iha089-labs.in":
        return current_lab.wsgi_app(environ, start_response)

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

def add_subdomain(subdomain_name):
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        print("Unknown OS")
        return
    
    with open(host_path, 'a') as ff:
        ff.write(f"\n127.0.0.1   {subdomain_name}.iha089-labs.in")
    
def remove_subdomain(subdomain_name):
    if os.name == "posix":
        host_path = "/etc/hosts"
    elif os.name == "nt":
        host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    else:
        print("Unknown OS")
        return
    
    with open(host_path, 'r') as ff:
        lines = ff.readlines()
    
    with open(host_path, 'w') as ff:
        for line in lines:
            if f"{subdomain_name}.iha089-labs.in" not in line:
                if line != "\n":
                    ff.write(line)

def run_vulnerable_lab(file_path, category, lab_name, app_name):
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

        flask_app.lab_name = app_name.lower()
        flask_app.real_name = app_name
        flask_app.cat_name = category
        flask_app.lbname = lab_name
        current_lab = flask_app
        add_subdomain(flask_app.lab_name)

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

def check_for_cat_path(cat_name):
    lab_path = os.path.join(os.getcwd(), cat_name)
    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)

def check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, category, lab_name, adf="Fetching"):
    lab_path = os.path.join(os.getcwd(), cat_name, lab_url)
    check_for_cat_path(cat_name)
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
                check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, category, lab_name, adf="Updating")
        except FileNotFoundError:
            if os.name == "posix":
                os.system("rm -rf "+lab_path)
            elif os.name == "nt":
                os.system("rmdir /s /q \""+lab_path+"\"")
            check_lab_is_present(lab_url, cat_name, nname, mailserver, version, description, blog_url, category, lab_name, adf="Fetching")

    py_path = lab_url.replace('Lab','.py')
    ff_path = os.path.join(lab_path, py_path)

    appName = lab_url.replace('Lab','')
    try:
        module_path = os.path.join(lab_path, "modules.txt")
        load_module(module_path)
    except Exception as e:
        pass 

    run_vulnerable_lab(ff_path, category, lab_name, app_name=appName)

def each_info(lab_info, cat_name, nname, mailserver, category, lab_name):
    lab_desc = lab_info['description']
    lab_url = lab_info['laburl']
    blog_url = lab_info['blogurl']
    version = lab_info['version']
    check_lab_is_present(lab_url, cat_name, nname, mailserver, version, lab_desc, blog_url, category, lab_name)

def chech_main_lab_name(name):
    lab_path = os.path.join(os.getcwd(),name)
    if not os.path.isdir(lab_path):
        os.mkdir(lab_path)

def start_smtp_process():
    global smtp_proc, mail_enabled, run_server
    if smtp_proc and smtp_proc.is_alive():
        mail_enabled = True
        return
    smtp_proc = multiprocessing.Process(target=run_server, daemon=True)
    smtp_proc.start()
    time.sleep(0.5)
    mail_enabled = True

def is_running_in_venv(venv_name="IHA089_Labs_venv"):
    return (sys.prefix != sys.base_prefix) and (venv_name in sys.prefix)



if __name__ == "__main__":
    VENV_NAME = "IHA089_Labs_venv"
    if not is_running_in_venv(VENV_NAME):
        try:
            run_with_venv(VENV_NAME) 
        except Exception as e:
            print(f"Failed to re-execute in venv: {e}")
            sys.exit(1)
        sys.exit(0) 

    print(f"Running inside virtual environment: {VENV_NAME}")
    env = Environment(loader=FileSystemLoader("templates"))
    STATIC_DIR = "static"
    from sec_bas import load_module
    current_lab = None
    mail_enabled = True
    smtp_proc = None
    MailServerIHA089 = None
    run_server = None
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

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="iha089-labs.crt", keyfile="iha089-labs.key")

    print("Access URL::: https://iha089-labs.in")
    run_simple("127.0.0.1", 443, application, ssl_context=context)
