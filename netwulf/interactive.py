# -*- coding: utf-8 -*-
"""
This module provides the necessary functions to start up a local
HTTP server and open an interactive d3-visualization of a network.
"""
from __future__ import print_function

import os
import sys

import http.server
import webbrowser
import time
import threading

import shutil

import netwulf as wulf

import json
from distutils.dir_util import copy_tree

import networkx as nx

def mkdirp_customdir(directory='~/.netwulf/'):
    """simulate `mkdir -p` functionality"""

    directory = os.path.abspath(os.path.expanduser(directory))
    if not os.path.exists(directory):
        os.makedirs(directory)


html_source_path = os.path.join(wulf.__path__[0], 'js')


def _make_and_get_directory(path):
    """Simulate ``mkdir -p`` and return the path of the repository"""
    directory, _ = os.path.split(
        os.path.abspath(os.path.expanduser(path))
    )
    mkdirp_customdir(directory)
    return directory


def prepare_visualization_directory():
    """Move all files from the netwulf/js directory to ~/.netwulf"""
    src = html_source_path
    dst = os.path.abspath(os.path.expanduser("~/.netwulf/"))

    # always copy source files to the subdirectory
    copy_tree(src, dst)


class StoppableHTTPServer(http.server.HTTPServer):
    """Taken from https://stackoverflow.com/questions/268629/how-to-stop-basehttpserver-serve-forever-in-a-basehttprequesthandler-subclass """

    def __init__(self, server_address, handler, subfolder):
        http.server.HTTPServer.__init__(self, server_address, handler)
        self.subfolder = subfolder

        while subfolder.endswith('/'):
            subfolder = subfolder[:-1]

        self.subjson = subfolder + '_config.json'

    def run(self):
        try:
            self.serve_forever()
        except OSError:
            pass

    def stop_this(self):
        # Clean-up server (close socket, etc.)
        print('was asked to stop the server')
        self.server_close()

        # try:
        if os.path.exists(self.subjson):
            os.remove(self.subjson)
        # except
        if os.path.exists(self.subfolder):
            try:
                # os.rmdir(self.subfolder)
                shutil.rmtree(self.subfolder)
            except FileNotFoundError as e:
                raise e

        # os.chdir(self.cwd)
        print('deleted all files')

    # def __del__(self):
    #    self.stop_this()


def visualize(network,
              port=9853):
    """
    Visualize a network interactively using Ulf Aslak's d3 web app.
    """

    path = "~/.netwulf/"
    web_dir = os.path.abspath(os.path.expanduser(path))

    # copy the html and js files for the visualizations
    prepare_visualization_directory()

    # create a json-file based on the current time
    filename = "tmp_{:x}".format(int(time.time()*1000)) + ".json"

    with open(os.path.join(web_dir, filename),'w') as f:
        json.dump(nx.node_link_data(network), f)

    # change directory to this directory
    print("changing directory to", web_dir)
    print("starting server here ...", web_dir)
    cwd = os.getcwd()
    os.chdir(web_dir)

    server = StoppableHTTPServer(("127.0.0.1", port),
                                 http.server.SimpleHTTPRequestHandler,
                                 web_dir,
                                 )

    # ========= start server ============
    thread = threading.Thread(None, server.run)
    thread.start()

    webbrowser.open("http://localhost:"+str(port)+"/?data=" + filename)

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        # thread.join()
        print('stopping server ...')
        server.stop_this()
        # thread.join()

    # time.sleep(1)

    print('changing directory back to', cwd)

    os.chdir(cwd)


if __name__ == "__main__":
    # download_d3()
    G = nx.fast_gnp_random_graph(100,0.1)
    visualize(G)