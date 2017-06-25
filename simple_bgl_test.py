import bpy
import bgl
import blf 

origin = (0.0, 0.0, 0.0)

def draw_line_3d(color, start, end, width=3):
    bgl.glLineWidth(width)
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(*start)
    bgl.glVertex3f(*end)
       
def draw_callback_3d(self, context):
    bgl.glPushAttrib(bgl.GL_ENABLE_BIT)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINES) 
    location = context.object.location if context.object else origin 
    draw_line_3d((0.0, 0.0, 0.0, 1.0), origin, location.to_tuple())
     
    bgl.glEnd()
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINES)

    bgl.glPopAttrib()

def draw_callback_2d(self, context):

    bgl.glEnable(bgl.GL_BLEND)

    # draw text
    draw_typo_2d((1.0, 1.0, 1.0, 1), "Hello Word ")

    bgl.glEnd()
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    
def draw_typo_2d(color, text):
    font_id = 0
    
    bgl.glColor4f(*color)
    blf.position(font_id, 20, 70, 0)
    blf.size(font_id, 20, 72)
    blf.draw(font_id, text)
     
class ModalDrawOperator(bpy.types.Operator):
    bl_idname = "view3d.modal_operator"
    bl_label = "Simple Modal View3D Operator"
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'ESC'}:
            print("Cancelled")
            bpy.types.SpaceView3D.draw_handler_remove(self._handler_3d, 'WINDOW')  
            bpy.types.SpaceView3D.draw_handler_remove(self._handler_2d, 'WINDOW')
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            
            self._handler_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')
            self._handler_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
            
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
            
    
                
                
    

    
    