from libcpp cimport bool
cdef extern from "libretro.h":
	ctypedef char* const_char_pointer "const char*"
	ctypedef void* const_void_pointer "const void*"
	ctypedef short int16_t "int16_t"
	ctypedef int16_t* const_int16_t_pointer "const int16_t*"
	cdef struct retro_message:
		const_char_pointer msg
		unsigned frames

	cdef struct retro_system_info:

		const_char_pointer library_name
		const_char_pointer library_version

		const_char_pointer valid_extensions
                                  			
		bint        need_fullpath        	  
		bint        block_extract     		  
 
	cdef struct retro_game_geometry:
		unsigned base_width    				  
		unsigned base_height   				  
		unsigned max_width    				  
		unsigned max_height    				  

		float    aspect_ratio  				  

	cdef struct retro_system_timing:
		double fps             
		double sample_rate     

	cdef struct retro_system_av_info:

		retro_game_geometry geometry
		retro_system_timing timing

	cdef struct retro_variable:

		const_char_pointer key     	
		const_char_pointer value     	

	cdef struct retro_game_info:

		const_char_pointer path   	
		const_void_pointer data      	
		size_t      size 		
		const_void_pointer meta    

	ctypedef bool (*retro_environment_t)(unsigned cmd, void *data)
	ctypedef void (*retro_video_refresh_t)(const_void_pointer data, unsigned width, unsigned height, size_t pitch) 
	ctypedef void (*retro_audio_sample_t)(int16_t left, int16_t right)
	ctypedef size_t (*retro_audio_sample_batch_t)(const_int16_t_pointer data, size_t frames)
	ctypedef void (*retro_input_poll_t)()
	ctypedef int16_t (*retro_input_state_t)(unsigned port, unsigned device, unsigned index, unsigned id)
