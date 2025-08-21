from enum import Enum, IntEnum

class ChunkType(Enum):
    NAOBJECT        = 0x0  #do NOT use this.
    STRUCT          = 0x1  #nonymous chunk.
    STRING          = 0x2
    EXTENSION       = 0x3
    CAMERA          = 0x5
    TEXTURE         = 0x6
    MATERIAL        = 0x7
    MATLIST         = 0x8
    ATOMICSECT      = 0x9
    PLANESECT       = 0xA
    WORLD           = 0xB
    SPLINE          = 0xC
    MATRIX          = 0xD
    FRAMELIST       = 0xE
    GEOMETRY        = 0xF
    CLUMP           = 0x10
    LIGHT           = 0x12
    UNICODESTRING   = 0x13
    ATOMIC          = 0x14
    TEXTURENATIVE   = 0x15
    TEXDICTIONARY   = 0x16
    ANIMDATABASE    = 0x17
    IMAGE           = 0x18
    SKINANIMATION   = 0x19
    GEOMETRYLIST    = 0x1A
    ANIMANIMATION   = 0x1B
    HANIMANIMATION  = 0x1B
    TEAM            = 0x1C
    CROWD           = 0x1D
    RIGHTTORENDER   = 0x1F
    MTEFFECTNATIVE  = 0x20
    MTEFFECTDICT    = 0x21
    TEAMDICTIONARY  = 0x22
    PITEXDICTIONARY = 0x23
    TOC             = 0x24
    PRTSTDGLOBALDATA = 0x25
    ALTPIPE         = 0x26
    PIPEDS          = 0x27
    PATCHMESH       = 0x28
    CHUNKGROUPSTART = 0x29
    CHUNKGROUPEND   = 0x2A
    UVANIMDICT      = 0x2B
    COLLTREE        = 0x2C
    ENVIRONMENT     = 0x2D
    COREPLUGINIDMAX = 0x2E
    METRICSPLUGIN   = 0x101
    SPLINEPLUGIN    = 0x102
    STEREOPLUGIN    = 0x103
    VRMLPLG         = 0x104
    MORPH           = 0x105
    PVSPLUGIN       = 0x106
    MEMLEAKPLUGIN   = 0x107
    ANIMPLUGIN      = 0x108
    GLOSSPLUGIN     = 0x109
    LOGOPLUGIN      = 0x10a
    MEMINFOPLUGIN   = 0x10b
    RANDOMPLUGIN    = 0x10c
    PNGIMAGEPLUGIN  = 0x10d
    BONEPLUGIN      = 0x10e
    VRMLANIMPLUGIN  = 0x10f
    SKYMIPMAP       = 0x110
    MRMPLUGIN       = 0x111
    LODATMPLUGIN    = 0x112
    MEPLUGIN        = 0x113
    LTMAPPLUGIN     = 0x114
    REFINEPLUGIN    = 0x115
    SKIN            = 0x116
    LABELPLUGIN     = 0x117
    PARTICLES       = 0x118
    GEOMTXPLUGIN    = 0X119
    SYNTHCOREPLUGIN = 0X11a
    STQPPPLUGIN     = 0X11b
    PARTPPPLUGIN    = 0X11c
    COLLISPLUGIN    = 0X11d
    HANIMPLUGIN     = 0X11e
    USERDATAPLUGIN  = 0X11f
    MATERIALEFFECTS = 0x120
    PARTICLESYSTEMPLUGIN = 0X121
    DMORPHPLUGIN    = 0x122
    PATCHPLUGIN     = 0x123
    TEAMPLUGIN      = 0x124
    CROWDPPPLUGIN   = 0x125
    MIPSPLITPLUGIN  = 0x126
    ANISOTPLUGIN    = 0x127
    GCNMATPLUGIN    = 0x129
    GPVSPLUGIN      = 0x12a
    XBOXMATPLUGIN   = 0x12b
    MULTITEXPLUGIN  = 0x12c
    CHAINPLUGIN     = 0x12d
    TOONPLUGIN      = 0x12e
    PTANKPLUGIN     = 0x12f
    PRTSTDPLUGIN    = 0x130
    PDSPLUGIN       = 0x131
    PRTADVPLUGIN    = 0x132
    NORMMAPPLUGIN   = 0x133
    ADCPLUGIN       = 0x134
    UVANIMPLUGIN    = 0x135
    CHARSEPLUGIN    = 0x180
    NOHSWORLDPLUGIN = 0x181
    IMPUTILPLUGIN   = 0x182
    SLERPPLUGIN     = 0x183
    OPTIMPLUGIN     = 0x184
    TLWORLDPLUGIN   = 0x185
    DATABASEPLUGIN  = 0x186
    RAYTRACEPLUGIN  = 0x187
    RAYPLUGIN       = 0x188
    LIBRARYPLUGIN   = 0x189
    _2DPLUGIN        = 0x190
    TILERENDPLUGIN  = 0x191
    JPEGIMAGEPLUGIN = 0x192
    TGAIMAGEPLUGIN  = 0x193
    GIFIMAGEPLUGIN  = 0x194
    QUATPLUGIN      = 0x195
    SPLINEPVSPLUGIN = 0x196
    MIPMAPPLUGIN    = 0x197
    MIPMAPKPLUGIN   = 0x198
    _2DFONT          = 0x199
    INTSECPLUGIN    = 0x19a
    TIFFIMAGEPLUGIN = 0x19b
    PICKPLUGIN      = 0x19c
    BMPIMAGEPLUGIN  = 0x19d
    RASIMAGEPLUGIN  = 0x19e
    SKINFXPLUGIN    = 0x19f
    VCATPLUGIN      = 0x1a0
    _2DPATH          = 0x1a1
    _2DBRUSH         = 0x1a2
    _2DOBJECT        = 0x1a3
    _2DSHAPE         = 0x1a4
    _2DSCENE         = 0x1a5
    _2DPICKREGION    = 0x1a6
    _2DOBJECTSTRING  = 0x1a7
    _2DANIMPLUGIN    = 0x1a8
    _2DANIM          = 0x1a9
    _2DKEYFRAME      = 0x1b0
    _2DMAESTRO       = 0x1b1
    BARYCENTRIC     = 0x1b2
    PITEXDICTIONARYTK = 0x1b3
    TOCTOOLKIT      = 0x1b4
    TPLTOOLKIT      = 0x1b5
    ALTPIPETOOLKIT  = 0x1b6
    ANIMTOOLKIT     = 0x1b7
    SKINSPLITTOOKIT = 0x1b8
    CMPKEYTOOLKIT   = 0x1b9
    GEOMCONDPLUGIN  = 0x1ba
    WINGPLUGIN      = 0x1bb
    GENCPIPETOOLKIT = 0x1bc
    LTMAPCNVTOOLKIT = 0x1bd
    FILESYSTEMPLUGIN = 0x1be
    DICTTOOLKIT     = 0x1bf
    UVANIMLINEAR    = 0x1c0
    UVANIMPARAM     = 0x1c1
    BINMESH         = 0x50E
    NATIVEDATA      = 0x510
    VERTEXFORMAT    = 0x510
    SCRIPT          = 0x704
    ASSET           = 0x716
    CONTAINER       = 0x71C
    PIPELINESET     = 0x253F2F3
    SPECULARMAT     = 0x253F2F6
    CHUNK_2DFX      = 0x253F2F8
    NIGHTVERTEXCOLOR = 0x253F2F9
    COLLISIONMODEL  = 0x253F2FA
    REFLECTIONMAT   = 0x253F2FC
    MESHEXTENSION   = 0x253F2FD
    FRAME           = 0x253F2FE

