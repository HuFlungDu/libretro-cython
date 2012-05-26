cdef extern from "windows.h":
	void *LoadLibrary(const_char_pointer)
	void *GetProcAddress(void *, const_char_pointer)
	int   FreeLibrary(void *)
