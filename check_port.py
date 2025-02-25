import socket

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

if __name__ == "__main__":
    port = 5000
    if check_port(port):
        print(f"✅ Porta {port} está aberta e respondendo")
        print(f"O servidor está rodando e configurado corretamente")
    else:
        print(f"❌ Porta {port} não está respondendo")
        print(f"O servidor pode não estar rodando ou há um problema de configuração")
