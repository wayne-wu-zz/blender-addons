import bpy
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
import numpy
from mathutils import Matrix

sizeOfFloat = 4 #byte
sizeOfInt = 4 #byte

#vertex shader
vertex_shader = """
#version 330
layout(location = 0) in vec3 position;
    
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
    
void main()
{
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""

#fragment shader
fragment_shader = """
#version 330
out vec4 outputColor;
void main()
{
    outputColor = vec4(1.0f, 1.0f, 1.0f, 1.0f);
}
"""

#global instances of the program and vbos
own = {
	'vbo':      None,
    'vao':      None,
    'ebo':      None,
	'program':  None,
	'vertex':   None,
	'fragment': None
}

#global instances for uniform locations
uniforms = {
    'projection' : None,
    'model' : None,
    'view' : None,
}

vertex_data = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0]
]

index_data = [
    [0, 1, 2]
]

def is_successful(shader):
    #TODO: Check if the shader was successfully compiled
    return True

def create_VBO():
    #Create the VBO

    vertices = numpy.array(vertex_data, numpy.float32)
    indices = numpy.array(index_data, numpy.int32)

    own["program"] = glCreateProgram()

    #shaders
    shader_v = glCreateShader(GL_VERTEX_SHADER)
    shader_f = glCreateShader(GL_FRAGMENT_SHADER)

    #Assign the shader string
    glShaderSource(shader_v, vertex_shader)
    glShaderSource(shader_f, fragment_shader)

    #Compile the shader to make sure it works
    glCompileShader(shader_v)
    glCompileShader(shader_f)

    #Attach the shader to the gl program
    glAttachShader(own["program"], shader_v)
    glAttachShader(own["program"], shader_f)

    glLinkProgram(own["program"])

    #Store the uniform values' locations. Must get it after the program has been linked.
    uniforms['projection'] = glGetUniformLocation(own['program'], 'projection')
    uniforms['view'] = glGetUniformLocation(own['program'], 'view')
    uniforms['model'] = glGetUniformLocation(own['program'], 'model')

    #Once the shaders are attached and linked, they can be deleted
    glDeleteShader(shader_v)
    glDeleteShader(shader_f)

    # Create a new VAO (Vertex Array Object) and bind it. VAO seems to be mandatory for Blender
    own['vao'] = glGenVertexArrays(1)
    glBindVertexArray(own['vao'])

    # Create VBO and EBO
    own['vbo'] = vbo.VBO(vertices, usage = 'GL_STATIC_DRAW')
    own['vbo'].bind()
    own['ebo'] = vbo.VBO(indices, usage = 'GL_STATIC_DRAW', target = 'GL_ELEMENT_ARRAY_BUFFER')
    own['ebo'].bind()

    glEnableVertexAttribArray(0);

    # Describe the position data layout in the buffer
    #NULL = Buffer(GL_INT, 1, [0])
    #glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, NULL)
    glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)

    # Unbind the VAO first (Important, otherwise nothing will be drawn and Blender UI will be over drawn after stop)
    glBindVertexArray(0)

    # Unbind other stuff
    unbind()

def bind():
    #Bind the VBOs
    own['vbo'].bind()
    own['ebo'].bind()

def bind_vao():
    #Bind the VAO for drawing
    glBindVertexArray(own['vao'])

def unbind_vao():
    #Unbind the VAO
    glBindVertexArray(0)

def unbind():
    #Unbind the VBOs
    own['vbo'].unbind()
    own['ebo'].unbind()

#The draw loop
def draw_callback(context):
    glUseProgram(own["program"])

    #Set the uniform variables
    mat_p = get_perspective_matrix(context)
    mat_v = Matrix.Identity(4) #Not needed
    mat_m = Matrix.Identity(4) #Not needed
    set_uniform('projection', to_array(mat_p))
    set_uniform('view', to_array(mat_v))
    set_uniform('model', to_array(mat_m))

    try:
        bind_vao()
        #glDrawArrays(GL_TRIANGLES, 0, len(vertices)//3)

        #NULL = Buffer(GL_INT, 1, [0])
        #glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, NULL)
        glDrawElements(GL_TRIANGLES, len(index_data[0]), GL_UNSIGNED_INT, None)

    finally:
        # Unbind the VAO (Important, otherwise Blender will crash)
        unbind_vao()

    # Unbind Program (Important, otherwise Blender UI will be over drawn after stop)
    glUseProgram(0)

def terminate():
    glUseProgram(0)
    own['program'] = None

    #Technically optional, but should delete the VAO. It's throwing a TypeError right now.
    #glDeleteVertexArrays(1, own['vao'])
    own['vao'] = None

    # glDeleteBuffers(1, own['vbo'])
    own['vbo'].delete()
    own['vbo'] = None
    # glDeleteBuffers(1, own['ebo'])
    own['ebo'].delete()
    own['ebo'] = None

def set_uniform(variable, value):
    if variable not in uniforms:
        return
    glUniformMatrix4fv(uniforms[variable], 1, GL_TRUE, value)

def get_perspective_matrix(context):
    return context.area.spaces[0].region_3d.perspective_matrix # = (window_matrix * view_matrix)

def to_array(matrix):
    #Convert blender matrix to shader-readable numpy array
    return numpy.array([p for v in matrix for p in v], numpy.float32)

class ModalDrawOperator(bpy.types.Operator):
    bl_idname = "view3d.modal_operator"
    bl_label = "Simple Modal View3D Operator"

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handler_3d, 'WINDOW')
            terminate()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            global own
            create_VBO()
            args = (context,)
            self._handler_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ModalDrawOperator)

def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)

if __name__ == "__main__":
    register()