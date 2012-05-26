cdef extern from "dlfcn.h":
	ctypedef char * const_char_pointer "const char *"
	void *dlopen(const_char_pointer, int)
	void *dlsym(void *, const_char_pointer)
	int   dlclose(void *)
	char *dlerror()
