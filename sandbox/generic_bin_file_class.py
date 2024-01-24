'''
Purpose:
'''

###################
##### IMPORTS #####
###################

import struct

##############################
##### GENERIC FILE CLASS #####
##############################

class Generic_Bin_File_Class():
    '''
    Base class for reading, modifying, and saving a binary file.
    '''
    def __init__(self, file_path:str):
        '''
        Constructor
        '''
        self._file_path = file_path
        self._file_content = None
        self._read_file()

    ###################
    ##### NUMBERS #####
    ###################

    def _possible_negative(self, int_val:int, byte_count:int):
        '''
        Interprets the raw byte array integer whether it would be considered a negative integer.
        '''
        max_val = 0x1 << (byte_count * 8)
        if(int_val > (max_val / 2)):
            int_val -= max_val
        return int_val
    
    def _possible_neg_to_pos(self, int_val:int, byte_count:int):
        '''
        Returns an integer as a value that can be inserted for a byte array.
        '''
        if(int_val >= 0):
            return int_val
        max_val = 0x1 << (byte_count * 8)
        int_val += max_val
        return int_val

    ### INTEGERS

    def _read_bytes_as_int(self, index_start:int, byte_count:int, check_for_negative:bool=False):
        '''
        Turns a byte or set of bytes into an integer.
        Revisit this, might be able to say signed=check_for_negative?
        '''
        this_int:int = int.from_bytes(self._file_content[index_start:index_start+byte_count])
        if(check_for_negative):
            this_int:int = self._possible_negative(this_int, byte_count)
        return this_int
    
    def _write_bytes_from_int(self, index_start:int, int_val:int, byte_count:int):
        '''
        Writes a byte or set of bytes from an integer.
        '''
        int_val:int = self._possible_neg_to_pos(int_val, byte_count)
        self._file_content[index_start:index_start+byte_count] = int_val.to_bytes(byte_count)
    
    ### FLOATS

    def _read_bytes_as_float(self, index_start:int):
        '''
        Turns a byte or set of bytes into a float.
        '''
        float_bytes:bytes = self._file_content[index_start:index_start+0x04]
        this_float:float = struct.unpack('!f', float_bytes)[0]
        return this_float

    def _write_bytes_from_float(self, index_start:int, float_val:float):
        '''
        Writes a byte or set of bytes from a float.
        '''
        self._file_content[index_start:index_start+4] = struct.pack('!f', float_val)

    ### BITS
    
    ###################
    ##### STRINGS #####
    ###################
    
    ### HEX STRINGS
    # These are typically used for debugging

    def _leading_zeros(self, str_val:str, byte_count:int):
        '''
        For any hexadecimal represented by a string, this function adds leading
        zeros until the string matches the length in bytes.
        '''
        str_val:str = str_val.zfill(byte_count * 2).upper()
        return str_val
    
    def _read_bytes_as_hex_str(self, index_start:int, byte_count:int):
        '''
        Turns a byte or set of bytes into a hexadecimal string.
        '''
        hex_str_bytes:bytes = self._file_content[index_start:index_start+byte_count]
        hex_str_val:str = self._leading_zeros(str(bytes(hex_str_bytes).hex()), byte_count)
        return hex_str_val
    
    def _write_bytes_from_hex_str(self, index_start:int, hex_str_val:str):
        '''
        Writes a byte or set of bytes from a hexadecimal string.
        '''
        byte_count:int = len(hex_str_val) // 2
        self._file_content[index_start:index_start+byte_count] = bytearray.fromhex(hex_str_val)
    
    ### LATIN STRINGS

    def _read_bytes_as_str(self, index_start:int, byte_count:int):
        '''
        Turns a byte or set of bytes into a latin-decoded string.
        '''
        string_bytes:bytes = self._file_content[index_start:index_start+byte_count]
        this_str:str = str(string_bytes, encoding="latin-1")
        return this_str
    
    def _write_bytes_from_str(self, index_start:int, str_val:str):
        '''
        Writes a byte or set of bytes from a latin-decoded string.
        '''
        byte_count:int = len(str_val)
        self._file_content[index_start:index_start+byte_count] = bytes(str_val, 'latin-1')

    #######################
    ##### CONVERSIONS #####
    #######################

    def _convert_int_to_hex_str(self, int_val:int, byte_count:int=0):
        '''
        Turns an integer into a hexadecimal string.
        '''
        str_val:str = self._leading_zeros(str(hex(int_val))[2:], byte_count)
        return str_val
    
    ##########################
    ##### MAIN FUNCTIONS #####
    ##########################
    
    def _read_file(self):
        '''
        Reads a file as a byte array.
        '''
        with open(self._file_path, "rb+") as bin_file:
            self._file_content = bytearray(bin_file.read())
    
    def _save_changes(self, file_path:str|None=None):
        '''
        Writes a file in binary mode.
        '''
        if(file_path is None):
            file_path = self._file_path
        with open(file_path, "wb+") as bin_file:
            bin_file.write(self._file_content)
