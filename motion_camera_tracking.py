#!BPY

bl_info = {
    'name': 'Export: Apple Motion (.motn)',
    'description': 'Export Camera Tracking Data to Apple Motion',
    'author': 'Andrew Rollo',
    'version': (1, 00),
    'blender': (2, 5, 8),
    'api': 36147,
    'location': 'File > Export > Apple Motion (.motn)',
    'category': 'Import-Export',
    "warning": "",
    "wiki_url": ""
    }

import time
import mathutils
from mathutils import Matrix
from math import degrees, radians, pi
#from bpy.Window import DrawProgressBar

exportfilepath = None

import bpy
from bpy.props import *
from bpy_extras.io_utils import ExportHelper

# AE and Shake struggle with lots of tracking points so this caps the number of static objects exported
max_static = 500

# having to check every object for every frame can be slow in a big scene so only exporting certain objects can help
limit_export = 0 # set to 1 to limit export to cameras and empties
export_types = ['Camera','Empty'] # set this list to objects you want to use as trackers
	
def fixObjName(name):
	return name.replace(".","_")

class ExportMOTN(bpy.types.Operator, ExportHelper):
	'''Export camera tracking data'''
	bl_idname = "export.motn"
	bl_label = "Export Apple Motion file"
	
	destination = EnumProperty(
        name="Destination Application",
        description="Select the application you are exporting to",
        items=[("AE","AfterFX","After Effects"),
               ("SHAKE","Shake","Shake"),
               ("MAYA","Maya","Maya"),
              ],
        default='AE')
		
	filename_ext = ".motn"
	filter_glob = StringProperty(default="*.motn", options={'HIDDEN'})
		
	@classmethod	
	def poll(cls, context):
		return context.active_object != None
	
	def execute(self, context):
		self.exportTracking(self.filepath)
		return {'FINISHED'}
	
	def draw(self, context):
		layout = self.layout
		
	def exportTracking(self, mafilename):
		sscale = 1 # scene scale
		if self.destination == 'AE': sscale = 100
		tscale = 1 # tracking point scale
		
		scene = bpy.context.scene
		
		oframe = scene.frame_current
		start_frame = scene.frame_start
		end_frame = scene.frame_end
		
		scene.frame_set(start_frame)
		
		num_frames = end_frame+1 - start_frame
					
		camobj = scene.camera
		camera = camobj.data
		
		context = scene.render
		xRes = context.resolution_x * context.resolution_percentage / 100
		yRes = context.resolution_y * context.resolution_percentage / 100
		aspX = context.pixel_aspect_x
		aspY = context.pixel_aspect_y
		aspect = xRes*aspX / float(yRes*aspY)
			
		t = {}
		t['header'] = []
		t['header'].append('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE ozxmlscene>\n<ozml version="3.0">\n\n')
		
		t['header'].append('<factory id="1" uuid="de1a9415beb34e5fb0964d1528bef14a">\n'
							'\t<description>Camera</description>\n'
							'\t<manufacturer>Apple</manufacturer>\n'
							'\t<version>1</version>\n'
							'</factory>\n')
	
		t['header'].append('<viewer subview="0">\n'
							'\t<cameraType>0</cameraType>\n'
							'\t<cameraName>Active Camera</cameraName>\n'
							'\t<panZoom camera="0" zoom="0.5" panX="236" panY="105" mode="1" centered="1"/>\n'
							'</viewer>\n\n')
		
		isntsc = 0
		if context.fps_base > 1: isntsc = 1
		t['header'].append('<scene>\n'
							'\t<sceneSettings>\n'
								'\t\t<width>%s</width>\n'
								'\t\t<height>%s</height>\n'
								'\t\t<duration>%s</duration>\n'
								'\t\t<frameRate>%s</frameRate>\n'
								'\t\t<fieldRenderingMode>0</fieldRenderingMode>\n'
								'\t\t<NTSC>%s</NTSC>\n'
								'\t\t<pixelAspectRatio>1</pixelAspectRatio>\n'
							'\t</sceneSettings>\n'
							'\t<currentFrame>1</currentFrame>\n'
							'\t<timeRange offset="0" duration="%s"/>\n'
							'\t<playRange offset="0" duration="%s"/>\n' %(xRes, yRes, end_frame, context.fps, isntsc, end_frame, end_frame))
									
		t['header'].append('<scenenode name="Project" id="746135465" factoryID="12" version="5">\n'
								'<scenenode name="Widget" id="746135466" factoryID="9" version="5">\n'
								'</scenenode>\n'
							'</scenenode>\n\n')
		
		# if aspect > 1: x is constant, otherwise y constant
		# constant comes from fov equations: fov = 2 * atan(aspect * 16.0 / camera.lens), aperturey = tan(fov/2)*camera.lens*2/25.4
		# tracking seems to work better using 1.25, change as needed
		#c = 16.0*2/25.4
		c = 1.25
		aperturex = min(c,c*aspect)
		aperturey = min(c,c/aspect)
		
		t['nodes'] = {}
		t['names'] = {}
		attrlist = ['_translateX','_translateY','_translateZ','_rotateX','_rotateY','_rotateZ','_scaleX','_scaleY','_scaleZ']
		for obj in scene.objects:
			if filter(lambda x:x in obj.layers, scene.layers )==[]: continue
			#if limit_export and obj.type not in export_types: continue
			name = fixObjName(obj.name)
			t['names'][obj.name] = name
			t['nodes'][name] = []
			for p in attrlist:
				t[name+"_null"+p] = {'function':[], 'data':{}}
			if obj.name == camera.name:
				t[name+'_fov'] = {'function':[], 'data':{}}
		
		#DrawProgressBar (0, "starting...")
		# this creates major memory usage as it makes a key for every object every frame in memory
		# so it iterates over each object and then cleans up redundant keyframes
		fnum = 0
		pvals = {}
		frames = scene.frame_end+1-scene.frame_start
		tt12 = 0
			
		for frame in range(scene.frame_start, scene.frame_end+1):
			scene.frame_set(frame)
			pc = (frame + scene.frame_start - 1)/float(frames)
			#DrawProgressBar (pc, "frame %s" %str(frame))
			for obj in scene.objects:
				if fnum>0 and limit_export and obj.type not in export_types: continue
				if not obj.name in t['names']: continue # quicker than re-checking layers
				name = t['names'][obj.name]
				
				matrix = obj.matrix_world
				
				mx = Matrix.Rotation(radians(-90), 4, "X")
		
				#tInv = matrix.inverted().to_translation()
				#tInvM = mathutils.Matrix([[1,0,0,tInv.x],[0,1,0,tInv.y],[0,0,1,tInv.z],[0,0,0,1]])
				#ttM = matrix.to_translation()
				#tM = mathutils.Matrix([[1,0,0,ttM.x],[0,1,0,ttM.y],[0,0,1,ttM.z],[0,0,0,1]])
			
				matrix = mx*matrix
				
				mt = matrix.to_translation()
				x = mt.x*sscale
				y = mt.y*sscale
				z = mt.z*sscale
				t[name+'_null_translateX']['data'][frame] = x
				t[name+'_null_translateY']['data'][frame] = y
				t[name+'_null_translateZ']['data'][frame] = z
				
				mr = matrix.to_euler('ZXY')
				rx = mr.x
				ry = mr.y
				rz = mr.z
				
				t[name+'_null_rotateX']['data'][frame] = rx
				t[name+'_null_rotateY']['data'][frame] = ry
				t[name+'_null_rotateZ']['data'][frame] = rz
				
				ms = matrix.to_scale()
				sx = ms.x
				sy = ms.y
				sz = ms.z
				t[name+'_null_scaleX']['data'][frame] = sx
				t[name+'_null_scaleY']['data'][frame] = sz
				t[name+'_null_scaleZ']['data'][frame] = sy
				
				if obj.name == camera.name:
					t[name+'_fov']['data'][frame] = degrees(camera.angle)
							
				if fnum==0:
					t[name+'_null_translateX']['default'] = x			
					t[name+'_null_translateY']['default'] = y
					t[name+'_null_translateZ']['default'] = z
					
					t[name+'_null_rotateX']['default'] = rx
					t[name+'_null_rotateY']['default'] = ry
					t[name+'_null_rotateZ']['default'] = rz
					
					t[name+'_null_scaleX']['default'] = sx
					t[name+'_null_scaleY']['default'] = sz
					t[name+'_null_scaleZ']['default'] = sy
					
					if obj.name == camera.name:
						t[name+'_fov']['default'] = degrees(camera.angle)
					
					if not name in pvals: pvals[name] = dict((p,[None,None]) for p in attrlist)
				del_last_frame = 0
				
				pvaldata = pvals[name]
				for p in attrlist:
					vv = t[name+"_null"+p]['data'][frame]
					if vv==pvaldata[p][0] and vv==pvaldata[p][1]: del_last_frame = 1
					pvaldata[p][1] = pvaldata[p][0]
					pvaldata[p][0] = vv
									
					if del_last_frame == 1:
						del t[name+"_null"+p]['data'][frame-1]
						if fnum==2: del t[name+"_null"+p]['data'][frame-2]
						if fnum==frames-1: del t[name+"_null"+p]['data'][frame]
						del_last_frame = 0
					
			fnum += 1
				
		t['footer'] = []
		static_objs = {}
		
		t['footer'].append('\n\t</scene>\n\n</ozml>')
				
		if not mafilename.endswith('.motn'):
			mafilename += '.motn'
		mafile = open(mafilename, 'w')
		for line in t['header']:
			mafile.write(line)
		num_static = 0
		for name,lines in t['nodes'].items():
			if name in static_objs and self.destination!='MAYA':
				num_static += 1
				if(num_static>max_static): continue

		idcounter = 10000
		for obj in scene.objects:
			if filter(lambda x:x in obj.layers, scene.layers )==[]: continue
			if limit_export and obj.type not in export_types: continue
			name = fixObjName(obj.name)

			pattrname = ""
			pattrnamelast = ""
			pattrsubname = ""
			if obj.name == camera.name:
				mafile.write('<scenenode name="%s" id="%s" factoryID="1">\n' %(name, str(idcounter)))
			else:
				mafile.write('<layer name="%s" id="%s">\n' %(name, str(idcounter)))
			mafile.write('<parameter name="Properties" id="1" flags="8589938704">\n')
			mafile.write('<parameter name="Transform" id="100">\n')
			idcounter += 1
			for p in attrlist:
				#for line in t[name+"_null"+p]['function']:
				#	mafile.write(line)
				if p.find("translate") > 0: pattrname = "Position"; pattrid = 101
				elif p.find("rotate") > 0: pattrname = "Rotation"; pattrid = 109
				else: pattrname = "Scale"; pattrid = 105
								
				if p.find("X") > 0: pattrsubname = "X"; pattrsubid = 1
				elif p.find("Y") > 0: pattrsubname = "Y"; pattrsubid = 2
				else: pattrsubname = "Z"; pattrsubid = 3
				
				if pattrname != pattrnamelast:
					mafile.write('<parameter name="%s" id="%s">\n' %(pattrname, str(pattrid)))
					pattrnamelast = pattrname
														
				mafile.write('<parameter name="%s" id="%s" default="%s" value="%s">\n'
								'<curve type="1">\n'
								'<numberOfKeypoints>%s</numberOfKeypoints>\n'
								%(str(pattrsubname), str(pattrsubid), str(t[name+"_null"+p]['default']),
								str(t[name+"_null"+p]['default']), str(len(t[name+"_null"+p]['data']))))
				for frame,val in t[name+"_null"+p]['data'].items():
					#mafile.write('%s %s ' %(frame, val))
					framespeed = 256 * context.fps
					mafile.write('\t<keypoint interpolation="1" flags="32">\n'
								'\t\t<time>%s</time>\n'
								'\t\t<value>%s</value>\n'
								'\t</keypoint>\n' %(frame-1, val))
				
				mafile.write('</curve>\n')
				mafile.write('</parameter>\n')
				if pattrsubname == 'Z':
					mafile.write('</parameter>\n')
				
				#del t[name+"_null"+p]['function']
				del t[name+"_null"+p]['data']
			mafile.write('</parameter>\n')
			mafile.write('</parameter>\n')
			if obj.name == camera.name:
				mafile.write('<parameter name="Object" id="2">\n')
				#mafile.write('\t<parameter name="Angle Of View" id="201" default="%s" value="%s"/>\n' %(degrees(camera.angle), degrees(camera.angle)))
				
				mafile.write('\t<parameter name="Angle Of View" id="201" default="%s" value="%s" >\n'
					'<curve type="1">\n'
					'<numberOfKeypoints>%s</numberOfKeypoints>\n'
					%(str(t[name+"_fov"]['default']), str(t[name+"_fov"]['default']), str(len(t[name+"_fov"]['data']))))
				
				for frame,val in t[name+"_fov"]['data'].items():
					framespeed = 256 * context.fps
					mafile.write('\t<keypoint interpolation="1" flags="32">\n'
								'\t\t<time>%s</time>\n'
								'\t\t<value>%s</value>\n'
								'\t</keypoint>\n' %(frame-1, val))
				
				mafile.write('</curve>\n')
				mafile.write('</parameter>\n')
				
				mafile.write('\t<parameter name="Camera Type" id="200" default="1" value="0"/>\n')
				mafile.write('</parameter>\n')
				mafile.write('</scenenode>\n')
			else:
				mafile.write('<parameter name="Object" id="2">')
				mafile.write('<parameter name="Type" id="307" default="0" value="1"/>')
				mafile.write('</parameter>')
				mafile.write('</layer>\n')
		for line in t['footer']:
			mafile.write(line)
		
		# free up all data
		del t
		del pvals
		scene.frame_set(oframe) # reset frame back to where it was

def menu_func(self, context):
	self.layout.operator(ExportMOTN.bl_idname, text="Apple Motion (.motn)")

def register():
	bpy.utils.register_class(ExportMOTN)
	bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
	bpy.utils.unregister_class(ExportMOTN)
	bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
	register()
