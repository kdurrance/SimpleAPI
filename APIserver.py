from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import psutil
import subprocess
import time
import threading

# global variables
global_api_key = ''
global_version = '1.0'
global_name = 'Host information API'
global_network_rates = {}
global_network_latency = '?'
global_cpu_temp = ''
global_fan_speed = ''
global_battery_status = ''

class Server(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
        
    # GET
    def do_GET(self):
        self._set_headers()

        # validate the api_key value
        authorised = authenticate(self.path)

        if not authorised == True:
            # bad api_key passed in url
            data = {}
            data['unauthorised'] = 'bad api_key'
            data['version'] = global_version
            data['product'] = global_name 

            self.wfile.write(json.dumps(data).encode())
 
        else:
            # valid API key, process the request
            # remove the query string
            requesturl = self.path.split('?',maxsplit=1)[0]

            # check the request string and respond with the appropriate json blob
            if requesturl == '/api/1.0/system':
                # respond with system statistics
                data = {}
                data['boottime'] = str(psutil.boot_time())
                data['uptime'] = str(round(time.time() - psutil.boot_time(), 2))

                self.wfile.write(json.dumps(data).encode())

            elif requesturl == '/api/1.0/cpu':
                # respond with CPU statistics
                data = {}
                data['percent'] = str(psutil.cpu_percent())
                data['count'] = str(psutil.cpu_count())
                data['speed'] = str(psutil.cpu_freq())

                self.wfile.write(json.dumps(data).encode())

            elif requesturl == '/api/1.0/network':
                # respond with network statistics
                data = {}
                data['inetlatency'] = global_network_latency
                data['bandwidth'] = global_network_rates

                self.wfile.write(json.dumps(data).encode())
    
            elif requesturl == '/api/1.0/mem':
                # respomnd with MEM statistics
                data = {}
                data['percent'] = str(psutil.virtual_memory()[2])

                self.wfile.write(json.dumps(data).encode())

            elif requesturl == '/api/1.0/disk':
                # respond with disk statistics
                data = {}

                partitions = psutil.disk_partitions()
                for p in partitions:
                    data[p.mountpoint] = str(psutil.disk_usage(p.mountpoint).percent) 

                self.wfile.write(json.dumps(data).encode())

            elif requesturl == '/api/1.0/sensor':
                # respond with sensor statistics - hacky reliance on istats and subprocess..
                data = {}
                data['cputemp'] = global_cpu_temp
                data['fanspeed'] = global_fan_speed
                data['battery'] = global_battery_status

                self.wfile.write(json.dumps(data).encode())

            else:
                # unknown request, respond with enabled commands
                data = {}
                data['/api/1.0/system'] = 'get system statistics'
                data['/api/1.0/cpu'] = 'get cpu statistics'
                data['/api/1.0/mem'] = 'get mem statistics'
                data['/api/1.0/disk'] = 'get disk statistics'
                data['/api/1.0/sensor'] = 'get sensor statistics'
                data['/api/1.0/network'] = 'get network statistics'
                data['version'] = global_version
                data['product'] = global_name 

                self.wfile.write(json.dumps(data).encode())

def authenticate(url):
    # routine to verify the query string against the configured api_key
    import urllib.parse as urlparse
    from urllib.parse import parse_qs
    parsed = urlparse.urlparse(url)

    query = parse_qs(parsed.query)
    if 'api_key' in query:
        if global_api_key == query['api_key'][0]:
            return True
        else:
            return False
    else:
       return False

def getapikey():
    # routine to get the api_key, if none exists then create one
    import os, secrets
    global global_api_key

    # expects the api.key file to be in same directory as this script
    keyfile = os.path.dirname(os.path.abspath(__file__)) + '/api.key'
    print ('api_key file: ' + keyfile)
    if not os.path.exists(keyfile):
        # create an api.key file
        api_key = secrets.token_urlsafe(16)
        with open(keyfile, 'wt') as key_file:
            key_file.write(api_key)
            key_file.close()

    with open(keyfile, 'r') as key_file:
        global_api_key = key_file.read().replace('\n', '').strip()
        key_file.close()

def cputemp():
    global global_cpu_temp
    while True:
        global_cpu_temp = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "cpu"]).decode("utf-8")).strip()
        time.sleep(30)

def fanspeed():
    global global_fan_speed
    while True:
        global_fan_speed = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "fan"]).decode("utf-8")).strip()
        time.sleep(30)

def batterystatus():
    global global_battery_status
    while True:
        global_battery_status = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "battery"]).decode("utf-8")).strip()
        time.sleep(30)

def ping(server='8.8.8.8', count=3, wait_time=1):
    global global_network_latency
    cmd = "ping -c {} -W {} {}".format(count, wait_time, server).split(' ')

    while True:
        try:
            output = subprocess.check_output(cmd).decode().strip()
            lines = output.split("\n")
            total = lines[-2].split(',')[3].split()[1]
            loss = lines[-2].split(',')[2].split()[0]
            timing = lines[-1].split()[3].split('/')
          
            # just return the avg latency for this routine
            latency = timing[1]
            global_network_latency = timing[1]
            time.sleep(3)

        except Exception as e:
            print(e)

def calc_ul_dl(dt=3, interface='en0'):
    global global_network_rates
    t0 = time.time()
    counter = psutil.net_io_counters(pernic=True)[interface]
    tot = (counter.bytes_sent, counter.bytes_recv)

    while True:
        last_tot = tot
        time.sleep(dt)
        counter = psutil.net_io_counters(pernic=True)[interface]
        t1 = time.time()
        tot = (counter.bytes_sent, counter.bytes_recv)
        ul, dl = [(now - last) / (t1 - t0) / 1024 * 8
                  for now, last in zip(tot, last_tot)]

        global_network_rates['traffic_dl_kbits_sec'] = dl
        global_network_rates['traffic_ul_kbits_sec'] = ul
        t0 = time.time()

def run(server_class=HTTPServer, handler_class=Server, port=8008, apikey=''):
    # kick off the network monitoring thread(s)
    global global_network_rates

    # Create the ul/dl thread
    tbandwidth = threading.Thread(target=calc_ul_dl)
    tbandwidth.daemon = True
    tbandwidth.start()

    # Create the ping thread
    tping = threading.Thread(target=ping)
    tping.daemon = True
    tping.start()

    # Create the cputemp thread
    tcputemp = threading.Thread(target=cputemp)
    tcputemp.daemon = True
    tcputemp.start()

    # Create the fanspeed thread
    tfan = threading.Thread(target=fanspeed)
    tfan.daemon = True
    tfan.start()

    # Create the battery thread
    tbattery = threading.Thread(target=batterystatus)
    tbattery.daemon = True
    tbattery.start()

    # set the api_key for authentication
    getapikey()

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    print ('Starting httpd on port:' + str(port))
    print ('Authenticated with api_key:' +  global_api_key)
    print ('Help endpoint: http://localhost:' + str(port) + '/api/1.0/help?api_key=' + global_api_key) 
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
        
    else:
        run()
