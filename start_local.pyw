"""Double-click on Windows to start the local site without PowerShell."""
import json
import os
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

URL='http://127.0.0.1:8000'

def main():
    # Windows' windowless Python has no console streams for HTTP request logs.
    if sys.stdout is None:
        sys.stdout=open(os.devnull,'w')
    if sys.stderr is None:
        sys.stderr=open(os.devnull,'w')
    try:
        with urlopen(URL+'/api/sites',timeout=2) as response:
            existing=json.load(response)
        if 'sites' in existing and 'species' in existing:
            webbrowser.open(URL)
            return
    except Exception:
        pass
    from app import Handler
    try:
        server=ThreadingHTTPServer(('127.0.0.1',8000),Handler)
    except OSError:
        from tkinter import messagebox
        messagebox.showerror('TidePool Explorer','Port 8000 is already in use. Close the other local server and try again.')
        return
    threading.Timer(0.5,lambda:webbrowser.open(URL)).start()
    server.serve_forever()

if __name__=='__main__':
    main()
