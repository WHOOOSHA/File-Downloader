from threading  import Lock, Barrier, Thread
from time import sleep
import urllib.parse
import http.client
import math
import sys
import os

downloaded_bytes = 0
content_length = 0
barrier = Barrier(2)
lock = Lock()

def parse_url(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path or '/'
    name = os.path.basename(path) or "downloaded_file"
    query = parsed_url.query
    is_https = parsed_url.scheme == 'https'
    

    if query:
        path += '?' + query

    return domain, path, name, is_https

def download(url):
    domain, path, name, is_https = parse_url(url)

    if is_https:  
        conn = http.client.HTTPSConnection(domain)
    else: 
        conn = http.client.HTTPConnection(domain)

    conn.request("GET", path)
    response = conn.getresponse()

    while response.status in (302, 301):
        new_url = response.getheader('Location')
        print(f'Redirecting to: {new_url}')
        domain, path, name, is_https = parse_url(new_url)

        conn.close()

        if is_https:  
            conn = http.client.HTTPSConnection(domain)
        else: 
            conn = http.client.HTTPConnection(domain)

        conn.request("GET", path)
        response = conn.getresponse()

    
    if response.status == 200:
        global content_length
        content_length = response.getheader('Content-Length') 
        global downloaded_bytes
        print(f"started download file: {name}")
        barrier.wait()
        with open(name, 'wb') as f:
            for i in range(math.ceil(int(content_length) / 1024)):
                buff = response.read(1024)
                f.write(buff)
                lock.acquire()
                downloaded_bytes += len(buff)
                lock.release()

        print("File downloaded successfully.")
    else:
        print(response.status, response.reason)

    conn.close()
        
def get_progress():
    barrier.wait()
    while True:
        lock.acquire()
        print(f"Downloaded {downloaded_bytes} bytes out of {content_length}")
        lock.release()
        sleep(1)




if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
    else:
        print("Ошибка указания ссылки")
        sys.exit(1)

    progress = Thread(target=get_progress, daemon = True)
    progress.start()
    download(url)
