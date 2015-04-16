import requests
import lxml.html
import time
from datetime import datetime
import random
import os
from unidecode import unidecode
import hashlib
import shutil
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

"""
Functions for the user:
map_images(base_url,depth): Gets the links for all the images on a given set of web pages
map_pdfs(url,depth): Gets the links for all the pdfs on a given set of web pages
map_links(base_url,depth): Gets all the links for all the pages of a given website, upto a certain depth.
Recommended depth: 3 - 6 (otherwise request may time out)
"""

class Mapper:
    def __init__(self):
        self.is_https = False

    def image_save(self,img_src,file_name):
        print "saving image:"+img_src
        img_dir = "images"+file_name
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)
        os.chdir(img_dir)
        path = img_src.split("/")[-1]
        if self.is_https:
            s = self.handle_https()
            r = s.get(img_src,stream=True)
        else:
            r = requests.get(img_src, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)  
                m = hashlib.sha256()
                m.update(str(r.raw))
                with open("img_hashes.txt","a") as h:
                    h.write(path+":"+m.hexdigest()+"\n")

        os.chdir("../")


    def storing(self,links):
        print "storing started"
        print len(links)
        responses = []
        for link in links:
            if self.is_https:
                s = self.handle_https()
                responses.append(s.get(link))
            else:
                responses.append(requests.get(link))
            #time.sleep(random.randint(2,10))
        tmp_dir = "tmp"+str(datetime.now())
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        os.chdir(tmp_dir)
        hashes = []
        for r in responses:
            imgs = self.image_grab(r)
            m = hashlib.sha256()
            file_name = tmp_dir + "_".join(r.url.split("/")[-3:-1])
            for img in imgs: self.image_save(img,file_name)
            text = unidecode(r.text)
            m.update(text)
            with open(file_name,"w") as f:
                print file_name
                f.write(text)
            with open("hashes.txt","a") as h:
                h.write(file_name+":"+m.hexdigest()+"\n")
        os.chdir("../")


    def link_grab(self,url,base_url):
        """Returns all links on the page.  
        Aka all those links who include the base url in the link."""

        links = []
        if self.is_https:
            s = self.handle_https()
            r = s.get(url)
        else:
            r = requests.get(url)
        obj = lxml.html.fromstring(r.text)
        potential_links = obj.xpath("//a/@href")
        links.append(r.url)

        for link in potential_links:
            if base_url in link:
                links.append(link)
            else:
                if link.startswith("http"):
                    links.append(link)

                if base_url.endswith("/"):
                    if link.startswith("/"):
                        link = link.lstrip("/")
                        link = base_url + link
                    else:
                        link = base_url + link
                    links.append(link)
        return links

    def map_links(self,base_url,depth):
        link_list = []
        return mapper(base_url,base_url,depth,link_list)

    def mapper(self,url,base_url,depth,link_list):
        """Grabs all the links on a given set of pages, does this recursively."""
        if "https" in url or "https" in base_url:
            self.is_https = True
        if depth <= 0:
            return link_list
        links_on_page = self.link_grab(url,base_url)
        tmp = []
        for link in links_on_page:
            if not link in link_list:
                link_list.append(link)
                tmp = self.mapper(link,base_url,depth-1,link_list)
                for elem in tmp:
                    if not elem in link_list:
                        link_list.append(elem)
        return link_list

    def map_pdfs(self,url,depth):
        """Grabs all the pdfs on a given set of pages."""
        links = self.map_website(url,depth)
        pdfs = []
        for link in links:
            if ".pdf" in link:
                pdfs.append(link)
        return pdfs

    def image_grab(self,r):
        """Returns all images on the page."""        
        obj = lxml.html.fromstring(r.text)
        base = "/".join(r.url.split("/")[:3]) 
        imgs = []
        for img in obj.xpath("//img/@src"):
            if "http" in img:
                imgs.append(img)
            else:
                imgs.append(base+img)
        return imgs
                        
    def handle_https(self):
        s = requests.Session()
        s.mount('https://', MyAdapter())
        return s

#potential issue and fix: http://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred
if __name__ == "__main__":
    print "mapping stuff"
    m = Mapper()
    links = m.mapper("https://www.google.com","https://www.google.com",1,[])
    print "storing stuff"
    m.storing(links)
