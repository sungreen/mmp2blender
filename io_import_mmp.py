# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os, subprocess
import bpy
from bpy.props import *
import xml.etree.ElementTree as ET

bl_info = {
    "name": "Import LMMP Pattern to Scene (.mmp)",
    "author": "blender-3d.ru/forum",
    "version": (0, 0, 1),
    "blender": (2, 78, 0),
    "location": "File > Import > LMMP Pattern to Scene(.mmp)",
    "description": "Imports LMMP files as a series of animation properties",
    "category": "Import-Export",
}

"""
This script imports LMMP files into 3D Scenes (.mmp)
"""

def loadMMP(path,name):
    filename=path+name+'.mmp'
    tree = ET.parse(filename)
    return make_object(name),tree.getroot()

def make_object(name):
    global scene
    ob = bpy.data.objects.new(name, None)
    scene.objects.link(ob)
    scene.update()
    ob.empty_draw_type = 'CUBE'
    ob.empty_draw_size = 1
    return ob

def insert_key(pattern,frame,name,value):
    global scene
    scene.frame_set(frame)
    pattern[name]=value
    pattern.keyframe_insert(data_path='["'+name+'"]')
    
def make_note(pattern,key,pos,len,vol):
    name="note:"+key
    insert_key(pattern,pos-offset,name,0)
    insert_key(pattern,pos,name,vol)
    insert_key(pattern,pos+len,name,vol)
    insert_key(pattern,pos+len+offset,name,0)

def sort_pattern(note):
    print(note)
    return note.attrib['key']

def parse(parent,node):
    global scale
    global offset
    if node.tag=='pattern':
        tname=node.attrib['name']
        tpos=int(node.attrib['pos'])
        tlen=int(node.attrib['len'])
        pattern=None
        for note in node:
            key=note.attrib['key']
            pos=int(note.attrib['pos'])
            len=int(note.attrib['len'])
            vol=int(note.attrib['vol'])
            if not pattern:
                pattern=make_object(tname)
                pattern.parent=parent
            make_note(pattern,key,startframe+(tpos+pos)*scale,len*scale,vol)
        return False
    for child in node:
        parse(parent,child)
    return True   

scale = 1
offset = 0
scene = None
startframe = 0

def main(filename, directory, Offset, DefaultTicksPerTact):
    global scene
    global scale
    global offset
    global startframe

    scene = bpy.context.scene
    songname = filename.rstrip('.mmp')
    songpath = directory.replace(' ', '\ ')
    parent,node=loadMMP(songpath,songname)
    
    bpm = 120
    for head in node.findall('head'):
        if 'bpm' in head.attrib:
            bpm = int(head.attrib['bpm'])
    fps = scene.render.fps
    tempo = bpm
    scale = 60/tempo/(DefaultTicksPerTact/4)*fps
    offset = Offset
    startframe = scene.frame_current
    parse(parent,node)
    scene.frame_set(startframe)
    return True


class LMMPPatternToScene(bpy.types.Operator):
    
    bl_idname = "import.lmmp_pattern_to_scene"
    bl_label = "LMMP Pattern to Scene"
    bl_description = "Imports notes from LMMP files into 3D Scenes"
    bl_options = {'REGISTER', 'UNDO'}
 
    filename = StringProperty(name="File Name", description="Name of the file")
    directory = StringProperty(name="Directory", description="Directory of the file")

    Offset = FloatProperty(name="Offset Frame", description="Offset frame", min=0, default=1)
    DefaultTicksPerTact = FloatProperty(name="Default Ticks Per Tact", description="Default ticks per tact", min=16, default=192)
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label('LMMP Pattern:', icon='SORTSIZE')
        box.prop(self, 'Offset')
        box.prop(self, 'DefaultTicksPerTact')
    
    def execute(self, context):
        print(self.filename,self.directory)
        if self.filename.endswith('.mmp'):
            ret = main(self.filename, self.directory, self.Offset, self.DefaultTicksPerTact)
            if not ret:
                return {'CANCELLED'}
        else:
            self.report({'ERROR'},"Selected file wasn't valid, try .mmp")
            return {'CANCELLED'}
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator(LMMPPatternToScene.bl_idname, text="LMMP Pattern to Scene (.mmp)", icon='PLUGIN')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()
