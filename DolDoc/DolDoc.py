#!/usr/bin/env python3
import struct
import io
import argparse

class DolDocError(BaseException):
    pass

class DolDocElement:
    def __init__(self, name, id):
        self.name = name
        self.id = id
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return "<DolDocElement {}>".format(self)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        return self
    
    @classmethod
    def fromBytes(cls, name, id, data):
        buffer = io.BytesIO(data)
        buffer.seek(0)
        return cls.fromStream(name, id, buffer)

class DolDocElementEnd(DolDocElement):
    def __str__(self):
        return "END"

class DolDocElementColor(DolDocElement):
    colors = [
        "BLACK", "BLUE", "GREEN", "CYAN", "RED", "PURPLE",
        "BROWN", "LTGRAY", "DKGRAY", "LTBLUE", "LTGREEN",
        "LTCYAN", "LTRED", "LTPURPLE", "YELLOW", "WHITE"
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = 0
    
    def __str__(self):
        return "{} {}".format(self.name, self.colors[self.color])
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.color = stream.read(1)[0]
        return self

class DolDocElementCircle(DolDocElement):
    #X, Y, Radius
    sCircle = struct.Struct("<iii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x = 0
        self.y = 0
        self.radius = 0
    
    def __str__(self):
        return "{} ({}, {}):{}R".format(self.name, self.x, self.y, self.radius)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x, self.y, self.radius = self.sCircle.unpack(
            stream.read(self.sCircle.size)
        )
        return self

class DolDocElementLine(DolDocElement):
    #X1, Y1, X2, Y2
    sLine = struct.Struct("<iiii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
    
    def __str__(self):
        return "{} ({}, {}), ({}, {})".format(self.name, self.x1, self.y1, self.x2, self.y2)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x1, self.y1, self.x2, self.y2 = \
            self.sLine.unpack(
                stream.read(self.sLine.size)
            )
        return self

class DolDocElementFloodFill(DolDocElement):
    #X, Y
    sFloodFill = struct.Struct("<ii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x = 0
        self.y = 0
    
    def __str__(self):
        return "{} ({}, {})".format(self.name, self.x, self.y)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x, self.y = self.sFloodFill.unpack(
            stream.read(self.sFloodFill.size)
        )
        return self

class DolDocElementThick(DolDocElement):
    sThickness = struct.Struct("<i")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thickness = 0
    
    def __str__(self):
        return "{} {}".format(self.name, self.thickness)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.thickness, = self.sThickness.unpack(
            stream.read(self.sThickness.size)
        )
        return self

class DolDocElementMesh(DolDocElement):
    #Vertice count, Triangle count
    sMeshHeader = struct.Struct("<ii")
    
    #X, Y, Z
    sVertex = struct.Struct("<iii")
    
    #Color, A, B, C
    sTriangle = struct.Struct("<iiii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vertices = []
        self.triangles = []
    
    def __str__(self):
        return "{} {}V,{}T".format(self.name, len(self.vertices), len(self.triangles))
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        vertex_cnt, tri_cnt = self.sMeshHeader.unpack(
            stream.read(self.sMeshHeader.size)
        )
        self.vertices = [None] * vertex_cnt
        for i in range(vertex_cnt):
            self.vertices[i] = self.sVertex.unpack(
                stream.read(self.sVertex.size)
            )
        
        self.triangles = [None] * tri_cnt
        for i in range(tri_cnt):
            self.triangles[i] = self.sTriangle.unpack(
                stream.read(self.sTriangle.size)
            )
        return self

class DolDocElementPoint(DolDocElement):
    #x, y, z(?)
    sPoint = struct.Struct("<iii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x = 0
        self.y = 0
        self.z = 0
    
    def __str__(self):
        return "{} ({},{})".format(self.name, self.x, self.y)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x, self.y, self.z = self.sPoint.unpack(
            stream.read(self.sPoint.size)
        )
        return self

class DolDocElementText(DolDocElement):
    sTextHeader = struct.Struct("<ii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x = 0
        self.y = 0
        self.text = b""
    
    def __str__(self):
        return "{} {},{}:{}".format(self.name, self.x, self.y, self.text)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x, self.y = self.sTextHeader.unpack(
            stream.read(self.sTextHeader.size)
        )
        self.text = b""
        while True:
            v = stream.read(1)
            if v == b"\0":
                break
            self.text += v
        
        return self


class DolDocElementBitMap(DolDocElement):
    sBitMapHeader = struct.Struct("<iiii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.data = []
    
    def __str__(self):
        return "{} ({},{}):{}W,{}H".format(self.name, self.x, self.y, self.width, self.height)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x, self.y, self.width, self.height = self.sBitMapHeader.unpack(
            stream.read(self.sBitMapHeader.size)
        )
        
        #TODO: Unpack this further.
        #It should be a left = pixel >> 4, right = pixel & 0xF
        self.data = stream.read(self.width*self.height)
        return self


class DolDocElementArrow(DolDocElement):
    #X1, Y1, X2, Y2
    sArrow = struct.Struct("<iiii")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
    
    def __str__(self):
        return "{} ({}, {}), ({}, {})".format(self.name, self.x1, self.y1, self.x2, self.y2)
    
    @classmethod
    def fromStream(cls, name, id, stream):
        self = cls(name, id)
        self.x1, self.y1, self.x2, self.y2 = \
            self.sArrow.unpack(
                stream.read(self.sArrow.size)
            )
        return self

DolDocTypes = {
    "End": DolDocElementEnd,
    "Color": DolDocElementColor,
    "Thick": DolDocElementThick,
    #"PlanarSymmetry": DolDocPlanarSymmetry,
    #"Transform": DolDocTransform,
    #"Shift": DolDocShift,
    "Pt": DolDocElementPoint, #FIXME: VERIFY
    #"PolyPt": DolDocPolyPt,
    "Line": DolDocElementLine,
    #"PolyLine": DolDocElementPolyLine,
    #"Rect": DolDocRect,
    "Circle": DolDocElementCircle,
    #"Ellipse": DolDocEllipse,
    #"Polygon": DolDocPolygon,
    #"BSpline2": DolDocBSpline2,
    #"BSpline3": DolDocBSpline3,
    "FloodFill": DolDocElementFloodFill,
    "BitMap": DolDocElementBitMap,
    "Mesh": DolDocElementMesh,
    "Arrow": DolDocElementArrow,
    "Text": DolDocElementText,
    #"TextBox": DolDocTextBox
    #"TextDiamond": DolDocTextDiamond
}

DolDocMapping = [
    ('End', 'End'),
    ('Color', 'Color'),
    ('Dither Color', 'Color'),
    ('Thick', 'Thick'),
    ('Planar Symmetry', 'PlanarSymmetry'),
    ('Transform On', 'Transform'),
    ('Transform Off', 'Transform'),
    ('Shift', 'Shift'),
    ('Point', 'Pt'),
    ('PolyPoint', 'PolyPt'),
    ('Line', 'Line'),
    ('PolyLine', 'PolyLine'),
    ('Rect', 'Rect'),
    ('Rotated Rect', 'Rect'),
    ('Circle', 'Circle'),
    ('Ellipse', 'Ellipse'),
    ('Polygon', 'Polygon'),
    ('BSpline2', 'BSpline2'),
    ('BSpline2 Closed', 'BSpline2'),
    ('BSpline3', 'BSpline3'),
    ('BSpline3 Closed', 'BSpline3'),
    ('Flood Fill', 'FloodFill'),
    ('Flood Fill Not Color', 'FloodFill'),
    ('BitMap', 'BitMap'),
    ('Mesh', 'Mesh'),
    ('Shiftable Mesh', 'Mesh'),
    ('Arrow', 'Arrow'),
    ('Text', 'Text'),
    ('Text Box', 'TextBox'),
    ('Text Diamond', 'TextDiamond')
]

class DolDocEntry:
    def __init__(self):
        self.elements = []
    
    @classmethod
    def fromStream(cls, stream):
        self = cls()
        i = 0
        while True:
            try:
                etype = stream.read(1)[0]
            except IndexError:
                raise DolDocError("EOF reached before End marker!")
            
            if etype > len(DolDocMapping):
                raise DolDocError("Don't know what type {} at {} is!".format(etype, stream.tell()))
            
            name = DolDocMapping[etype][0]
            cls = DolDocMapping[etype][1]
            if cls not in DolDocTypes:
                raise DolDocError("Don't know how to decode {} at {}!".format(cls, stream.tell()))
            
            elm = DolDocTypes[cls].fromStream(name, etype, stream)
            
            self.elements.append(elm)
            if elm.name == "End":
                break
        
        return self
    
    @classmethod
    def fromBytes(cls, data):
        buffer = io.BytesIO(data)
        buffer.seek(0)
        return cls.fromStream(buffer)

class DolDoc:
    sDolDocEntry = struct.Struct("<IIII")
    def __init__(self, text = "", chunks = None):
        self.text = text
        self.chunks = chunks or []
    
    @classmethod
    def load(cls, handle):
        self = cls()
        buffer = b""
        while True:
            c = handle.read(1)
            if not c or c == b"\0":
                break
            buffer += c
        
        self.text = buffer
        while True:
            data = handle.read(self.sDolDocEntry.size)
            if not data:
                break
            chunkId, flags, size, refCount \
                = self.sDolDocEntry.unpack(data)
            data = handle.read(size)
            self.chunks.append([
                chunkId,
                flags,
                size,
                refCount,
                DolDocEntry.fromBytes(data)
            ])
        return self

if __name__ == "__main__":
    # create the top-level parser
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(help='sub-command help')

    # List
    parser_list = subparsers.add_parser("l", help='a help')
    parser_list.add_argument('file', nargs="+", type=argparse.FileType('rb'), help='Input file(s)')

    # Extract
    parser_extract = subparsers.add_parser("e", help='b help')
    parser_extract.add_argument('file', nargs="+", type=argparse.FileType('rb'), help='Input file(s)')
    parser_extract.add_argument('-o', '--output', nargs="+", type=argparse.FileType('rb'), help='Output directory')

    args = parser.parse_args()
    
    for file in args.file:
        print("# "+file.name)
        dd = DolDoc.load(file)
        file.close()