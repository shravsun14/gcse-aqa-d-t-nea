import os # To interact with the operating system such as command ping
import socket # To create network connections (needed for DNS server)
import threading # Allows to run tasks in background
import subprocess # Allows to run shell commands (e.g. nmcli)
import time # Handles delays by providing an interval
import sys #  To kill the script so that no resources are wasted if internet is present
from flask import Flask, request, redirect, render_template # Necessary components from Flask library to run hotspot server

portal_ip = '10.42.0.1' # Static IP for Pi use when hotspot is on
hotspot_name = 'Smart Plant Feeder' # Name of hotspot

app = Flask(__name__) # Starts the Flask application

# --- AI Generated Start ---
class DHCPServer:
    def __init__(self):
        # We use AF_INET (IPv4) and SOCK_DGRAM (UDP) for the socket type.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # SO_BROADCAST: Allows us to send packets to '255.255.255.255'
        # This is required because the client doesn't have an IP address yet.
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # SO_REUSEADDR: Allows the script to restart immediately without waiting
        # for the OS to release the port (prevents 'Address already in use' errors).
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to Port 67: The standard UDP port for DHCP Servers.
        self.sock.bind(('', 67))
        print('DHCP Server listening on port 67...')

    def run(self):
        while True: # Loop to keep the thread alive
            try:
                # recvfrom(1024) waits for incoming data.
                # It returns the raw data bytes and the address of the sender.
                data, addr = self.sock.recvfrom(1024) 
                self.handle_packet(data)
            except Exception as e: # Error handling to prevent server crash due to bad packets
                print('DHCP Error:', e)

    def handle_packet(self, data):
        # Basic validation
        if len(data) < 240: return
        
        # 1. PARSE MESSAGE TYPE (Option 53)
        # We need to detect if the phone is saying "Hello" (DISCOVER) or "I want this" (REQUEST)
        msg_type = 1 # Default to DISCOVER
        try:
            # DHCP Options start after the magic cookie (byte 240)
            opts = data[240:]
            i = 0
            while i < len(opts):
                code = opts[i]
                if code == 255: break # End of options
                if code == 0: # Padding
                    i += 1
                    continue
                length = opts[i+1]
                if code == 53: # Found Message Type!
                    msg_type = opts[i+2]
                    break
                i += 2 + length
        except:
            pass

        # 2. DECIDE REPLY
        # If Client says DISCOVER (1) -> We say OFFER (2)
        # If Client says REQUEST (3)  -> We say ACK (5)
        # This fixes the "Disconnect Loop" on Macs/iPhones
        reply_type = 2 if msg_type == 1 else 5
        
        # 3. BUILD PACKET
        xid = data[4:8]      
        mac = data[28:34]    
        
        packet = b''
        packet += b'\x02'                     # Boot Reply
        packet += b'\x01'                     # Ethernet
        packet += b'\x06'                     # HW Len
        packet += b'\x00'                     # Hops
        packet += xid                         # Transaction ID
        packet += b'\x00\x00'                 # Seconds
        packet += b'\x00\x00'                 # Flags
        packet += b'\x00\x00\x00\x00'         # Client IP
        packet += socket.inet_aton('10.42.0.50') # Your IP
        packet += socket.inet_aton('10.42.0.1')  # Server IP
        packet += b'\x00\x00\x00\x00'         # Gateway IP
        packet += mac + b'\x00' * 10          # Client MAC
        packet += b'\x00' * 192               # Padding
        packet += b'\x63\x82\x53\x63'         # Magic Cookie

        # Option 53: Message Type (Dynamic now!)
        packet += b'\x35\x01' + bytes([reply_type])
        
        # Required Options
        packet += b'\x36\x04' + socket.inet_aton('10.42.0.1') # Server ID
        packet += b'\x33\x04\x00\x01\x51\x80' # Lease Time
        packet += b'\x01\x04\xff\xff\xff\x00' # Subnet Mask
        packet += b'\x03\x04' + socket.inet_aton('10.42.0.1') # Router
        packet += b'\x06\x04' + socket.inet_aton('10.42.0.1') # DNS
        packet += b'\xff'                     # End

        self.sock.sendto(packet, ('255.255.255.255', 68))
# --- AI Generated End ---

def check_internet():
    time.sleep(30)
    response = os.system('ping -c 1 8.8.8.8 > /dev/null 2>&1') # Sends command to Google's DNS servers to check for internet
    # Keeps console clean by preventing logs
    if response == 0: # 0 means successful, non-zero means failure)
        return True
    else:
        return False

def start_hotspot():
    print('No internet, starting hotspot...')
    # 1. Kill any "Ghost" DHCP servers running in the background
    subprocess.run('sudo killall dnsmasq', shell=True)
    # 2. Delete old connection
    subprocess.run('nmcli con delete "' + hotspot_name + '"', shell=True)
    # 3. Create the connection with MANUAL mode immediately (All in one command)
    # This prevents the OS from ever thinking it should run DHCP.
    cmd = (
        'nmcli con add type wifi ifname wlan0 '
        'con-name "' + hotspot_name + '" '
        'autoconnect no '
        'ssid "' + hotspot_name + '" '
        '802-11-wireless.mode ap '
        '802-11-wireless.band bg '
        'ipv4.method manual '
        'ipv4.addresses 10.42.0.1/24 '
        'ipv4.gateway 10.42.0.1'
    )
    subprocess.run(cmd, shell=True)
    # 4. Start it
    subprocess.run('nmcli con up "' + hotspot_name + '"', shell=True)
    # 5. Wait for hardware
    print("Waiting 5 seconds for Wi-Fi to settle...")
    time.sleep(5)

