'''
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <jbaldwin8880@gmail.com> wrote this file. As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return Josiah Baldwin
 * ----------------------------------------------------------------------------
'''

cimport cdl
cimport cretro
from numpy cimport ndarray, NPY_USHORT, NPY_SHORT, NPY_UBYTE, NPY_BYTE,NPY_UINT,NPY_INT,npy_intp, import_array
import_array()

cdef extern from "libretro.h":
	ctypedef char* const_char_pointer "const char*"
	ctypedef void* const_void_pointer "const void*"
	ctypedef short int16_t "int16_t"
	ctypedef int16_t* const_int16_t_pointer "const int16_t*"
	ctypedef cretro.retro_game_info const_retro_game_info "const retro_game_info"
cdef extern from "unconst.cpp":
	void *unconst_void_pointer(const_void_pointer test)
	void *unconst_int16_t_pointer(const_int16_t_pointer test)
cdef extern from "numpy/arrayobject.h":
	cdef object PyArray_SimpleNewFromData(int nd, npy_intp *dims,
                                           int typenum, void *data)

from libcpp cimport bool


global environment_func
global video_refresh_func
global audio_sample_func
global audio_sample_batch_func
global input_poll_func
global input_state_func

environment_func=None
video_refresh_func=None
audio_sample_func=None
audio_sample_batch_func=None
input_poll_func=None
input_state_func=None

cdef class void_pointer_wrapper:
	cdef void *_ptr

cdef class data_array:
	cdef void *_ptr
	cdef str datatype
	cdef int length
	def __cinit__(self,datatype,length):
		self.datatype = datatype
		self.length = length

	def get_numpy(self):
		datasize = 1
		if self.datatype == "ushort":
			datasize = 2
			dtype = NPY_USHORT
		if self.datatype == "short":
			datasize = 2
			dtype = NPY_SHORT
		if self.datatype == "uchar":
			datasize = 1
			dtype = NPY_UBYTE
		if self.datatype == "char":
			datasize = 1
			dtype = NPY_BYTE
		if self.datatype == "uint":
			datasize = 4
			dtype = NPY_UINT
		if self.datatype == "int":
			datasize = 4
			dtype = NPY_INT
		cdef npy_intp size = self.length*datasize
		numpyarray = PyArray_SimpleNewFromData(1, &size, dtype, self._ptr)
		return numpyarray

cdef bool callenvironment(unsigned cmd, void *data):
	global environment_func
	cdef void_pointer_wrapper datawrapper
	datawrapper = void_pointer_wrapper()
	datawrapper._ptr = data
	return environment_func(cmd, datawrapper)

cdef void callvideorefresh(const_void_pointer data, unsigned width, unsigned height, size_t pitch):
	global video_refresh_func
	cdef data_array datawrapper
	datawrapper = data_array("ushort",height*width)
	datawrapper._ptr = unconst_void_pointer(data)
	video_refresh_func(datawrapper,width,height)

cdef void callaudiosample(int16_t left, int16_t right):
	global audio_sample_func
	audio_sample_func(left,right)

cdef size_t callaudiosamplebatch(const_int16_t_pointer data, size_t frames):
	global audio_sample_batch_func
	cdef data_array datawrapper
	datawrapper = data_array("ushort",frames)
	datawrapper._ptr = unconst_int16_t_pointer(data)
	return audio_sample_batch_func(datawrapper,frames)

cdef void callinputpoll():
	global input_poll_func
	input_poll_func()
cdef int16_t callinputstate(unsigned port, unsigned device, unsigned index, unsigned id):
	global input_state_func
	return input_state_func(port,device,index,id)
	
class retro_message(object):
	def __init__(self,msg,frames):
		self.msg = msg
		self.frames = frames

class retro_system_info(object):
	def __init__(self,library_name,library_version,valid_extensions,
				 need_fullpath, block_extract):
		self.library_name = library_name
		self.library_version = library_version
		self.valid_extensions = valid_extensions
		self.need_fullpath = need_fullpath
		self.block_extract = block_extract

class retro_game_geometry(object):
	def __init__(self,base_width,base_height,max_width, max_height,
				 aspect_ratio):
		self.base_width = base_width
		self.base_height = base_height
		self.max_width = max_width
		self.max_height = max_height
		self.aspect_ratio = aspect_ratio

class retro_system_timing(object):
	def __init__(self,fps,sample_rate):
		self.fps = fps
		self.sample_rate = sample_rate

