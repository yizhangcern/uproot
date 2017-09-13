#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import struct

import numpy
import pyxrootd.client

import uproot.walker.walker

class XRootDWalker(uproot.walker.walker.Walker):
    def __init__(self, path, index=None, origin=None, reusefile=None):
        if reusefile is None:
            self.path = path
            self.file = None
        else:
            self.path = path
            self.file = reusefile

        if index is not None:
            self.index = index
        else:
            self.index = 0

        self.refs = {}
        if origin is not None:
            self.origin = origin

    def _evaluate(self, newfile=False):
        self._holdfile = self.file
        if newfile:
            self.file = None

    def _unevaluate(self):
        self.file = self._holdfile

    def startcontext(self):
        if self.file is None:
            self.file = pyxrootd.client.File()
            status, dummy = self.file.open(self.path)
            if status["error"]:
                raise IOError(status.message)

    def copy(self, index=None, origin=None):
        if index is None:
            index = self.index
        return XRootDWalker(self.path, index, origin, self.file)
        
    def skip(self, format):
        if isinstance(format, int):
            self.index += format
        else:
            size = self.size(format)
            self.index += size

    def readfields(self, format, index=None):
        if index is not None:
            self.index = index
        size = self.size(format)
        self.index += size
        status, data = self.file.read(self.index, size)
        if status["error"]:
            raise IOError(status.message)
        return struct.unpack(format, data)

    def readfield(self, format, index=None):
        out, = self.readfields(format, index)
        return out

    def readbytes(self, length, index=None):
        if index is not None:
            self.index = index
        self.index += length
        status, data = self.file.read(self.index, length)
        if status["error"]:
            raise IOError(status.message)
        return numpy.frombuffer(data, dtype=numpy.uint8)

    def readarray(self, dtype, length, index=None):
        if index is not None:
            self.index = index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        self.index += length * dtype.itemsize
        status, data = self.file.read(self.index, length * dtype.itemsize)
        if status["error"]:
            raise IOError(status.message)
        return numpy.frombuffer(data, dtype=dtype)

    def readstring(self, index=None, length=None):
        if index is not None:
            self.index = index
        if length is None:
            status, data = self.file.read(self.index, 1)
            if status["error"]:
                raise IOError(status.message)
            length = ord(data)
            self.index += 1
            if length == 255:
                status, data = self.file.read(self.index, 4)
                if status["error"]:
                    raise IOError(status.message)
                length = numpy.frombuffer(data, dtype=numpy.uint32)[0]
                self.index += 4
        self.index += length
        status, data = self.file.read(self.index, length)
        if status["error"]:
            raise IOError(status.message)
        return data

    def readcstring(self, index=None):
        if index is not None:
            self.index = index
        out = []
        while len(out) == 0 or ord(out[-1]) != 0:
            self.index += 1
            status, data = self.file.read(self.index, 1)
            if status["error"]:
                raise IOError(status.message)
            out.append(data)
        return b"".join(out[:-1])
