from http.server import BaseHTTPRequestHandler,HTTPServer
import socketserver
import json
import cgi
import psutil
import subprocess
import time

class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
        
    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()

	# check the url string and respond with the appropriate json blob
        if self.path == '/api/1.0/system':
            # respond with system statistics
            data = {}
            json_data = json.dumps(data)
            data['boottime'] = str(psutil.boot_time())
            data['uptime'] = str(round(time.time() - psutil.boot_time(), 2))

            self.wfile.write(json.dumps(data).encode())

        elif self.path == '/api/1.0/cpu':
            # respond with CPU statistics
            data = {}
            json_data = json.dumps(data)
            data['percent'] = str(psutil.cpu_percent())
            data['count'] = str(psutil.cpu_count())
            data['speed'] = str(psutil.cpu_freq())

            self.wfile.write(json.dumps(data).encode())

        elif self.path == '/api/1.0/network':
            # respond with network statistics
            data = {}
            json_data = json.dumps(data)
            data['inetlatency'] = ping()

            self.wfile.write(json.dumps(data).encode())
    
        elif self.path == '/api/1.0/mem':
            # respomnd with MEM statistics
            data = {}
            json_data = json.dumps(data)
            data['percent'] = str(psutil.virtual_memory()[2])

            self.wfile.write(json.dumps(data).encode())

        elif self.path == '/api/1.0/disk':
            # respond with disk statistics
            data = {}
            json_data = json.dumps(data)

            partitions = psutil.disk_partitions()
            for p in partitions:
                data[p.mountpoint] = str(psutil.disk_usage(p.mountpoint).percent) 

            self.wfile.write(json.dumps(data).encode())

        elif self.path == '/api/1.0/sensor':
            # respond with sensor statistics - hacky reliance on istats and subprocess..
            data = {}
            json_data = json.dumps(data)
            data['cputemp'] = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "cpu"]).decode("utf-8")).strip()
            data['fanspeed'] = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "fan"]).decode("utf-8")).strip()
            data['battery'] = str(subprocess.check_output(["/usr/local/bin/istats", "--no-graph", "--value-only",  "battery"]).decode("utf-8")).strip()

            self.wfile.write(json.dumps(data).encode())

        else:
            # unknown request, respond with enabled commands
            data = {}
            json_data = json.dumps(data)
            data['/api/1.0/system'] = 'get system statistics'
            data['/api/1.0/cpu'] = 'get cpu statistics'
            data['/api/1.0/mem'] = 'get mem statistics'
            data['/api/1.0/disk'] = 'get disk statistics'
            data['/api/1.0/sensor'] = 'get sensor statistics'
            data['/api/1.0/network'] = 'get network statistics'

            self.wfile.write(json.dumps(data).encode())

def ping(server='8.8.8.8', count=1, wait_sec=1):
    """

    :rtype: dict or None
    """
    cmd = "ping -c {} -W {} {}".format(count, wait_sec, server).split(' ')
    try:
        output = subprocess.check_output(cmd).decode().strip()
        lines = output.split("\n")
        total = lines[-2].split(',')[3].split()[1]
        loss = lines[-2].split(',')[2].split()[0]
        timing = lines[-1].split()[3].split('/')
        
        # just return the avg latency for this routine
        return timing[1]        

    except Exception as e:
        print(e)
        return None

def run(server_class=HTTPServer, handler_class=Server, port=8008):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    print ('Starting httpd on port %d...' % port)
    httpd.serve_forever()
    
if __name__ == "__main__":
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