def PackRWVersion(decversion):
    rwversion = ((decversion - 0x30000 & 0x3ff00) << 14) | (decversion & 0x3F) << 16
    rwversion =  rwversion.to_bytes(4, byteorder="little")
    return rwversion

def UnpackRWVersion(rwfile):
    rwversion = rwfile.read(4)
    rwversion = int.from_bytes(rwversion, 'little')
    rwversion = (rwversion >> 14 & 0x3FF00) + 0x30000 | (rwversion >> 16 & 0x3F)
    return rwversion

def GetFileSize(rwfile):
    rwfile.seek(0, 2)
    fileSize = rwfile.tell()
    return fileSize

#Section Parameter functions

def GetSectionType(rwfile):
    rwtype = rwfile.read(4)
    rwtype = int.from_bytes(rwtype, 'little')
    disptype = str()
    if rwtype in ChunkType._value2member_map_:
        disptype = ChunkType(rwtype)
        disptype = disptype.name
    else:
        disptype = 'UNKNOWN'
    return disptype

def GetSectionTypeRaw(rwsection):
    typeraw = rwsection.read(4)
    typeraw = int.from_bytes(typeraw, 'little')
    return typeraw

def GetSectionSize(rwsection):
    secSize = rwsection.read(4)
    secSize = int.from_bytes(secSize, 'little')
    return secSize

def GetHeaderSize(rwsection):
    HeaderSize = rwsection.read(4)
    HeaderSize = int.from_bytes(HeaderSize, 'little')
    #HeaderSize += 4
    return HeaderSize

def GetSectionName(rwsection):
    NameSize = rwsection.read(4)
    NameSize = int.from_bytes(NameSize, 'little')
    SectionName = rwsection.read(NameSize)
    return SectionName

def GetUnknownBin(rwsection):
    UnknownBin = rwsection.read(16)
    return UnknownBin

def GetTypeName(rwsection):
    rwIDSize = rwsection.read(4)
    rwIDSize = int.from_bytes(rwIDSize, 'little')
    rwIDName = rwsection.read(rwIDSize)
    return rwIDName

def GetProjectPath(rwsection):
    ProjPathSize = rwsection.read(4)
    ProjPathSize = int.from_bytes(ProjPathSize, 'little')
    ProjectPath = rwsection.read(ProjPathSize)
    return ProjectPath

def GetBuildPath(rwsection):
    BuildPathSize = rwsection.read(4)
    BuildPathSize = int.from_bytes(BuildPathSize, 'little')
    BuildPath = rwsection.read(BuildPathSize)
    return BuildPath

def Skip4Bytes(rwsection):
    #Null Padding
    rwsection.seek(4, 1)
    return rwsection

def GetAssetSize(rwsection):        
    AssetSize = rwsection.read(4)
    AssetSize = int.from_bytes(AssetSize, 'little')
    #AssetSize -= 9
    return AssetSize