def get_networks():
    try:
        output = subprocess.check_output('nmcli -t -f SSID dev wifi', shell=True)
        # List Wi-Fi networks, -t = clean output, -f = SSID only
        output_str = output.decode('utf-8') # Decode bytes into string
        networks = output_str.split('\n') # Split string into list
        clean_list = []
        for net in networks: # Clean outputs, remove duplicates & SSID
            if net != '' and net != hotspot_name:
                if net not in clean_list:
                    clean_list.append(net)

        return clean_list
    except Exception as e:
        print('Error scanning networks: ' + str(e))
        return []

def connect_to_wifi(ssid, password):
    print('Connecting to', ssid + '...')
    subprocess.run('nmcli con delete "' + hotspot_name + '"', shell=True)
    time.sleep(5)
    cmd = ('nmcli dev wifi connect "' + ssid + '" password "' + password + '" '
	'autoconnect yes '
	'autoconnect-priority 100'
    )
    # Construct command to connect new Wi-Fi using the given SSID
    result = subprocess.run(cmd, shell=True)
    # Execute the terminal command
    if result.returncode == 0:
        print('Successfully connected to ' + ssid, 'rebooting to apply changes.')
        time.sleep(5)
        subprocess.run('reboot', shell=True)
    else:
        print('Connection failed. Reverting to hotspot.')
        start_hotspot()

def connect_to_wifi(ssid, password):
    print('Connecting to ' + ssid + '...')
    subprocess.run('nmcli con down "' + hotspot_name + '"', shell=True)
    time.sleep(2)
    cmd = 'nmcli dev wifi connect "' + ssid + '" password "' + password + '"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print('Successfully connected to ' + ssid)
        print('Setting network priority to 100...')
        priority_cmd = 'nmcli connection modify "' + ssid + '" connection.autoconnect yes connection.autoconnect-priority 100'
        subprocess.run(priority_cmd, shell=True)
        print('Rebooting in 5 seconds to apply changes...')
        subprocess.run('sudo nmcli con delete "' + hotspot_name + '"', shell=True)
        time.sleep(5)
        subprocess.run('sudo reboot', shell=True)
    else:
        print('CRITICAL: Connection failed!')
        print('Error Code: ' + str(result.returncode))
        print('Error Message: ' + result.stderr) 
        print('Reverting to hotspot...')
        start_hotspot()

def build_dns_response(data):
    packet = b''
    packet += data[:2] + b'\x81\x80'
    packet += data[4:6] + data[4:6] + b'\x00\x00\x00\x00'
    packet += data[12:]
    packet += b'\xc0\x0c'
    packet += b'\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
    ip_parts = portal_ip.split('.')
    packet += bytes([int(x) for x in ip_parts])
    return packet

def run_dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 53))
    print('DNS Server running on port 53...')
    while True:
        try:
            data, addr = sock.recvfrom(512)
            response = build_dns_response(data)
            sock.sendto(response, addr)
        except Exception as e:
            print('DNS Error: ' + str(e))

@app.route('/', methods=['GET'])
def home(): # Send list of Wi-Fis, return and render HTML template
    wifi_list = get_networks()
    return render_template('login.html', ssids=wifi_list)

@app.route('/connect', methods=['POST']) # Handle form submission
def handle_login(): # Extract information which user provides
    ssid = request.form['ssid']
    password = request.form['password']
    t = threading.Thread(target=connect_to_wifi, args=(ssid, password))
    t.start()
    return '<h1>Connecting...</h1><p>The device is rebooting to switch networks. Please wait 30 seconds.</p>'

@app.route('/<path:path>')
def catch_all(path): # Prevents users from going any other site and redirects back to captive
    return redirect('http://' + portal_ip + '/', code=302)

if __name__ == '__main__':
    time.sleep(20)
    if check_internet() == False: # Check if internet is true
        try:
            nmcli_output = subprocess.check_output('nmcli -t -f NAME con show', shell=True).decode()
            saved_nmcli = nmcli_output.strip().split('\n')
            for con in saved_nmcli:
                if con != hotspot_name and con != "":
                    subprocess.run('nmcli con up "' + con + '"', shell=True)
                    time.sleep(10)
                    check_internet()
                    if check_internet() == True:
                        print('Connection successful for', con)
                        break
        except:
            pass
    if check_internet() == True:
        print('Internet is connected. Running normal code...')
        sys.exit(0)
    else:
        start_hotspot() # Start hotspot due to lack of internet
        dns_thread = threading.Thread(target=run_dns_server) # Runs DNS server in background
        dns_thread.daemon = True
        dns_thread.start()
        dhcp = DHCPServer() # Star
        dhcp_thread = threading.Thread(target=dhcp.run)
        dhcp_thread.daemon = True
        dhcp_thread.start()
        print('Starting Web Portal on ' + portal_ip)
        app.run(host='0.0.0.0', port=80, debug=False) # Run teh FLask server on port 80
