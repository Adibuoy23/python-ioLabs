from hid.cparser import *

import ctypes

def test_tokenizer():
    t=tokenizer('void* my_fn(void)')
    assert not t.empty()
    assert t.next() == 'void'
    assert t.next() == '*'
    assert t.next() == 'my_fn'
    assert t.next() == '('
    assert t.next() == 'void'
    assert t.next() == ')'
    assert t.empty()

def test_tokenizer_keywords():
    define('long long', ctypes.c_longlong)
    t=tokenizer('void* my_fn(long long)')
    assert not t.empty()
    assert t.next() == 'void'
    assert t.next() == '*'
    assert t.next() == 'my_fn'
    assert t.next() == '('
    assert t.next() == 'long long'
    assert t.next() == ')'
    assert t.empty()


def test_parse_c_def_fn_ptr():
    fn=parse_c_def('CFRunLoopSourceRef (*GetInterfaceAsyncEventSource)(void *self)')
    assert fn.name == 'GetInterfaceAsyncEventSource'
    
    return_type=fn.return_type
    assert return_type.name == ''
    assert return_type.type_name == 'CFRunLoopSourceRef'
    
    param_list = fn.param_list
    assert len(param_list) == 1
    
    param=param_list[0]
    assert param.name == 'self'
    assert param.type_name == 'void*'

def test_parse_c_def_fn():
    fn=parse_c_def('CFRunLoopSourceRef GetInterfaceAsyncEventSource(void *self)')
    assert fn.name == 'GetInterfaceAsyncEventSource'
    
    return_type=fn.return_type
    assert return_type.name == ''
    assert return_type.type_name == 'CFRunLoopSourceRef'
    
    param_list = fn.param_list
    assert len(param_list) == 1
    
    param=param_list[0]
    assert param.name == 'self'
    assert param.type_name == 'void*'

def test_parse_c_def_var():
    var=parse_c_def('int i')
    assert var.type_name == 'int'
    assert var.name == 'i'
    
    var=parse_c_def('int* i')
    assert var.type_name == 'int*'
    assert var.name == 'i'
    
    var=parse_c_def('int *i')
    assert var.type_name == 'int*'
    assert var.name == 'i'

def test_parse_c_def_var_type():
    var=parse_c_def('int')
    assert var.type_name == 'int'
    print var.name
    assert var.name == ''
    
    var=parse_c_def('void')
    assert var.type_name == 'void'
    assert var.name == ''
    
    var=parse_c_def('void*')
    assert var.type_name == 'void*'
    print var.name
    assert var.name == ''

def test_parse_c_def_void_ctype():
    assert parse_c_def('void').ctype is None
    assert parse_c_def('void*').ctype  == ctypes.c_void_p
    assert parse_c_def('void**').ctype == ctypes.POINTER(ctypes.c_void_p)

def test_parse_c_def_int_ctype():
    assert parse_c_def('int').ctype   == ctypes.c_int
    assert parse_c_def('int*').ctype  == ctypes.POINTER(ctypes.c_int)
    assert parse_c_def('int**').ctype == ctypes.POINTER(ctypes.POINTER(ctypes.c_int))

def test_parse_basic_types():
    assert parse_c_def('void').ctype is None
    assert parse_c_def('void*').ctype == ctypes.c_void_p
    assert parse_c_def('char').ctype == ctypes.c_char
    assert parse_c_def('wchar_t').ctype == ctypes.c_wchar
    assert parse_c_def('unsigned char').ctype == ctypes.c_ubyte
    assert parse_c_def('short').ctype == ctypes.c_short
    assert parse_c_def('unsigned short').ctype == ctypes.c_ushort
    assert parse_c_def('int').ctype == ctypes.c_int
    assert parse_c_def('unsigned int').ctype == ctypes.c_uint
    assert parse_c_def('long').ctype == ctypes.c_long
    assert parse_c_def('unsigned long').ctype == ctypes.c_ulong
    assert parse_c_def('long long').ctype == ctypes.c_longlong
    assert parse_c_def('unsigned long long').ctype == ctypes.c_ulonglong
    assert parse_c_def('float').ctype == ctypes.c_float
    assert parse_c_def('double').ctype == ctypes.c_double
    assert parse_c_def('char*').ctype == ctypes.c_char_p
    assert parse_c_def('wchar_t*').ctype == ctypes.c_wchar_p

def test_parse_c_def_function_ctype():
    assert parse_c_def('void hello(int)').ctype       == ctypes.CFUNCTYPE(None, ctypes.c_int)
    assert parse_c_def('void hello(int name)').ctype  == ctypes.CFUNCTYPE(None, ctypes.c_int)
    assert parse_c_def('int hello(int name)').ctype   == ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    assert parse_c_def('int hello(void *name)').ctype == ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)
    assert parse_c_def('int hello(void* name)').ctype == ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)

def test_parse_c_def_function_cstruct():
    assert parse_c_def('void hello(int)').cstruct == ('hello', ctypes.CFUNCTYPE(None, ctypes.c_int))
    assert parse_c_def('int var').cstruct == ('var', ctypes.c_int)
    assert parse_c_def('void *p').cstruct == ('p', ctypes.c_void_p)