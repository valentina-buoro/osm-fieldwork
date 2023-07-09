#!/usr/bin/python3
#
# Copyright (C) 2020, 2021, 2022, 2023 Humanitarian OpenstreetMap Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import logging
from datetime import datetime
from osm_fieldwork.convert import Convert, escape
from osm_fieldwork.xlsforms import xlsforms_path
import xmltodict
import argparse
from sys import argv
import os
import pathlib

# Intantiate logger
log = logging.getLogger(__name__)


class OsmFile(object):
    """OSM File output"""

    def __init__(self,
                 filespec: str = None,
                 options: dict = dict(),
                 outdir: str = "/tmp/"
                 ):
        self.options = options
        # Read the config file to get our OSM credentials, if we have any
        # self.config = config.config(self.options)
        self.version = 3
        self.visible = "true"
        self.osmid = -1
        # Open the OSM output file
        self.file = None
        if filespec is not None:
            self.file = open(filespec, "w")
            # self.file = open(filespec + ".osm", 'w')
            logging.info("Opened output file: " + filespec)
        self.header()
        # logging.error("Couldn't open %s for writing!" % filespec)

        # This is the file that contains all the filtering data
        # self.ctable = convfile(self.options.get('convfile'))
        # self.options['convfile'] = None
        # These are for importing the CO addresses
        self.full = None
        self.addr = None
        # decrement the ID
        self.start = -1
        # path = xlsforms_path.replace("xlsforms", "")
        self.convert = Convert()
        self.data = dict()

    def __del__(self):
        log.debug("Closing output file")
        self.footer()

    def isclosed(self):
        return self.file.closed

    def header(self):
        if self.file is not None:
            self.file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            # self.file.write('<osm version="0.6" generator="osm-fieldowrk 0.3" timestamp="2017-03-13T21:43:02Z">\n')
            self.file.write('<osm version="0.6" generator="osm-fieldwork 0.3">\n')
            self.file.flush()

    def footer(self):
        # logging.debug("FIXME: %r" % self.file)
        if self.file is not None:
            self.file.write("</osm>\n")
            self.file.flush()
            if self.file is False:
                self.file.close()

    def write(self,
              data = None
              ):
        if type(data) == list:
            if data is not None:
                for line in data:
                    self.file.write("%s\n" % line)
        else:
            self.file.write("%s\n" % data)

    def createWay(self,
                  way: dict,
                  modified: bool = False
                  ):
        """This creates a string that is the OSM representation of a node"""
        attrs = dict()
        osm = ""

        # Add default attributes
        if modified:
            attrs["action"] = "modify"
        if "osm_way_id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["osm_way_id"])
        elif "osm_id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["osm_id"])
        elif "id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["id"])
        else:
            attrs["id"] = self.start
            self.start -= 1
        if "version" not in way["attrs"]:
            attrs["version"] = 1
        else:
            attrs["version"] = way["attrs"]["version"] + 1
        attrs["timestamp"] = datetime.now().strftime("%Y-%m-%dT%TZ")
        # If the resulting file is publicly accessible without authentication, The GDPR applies
        # and the identifying fields should not be included
        if "uid" in way and attrs["uid"] is not None:
            attrs["uid"] = way["attrs"]["uid"]
        if "user" in way and attrs["user"] is not None:
            attrs["user"] = way["attrs"]["user"]

        # Make all the nodes first. The data in the track has 4 fields. The first two
        # are the lat/lon, then the altitude, and finally the GPS accuracy.
        # newrefs = list()
        node = dict()
        node["attrs"] = dict()
        # The geometry is an EWKT string, so there is no need to get fancy with
        # geometries, just manipulate the string, as OSM XML it's only strings
        # anyway.
        # geom = way['geom'][19:][:-2]
        # print(geom)
        # points = geom.split(",")
        # print(points)

        # epdb.st()
        # loop = 0
        # while loop < len(way['refs']):
        #     #print(f"{points[loop]} {way['refs'][loop]}")
        #     node['timestamp'] = attrs['timestamp']
        #     if 'user' in attrs and attrs['user'] is not None:
        #         node['attrs']['user'] = attrs['user']
        #     if 'uid' in attrs and attrs['uid'] is not None:
        #         node['attrs']['uid'] = attrs['uid']
        #     node['version'] = 0
        #     lat,lon = points[loop].split(' ')
        #     node['attrs']['lat'] = lat
        #     node['attrs']['lon'] = lon
        #     node['attrs']['id'] = way['refs'][loop]
        #     osm += self.createNode(node) + '\n'
        #     loop += 1

        # Processs atrributes
        line = ""
        for ref, value in attrs.items():
            line += "%s=%r " % (ref, str(value))
        osm += "  <way " + line + ">"

        for ref in way["refs"]:
            osm += '\n    <nd ref="%s"/>' % ref

        if "tags" in way:
            for key, value in way["tags"].items():
                if value is None:
                    continue
                if key == "track":
                    continue
                if key not in attrs:
                    newkey = escape(key)
                    osm += "\n    <tag k='%s' v=%r/>" % (newkey, str(value))
            if modified:
                osm += (
                    '\n    <tag k="fixme" v="Do not upload this without validation!"/>'
                )
            osm += "\n"

        osm += "  </way>"

        return osm

    def createNode(self,
                   node: dict,
                   modified: bool = False
                   ):
        """This creates a string that is the OSM representation of a node"""
        attrs = dict()
        # Add default attributes
        if modified:
            attrs["action"] = "modify"

        if "id" in node["attrs"]:
            attrs["id"] = int(node["attrs"]["id"])
        else:
            attrs["id"] = self.start
            self.start -= 1
        if "version" not in node["attrs"]:
            attrs["version"] = "1"
        else:
            attrs["version"] = int(node["version"]) + 1
        attrs["lat"] = node["attrs"]["lat"]
        attrs["lon"] = node["attrs"]["lon"]
        attrs["timestamp"] = datetime.now().strftime("%Y-%m-%dT%TZ")
        # If the resulting file is publicly accessible without authentication, THE GDPR applies
        # and the identifying fields should not be included
        if "uid" in node and attrs["uid"] is not None:
            attrs["uid"] = node["uid"]
        if "user" in node and attrs["ser"] is not None:
            attrs["user"] = node["user"]

        # Processs atrributes
        line = ""
        osm = ""
        for ref, value in attrs.items():
            line += "%s=%r " % (ref, str(value))
        osm += "  <node " + line

        if "tags" in node:
            osm += ">"
            for key, value in node["tags"].items():
                if not value:
                    continue
                if key not in attrs:
                    osm += "\n    <tag k='%s' v=%r/>" % (key, str(value))
            if modified:
                osm += (
                    '\n    <tag k="fixme" v="Do not upload this without validation!"/>'
                )
            osm += "\n  </node>"
        else:
            osm += "/>"

        return osm

    def createTag(self,
                  field: str,
                  value: str
                  ):
        """Create a data structure for an OSM feature tag"""
        newval = str(value)
        newval = newval.replace("&", "and")
        newval = newval.replace('"', "")
        tag = dict()
        # logging.debug("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        newtag = field
        change = newval.split("=")
        if len(change) > 1:
            newtag = change[0]
            newval = change[1]

        tag[newtag] = newval
        return tag

    def loadFile(self,
                 osmfile: str
                 ):
        """Read a OSM XML file generated by osm_fieldwork"""
        size = os.path.getsize(osmfile)
        with open(osmfile, "r") as file:
            xml = file.read(size)  # Instances are small, read the whole file
            doc = xmltodict.parse(xml)
            if "osm" not in doc:
                logging.warning("No data in this instance")
                return False
            field = doc["osm"]
        if type(field["node"]) == dict:
            attrs = dict()
            tags = dict()
            for k, v in field["node"].items():
                if k[0] == '@':
                    attrs[k[1:]] = v
                else:
                    for pair in field["node"]['tag']:
                        tags[pair['@k']] = pair['@v']
            node = {"attrs": attrs, "tags": tags}
            self.data[node["attrs"]["id"]] = node
        else:
            for node in field["node"]:
                attrs = {
                    "id": int(node["@id"]),
                    "lat": node["@lat"][:10],
                    "lon": node["@lon"][:10],
                    "timestamp": node["@timestamp"],
                }
                tags = dict()
                if "tag" in node:
                    for tag in node["tag"]:
                        print(f"NODE: {node}")
                        # Only one tag is a dictionary
                        if type(tag) == dict:
                            tags[tag["@k"]] = tag["@v"].strip()
                            continue
                        # Multiple tags is a list
                        elif type(tag) == list:
                            tags[tag["@k"]] = tag["@v"].strip()
                    node = {"attrs": attrs, "tags": tags}
                    self.data[node["attrs"]["id"]] = node
        return self.data

    def dump(self):
        """Dump the contents of an OSM file"""
        for id, item in self.data.items():
            for k, v in item["attrs"].items():
                print(f"{k} = {v}")
            for k, v in item["tags"].items():
                print(f"\t{k} = {v}")

    def getFeature(self,
                   id: int
                   ):
        """Get the data for a feature from the loaded OSM data file"""
        return self.data[id]

    def getFields(self):
        """Extract all the tags used in this file"""
        fields = list()
        for id, item in self.data.items():
            keys = list(item["tags"].keys())
            for key in keys:
                if key not in fields:
                    fields.append(key)
        print(fields)


if __name__ == "__main__":
    # Command Line options
    parser = argparse.ArgumentParser(
        description="This program conflates ODK data with existing features from OSM."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-o", "--osmfile", help="OSM XML file created by Osm-Fieldwork")
    args = parser.parse_args()

    # This program needs options to actually do anything
    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

    osm = OsmFile()
    osm.loadFile(args.osmfile)
    osm.dump()
