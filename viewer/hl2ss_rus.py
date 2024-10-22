import struct
import hl2ss

# 3D Primitive Types
class PrimitiveType:
    Sphere = 0
    Capsule = 1
    Cylinder = 2
    Cube = 3
    Plane = 4
    Quad = 5

# Server Target Mode
class TargetMode:
    UseID = 0
    UseLast = 1

# Object Active State
class ActiveState:
    Inactive = 0
    Active = 1

#------------------------------------------------------------------------------
# Commands
#------------------------------------------------------------------------------

class command_buffer(hl2ss.umq_command_buffer):
    def create_primitive(self, type):
        self.add(0, struct.pack('<I', type))

    def set_active(self, key, state):
        self.add(1, struct.pack('<II', key, state))

    def set_world_transform(self, key, position, rotation, scale):
        self.add(2, struct.pack('<Iffffffffff', key, position[0], position[1], position[2], rotation[0], rotation[1], rotation[2], rotation[3], scale[0], scale[1], scale[2]))

    def set_local_transform(self, key, position, rotation, scale):
        self.add(3, struct.pack('<Iffffffffff', key, position[0], position[1], position[2], rotation[0], rotation[1], rotation[2], rotation[3], scale[0], scale[1], scale[2]))

    def set_color(self, key, rgba):
        self.add(4, struct.pack('<Iffff', key, rgba[0], rgba[1], rgba[2], rgba[3]))

    def set_texture(self, key, texture):
        self.add(5, struct.pack('<I', key) + texture)

    def create_text(self): 
        self.add(6, b'')

    def create_interactable_text(self):
        self.add(21, b'')

    def set_interactable_text(self, key, text):
        self.__commands.append([22, struct.pack('<I', key) + text.encode('utf-8')])
    
    def create_arrow(self):
        self.add(23, b'')
    
    def set_arrow_transform(self, key, position, rotation, scale):
        data = bytearray()
        data.extend(struct.pack('I', key))

    def set_arrow_transform(self, key, position, rotation, scale):
        data = bytearray()
        data.extend(struct.pack('I', key))
        data.extend(struct.pack('fff', *position))
        data.extend(struct.pack('ffff', *rotation))
        data.extend(struct.pack('fff', *scale))
        self.add(25, data)
    
    def toggle_object_visibility(self, key, visible):
        data = bytearray()
        data.extend(struct.pack('I', key))
        data.extend(struct.pack('I', 1 if visible else 0))
        self.add(24, data)

    def set_text(self, key, font_size, rgba, string):
        self.add(7, struct.pack('<Ifffff', key, font_size, rgba[0], rgba[1], rgba[2], rgba[3]) + string.encode('utf-8'))

    def say(self, text):
        self.add(8, text.encode('utf-8'))

    def load_mesh(self, data):
        self.add(15, data)

    def remove(self, key):
        self.add(16, struct.pack('<I', key))

    def remove_all(self):
        self.add(17, b'')

    def begin_display_list(self):
        self.add(18, b'')

    def end_display_list(self):
        self.add(19, b'')

    def set_target_mode(self, mode):
        self.add(20, struct.pack('<I', mode))