class retro_system_av_info(object):
	def __init__(self,geometry, timing):
		self.geometry = geometry
		self.timing = timing

class retro_variable(object):
	def __init__(self,key,value):
		self.key = key
		self.value = value

class retro_game_info(object):
	def __init__(self,path, data,size,meta):
		self.path = path
		self.data = data
		self.size = size
		self.meta = meta

#cdef object get_pyclass_from_struct(instruct, tuple parameters, classtype):
	

cdef class CoreDef:
	cdef void *_ptr
	
	def __cinit__(self,libname):


		self._ptr = cdl.dlopen(libname,1)

		self.cretro_set_environment(callenvironment)
		self.cretro_set_video_refresh(callvideorefresh)
		self.cretro_set_audio_sample(callaudiosample)
		self.cretro_set_audio_sample_batch(callaudiosamplebatch)
		self.cretro_set_input_poll(callinputpoll)
		self.cretro_set_input_state(callinputstate)


	cdef void cretro_set_environment(self,cretro.retro_environment_t function):
		func = <void (*)(cretro.retro_environment_t)>cdl.dlsym(self._ptr, "retro_set_environment")
		func(function)
	cdef void cretro_set_video_refresh(self,cretro.retro_video_refresh_t function):
		func = <void (*)(cretro.retro_video_refresh_t)>cdl.dlsym(self._ptr, "retro_set_environment")
		func(function)
	cdef void cretro_set_audio_sample(self,cretro.retro_audio_sample_t function):
		func = <void (*)(cretro.retro_audio_sample_t)>cdl.dlsym(self._ptr, "retro_set_audio_sample")
		func(function)
	cdef void cretro_set_audio_sample_batch(self,cretro.retro_audio_sample_batch_t function):
		func = <void (*)(cretro.retro_audio_sample_batch_t)>cdl.dlsym(self._ptr, "retro_set_audio_sample_batch")
		func(function)
	cdef void cretro_set_input_poll(self,cretro.retro_input_poll_t function):
		func = <void (*)(cretro.retro_input_poll_t)>cdl.dlsym(self._ptr, "retro_set_input_poll")
		func(function)
	cdef void cretro_set_input_state(self,cretro.retro_input_state_t function):
		func = <void (*)(cretro.retro_input_state_t)>cdl.dlsym(self._ptr, "retro_set_input_state")
		func(function)
	cdef void cretro_init(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_init")
		func()
	cdef void cretro_deinit(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_deinit")
		func()
	cdef unsigned cretro_api_version(self):
		func = <unsigned (*)()>cdl.dlsym(self._ptr, "retro_api_version")
		return func()
	cdef void cretro_get_system_info(self, cretro.retro_system_info *info):
		func = <void (*)(cretro.retro_system_info*)>cdl.dlsym(self._ptr, "retro_get_system_info")
		func(info)
	cdef void cretro_get_system_av_info(self, cretro.retro_system_av_info *info):
		func = <void (*)(cretro.retro_system_av_info*)>cdl.dlsym(self._ptr, "retro_get_system_av_info")
		func(info)
	cdef void cretro_set_controller_port_device(self,unsigned port, unsigned device):
		func = <void (*)(unsigned, unsigned)>cdl.dlsym(self._ptr, "retro_set_controller_port_device")
		func(port,device)
	cdef cretro_reset(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_reset")
		func()
	cdef cretro_run(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_run")
		func()
	cdef size_t cretro_serialize_size(self):
		func = <size_t (*)()>cdl.dlsym(self._ptr, "retro_serialize_size")
		return func()
	cdef bool cretro_serialize(self, void *data, size_t size):
		func = <bool (*)(void*,size_t)>cdl.dlsym(self._ptr, "retro_serialize")
		return func(data,size)
	cdef bool cretro_unserialize(self,const_void_pointer data, size_t size):
		func = <bool (*)(const_void_pointer,size_t)>cdl.dlsym(self._ptr, "retro_unserialize")
		return func(data,size)
	cdef void cretro_cheat_reset(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_cheat_reset")
		func()
	cdef void cretro_cheat_set(self,unsigned index, bool enabled, const_char_pointer code):
		func = <void (*)(unsigned,bool,const_char_pointer)>cdl.dlsym(self._ptr, "retro_cheat_set")
		func(index, enabled, code)
	cdef bool cretro_load_game(self,const_retro_game_info *game):
		func = <bool (*)(const_retro_game_info*)>cdl.dlsym(self._ptr, "retro_load_game")
		return func(game)
	cdef bool cretro_load_game_special(self, unsigned game_type, const_retro_game_info *info, size_t num_info):
		func = <bool (*)(unsigned,const_retro_game_info*, size_t)>cdl.dlsym(self._ptr, "retro_load_game_special")
		return func(game_type,info,num_info)
	cdef void cretro_unload_game(self):
		func = <void (*)()>cdl.dlsym(self._ptr, "retro_unload_game")
		func()
	cdef unsigned cretro_get_region(self):
		func = <unsigned (*)()>cdl.dlsym(self._ptr, "retro_get_region")
		return func()
	cdef data_array cretro_get_memory_data(self,unsigned id):
		cdef data_array datawrapper
		size = self.cretro_get_memory_size(id)
		datawrapper = data_array("uchar",size)
		func = <void* (*)(unsigned)>cdl.dlsym(self._ptr, "retro_get_memory_data")
		datawrapper._ptr = func(id)
		return datawrapper
	cdef size_t cretro_get_memory_size(self,unsigned id):
		func = <size_t (*)(unsigned)>cdl.dlsym(self._ptr, "retro_get_memory_size")
		return func(id)

	def retro_get_memory_data(self,id):
		return self.cretro_get_memory_data(id).get_numpy()

	def retro_get_memory_size(self,id):
		return self.cretro_get_memory_size(id)

	def retro_get_region(self):
		return self.cretro_get_region()

	def retro_unload_game(self):
		self.cretro_unload_game()

	def retro_load_game(self,gameinfo):
		cdef cretro.retro_game_info info
		info = cretro.retro_game_info(<const_char_pointer>gameinfo.path,
									  <const_void_pointer>(<const_char_pointer>gameinfo.data),
									  gameinfo.size,
									  <const_char_pointer>gameinfo.meta)
		'''info.path = <const_char_pointer>gameinfo.path
		info.data = <const_void_pointer>(<const_char_pointer>gameinfo.data)
		info.size = gameinfo.size
		info.meta = <const_char_pointer>gameinfo.meta'''
		self.cretro_load_game(&info)

	def retro_cheat_reset(self):
		self.cretro_cheat_reset()

	def retro_cheat_set(self, index, enabled, code):
		self.cretro_cheat_set(index,enabled,<const_char_pointer>code)

	def retro_serialize(self,data, size):
		return self.cretro_serialize(<void *>data,size)

	def retro_unserialize(self,data,size):
		return self.cretro_unserialize(<const_void_pointer>data,size)

	def retro_serialize_size(self):
		return self.cretro_serialize_size()

	def retro_reset(self):
		self.cretro_reset()

	def retro_set_controller_port_device(self,port,device):
		self.cretro_set_controller_port_device(port,device)

	def retro_api_version(self):
		return self.cretro_api_version()

	def retro_get_system_info(self):
		cdef cretro.retro_system_info info
		self.cretro_get_system_info(&info)
		return retro_system_info(info.library_name,info.library_version,
						   info.valid_extensions, info.need_fullpath,
						   info.block_extract)

	def retro_get_system_av_info(self):
		cdef cretro.retro_system_av_info info
		self.cretro_get_system_av_info(&info)
		geometry = retro_game_geometry(info.geometry.base_width,
								 info.geometry.base_height,
								 info.geometry.max_width,
								 info.geometry.max_height,
								 info.geometry.aspect_ratio)
		timing = retro_system_timing(info.timing.fps,
							   info.timing.sample_rate)
		return retro_system_av_info(geometry,timing)

	def retro_init(self):
		self.cretro_init

	def retro_deinit(self):
		self.cretro_deinit

	def retro_set_environment(self, function):
		global environment_func
		environment_func = function	

	def retro_set_video_refresh(self, function):
		global video_refresh_func
		video_refresh_func = function	

	def retro_set_audio_sample(self, function):
		global audio_sample_func
		audio_sample_func = function	

	def retro_set_audio_sample_batch(self, function):
		global audio_sample_batch_func
		audio_sample_batch_func = function	

	def retro_set_input_poll(self, function):
		global input_poll_func
		input_poll_func = function	

	def retro_set_input_state(self, function):
		global input_state_func
		input_state_func = function	
		

