'''
Purpose:
* Class for running the compression and decompression algorithms on files.
'''

###################
##### IMPORTS #####
###################

import os
import zlib
import gzip
from shutil import copy
from math import ceil
import subprocess

from sandbox.generic_bin_file_class import Generic_Bin_File_Class

#############################
##### COMPRESSION CLASS #####
#############################

class COMPRESSION_CLASS(Generic_Bin_File_Class):
    '''
    Runs the compression and decompression algorithms on files.
    '''
    def __init__(self, file_name:str, file_type:str):
        '''
        Constructor
        '''
        ### CONSTANTS ###
        self._WBITS:int = -15
        # self._GZIP_PATH:str = f"{os.path.dirname(os.path.abspath(__file__))}/GZIP.EXE"
        self._GZIP_PATH:str = f"sandbox/patching/GZIP.EXE"
        self._EXTRACTED_FILES_DIR:str = "sandbox/extracted_files/"
        self._COMPRESSED_BIN_EXTENSION:str = "-Compressed.bin"
        self._DECOMPRESSED_BIN_EXTENSION:str = "-Decompressed.bin"
        self._RAW_BIN_EXTENSION:str = "-Raw.bin"
        self._DECOMPRESSED_STR:str = "Decompressed"
        self._COMPRESSED_STR:str = "Compressed"
        self._RAW_STR:str = "Raw"
        self._TEMPORARY_BIN:str = "tmp.bin"
        self._ASSET_FILE:str = "Asset"
        self._ASSEMBLY_FILE:str = "Assembly"
        self._PADDING_BYTE:str = "Padding Byte"
        self._PADDING_INTERVAL:str = "Padding Interval"
        self._PADDING_DICT:dict = {
            self._ASSET_FILE: {
                self._PADDING_BYTE: b"\xAA",
                self._PADDING_INTERVAL: 0x08,
            },
            self._ASSEMBLY_FILE: {
                self._PADDING_BYTE: b"\x00",
                self._PADDING_INTERVAL: 0x10,
            },
        }
        self._SKIP_ASSET_POINTERS:list = [
            "78B4", "78B8",
        ]

        ### VARIABLES ###
        self._file_name:str = file_name
        self._file_type:str = file_type
        self._file_path:str = None
        self._file_content = None
        self._determine_file_path(file_type)
        self._read_file()

    ###################
    ##### GENERIC #####
    ###################
    
    def _determine_file_path(self, file_type:str):
        '''
        Sets the current file's path based on the file extention.
        '''
        if(file_type == self._COMPRESSED_STR):
            file_ext = self._COMPRESSED_BIN_EXTENSION
        elif(file_type == self._DECOMPRESSED_STR):
            file_ext = self._DECOMPRESSED_BIN_EXTENSION
        elif(file_type == self._RAW_STR):
            file_ext = self._RAW_BIN_EXTENSION
        else:
            raise Exception("ERROR: _determine_file_path: Unknown File Extension")
        self._file_path:str = self._EXTRACTED_FILES_DIR + self._file_name + file_ext

    ######################
    ##### DECOMPRESS #####
    ######################
    
    def _check_extracted_file_type(self):
        '''
        Determines whether the current file is empty, compressed, or decompressed.
        '''
        if(len(self._file_content) == 0):
            return self._DECOMPRESSED_STR
        elif(self._file_name in self._SKIP_ASSET_POINTERS):
            return self._RAW_STR
        return self._COMPRESSED_STR

    def _generate_cic_result(self,
            chl:list, rsp:list, list_len:int):
        '''
        Pass
        '''
        key = 0xB
        lut0 = [
            0x4, 0x7, 0xA, 0x7, 0xE, 0x5, 0xE, 0x1,
            0xC, 0xF, 0x8, 0xF, 0x6, 0x3, 0x6, 0x9
        ]
        lut1 = [
            0x4, 0x1, 0xA, 0x7, 0xE, 0x5, 0xE, 0x1,
            0xC, 0x9, 0x8, 0x5, 0x6, 0x3, 0xC, 0x9
        ]
        lut = lut0
        for i in range(list_len):
            rsp[i] = ((key + 5 * chl[i]) & 0xF)
            key = lut[rsp[i]]
            sgn = (rsp[i] >> 3) & 0x1
            if(sgn == 1):
                mag = rsp[i]
            else:
                mag = rsp[i] & 0x7
            if(mag % 3 == 1):
                mod = sgn
            else:
                mod = 1 - sgn
            if(lut == lut1 and (rsp[i] == 0x1 or rsp[i] == 0x9)):
                mod = 1
            if(lut == lut1 and (rsp[i] == 0xB or rsp[i] == 0xE)):
                mod = 0
            if(mod == 1):
                lut = lut1
            else:
                lut = lut0
        return rsp

    def _decrypt_file(self,
            asset_id:int, file_content:bytearray, file_size:int):
        '''
        Pass
        '''
        rsp = [0] * 0x20
        input_key = [0] * 0x10
        key = asset_id - 0x995
        a2 = 0x10
        for v1 in range(0, 0xE, 0x2):
            t6 = key >> v1
            t7 = a2 - v1
            t8 = key << t7
            t9 = t6 | t8
            input_key[v1] = t9 & 0xFF
            input_key[v1 + 1] = (t9 & 0xFF00) & 0xFF
        input_key[0x0E] = 0x00
        input_key[0x0F] = 0x02
        nibble_key_version = [0] * 0x20
        for x in range(0x20):
            if(x % 2):
                nibble_key_version[x] = input_key[x // 2] & 0xF
            else:
                nibble_key_version[x] = (input_key[x // 2] >> 4) & 0xF
        rsp = self._generate_cic_result(nibble_key_version, rsp, 0x20 - 2)
        rsp[0x20 - 2] = 0x0
        rsp[0x20 - 1] = 0x0
        cic_value = [0] * 0x10
        for x in range(0, 0x20, 2):
            cic_value[x // 2] = (rsp[x] << 4) | rsp[x + 1]
        new_file_content = file_content
        for x in range(file_size):
            value = file_content[x]
            new_file_content[x] = (value ^ cic_value[x % 0xE])
        return new_file_content


    def _decompress_file(self, asset_id:int, decrypt_bool:bool=False):
        '''
        Creates a decompressed version of a compressed file.
        '''
        # Remove Decompress Size & Padding
        for byte_count, curr_byte in enumerate(reversed(self._file_content)):
            if(curr_byte != 0xAA):
                break
        file_content = self._file_content[2:-byte_count]
        if(decrypt_bool):
            file_size:int = len(file_content)
            file_content= self._decrypt_file(asset_id, file_content, file_size)
        # ZLIB Decompress
        compressor_obj = zlib.decompressobj(wbits=self._WBITS)
        decompressed_file_bytes = compressor_obj.decompress(file_content)
        decompressed_file_path:str = self._EXTRACTED_FILES_DIR + self._file_name + self._DECOMPRESSED_BIN_EXTENSION
        with open(decompressed_file_path, "wb+") as decompressed_file:
            decompressed_file.write(decompressed_file_bytes)

    def _copy_compressed_to_raw(self):
        '''
        Copies an extracted file as a raw file.
        '''
        raw_file_path:str = self._EXTRACTED_FILES_DIR + self._file_name + self._RAW_BIN_EXTENSION
        copy(self._file_path, raw_file_path)
    
    ####################
    ##### COMPRESS #####
    ####################
    
    def _compress_file(self, padding_byte:bytes, padding_interval:int):
        '''
        Pass
        '''
        # CONSTANTS
        decompressed_path:str = self._EXTRACTED_FILES_DIR + self._file_name + self._DECOMPRESSED_BIN_EXTENSION
        temp_path:str = self._EXTRACTED_FILES_DIR + "temp" + self._COMPRESSED_BIN_EXTENSION
        compressed_path:str = self._EXTRACTED_FILES_DIR + self._file_name + self._COMPRESSED_BIN_EXTENSION
        gzip_command:str = f'"{self._GZIP_PATH}" -c -9 "{decompressed_path}" >> "{temp_path}"'
        # FILE SIZE
        file_size:int = len(self._file_content)
        compressed_header:int = ceil(file_size / 0x10)
        print(self._convert_int_to_hex_str(compressed_header, 2))
        # GZIP
        subprocess.Popen(gzip_command, universal_newlines=True, shell=True).communicate()
        # READ TEMP FILE
        with open(temp_path, "rb") as temp_file:
            temp_content = temp_file.read()[:-8] # Remove Checksum
            curr_index:int = temp_content.find(b'\x2E\x62\x69\x6E\x00')
            temp_content = temp_content[curr_index + 0x5:]
        # COMPRESSED FILE
        compressed_length:int = len(temp_content) + 0x2
        with open(compressed_path, "wb+") as compressed_file:
            compressed_file.write(compressed_header.to_bytes(length=2, byteorder='big'))
            compressed_file.write(temp_content)
            while(compressed_length % padding_interval):
                compressed_file.write(padding_byte)
                compressed_length += 1
        # REMOVE TEMP FILE
        os.remove(temp_path)
        return compressed_length

    ##########################
    ##### MAIN FUNCTIONS #####
    ##########################

    def decompress_file_main(self, asset_id:int, decrypt_bool:bool):
        '''
        Runs the main workflow for prepping a file for modifying.
        The file may be decompressed or copied as raw.
        '''
        file_type:str = self._check_extracted_file_type()
        if(file_type == self._COMPRESSED_STR):
            self._decompress_file(asset_id, decrypt_bool)
        elif(file_type == self._DECOMPRESSED_STR):
            self._copy_compressed_to_raw()
    
    def compress_file_main(self, file_category:str):
        '''
        Pass
        '''
        padding_byte:bytes = self._PADDING_DICT[file_category][self._PADDING_BYTE]
        padding_interval:int = self._PADDING_DICT[file_category][self._PADDING_INTERVAL]
        if(self._file_type == self._DECOMPRESSED_STR):
            compressed_content_length:int = self._compress_file(padding_byte, padding_interval)
        elif(self._file_type == self._RAW_STR):
            compressed_content_length:int = self._copy_raw_to_compressed()
        else:
            raise Exception(f"Error: compress_file_main: Unidentified file type '{self._file_type}'")
        return compressed_content_length

################
##### MAIN #####
################

if __name__ == '__main__':
    ##############
    # Decompress #
    ##############

    # file_name:str = "6c2c"
    # print(f"File Name: 6C2C Object Model: Chuffy")
    # compression_obj = COMPRESSION_CLASS(file_name, "Compressed")
    # compression_obj.decompress_file_main()

    # file_name:str = "7960"
    # print(f"File Name: 7960 Map Setup: CS - 'Two Years have Passed'")
    # compression_obj = COMPRESSION_CLASS(file_name, "Compressed")
    # compression_obj.decompress_file_main(asset_id=0x9F6, decrypt_bool=True)

    ############
    # Compress #
    ############

    file_name:str = "7960-GED"
    print(f"File Name: 7960 Map Setup: CS - 'Two Years have Passed'")
    compression_obj = COMPRESSION_CLASS(file_name, "Decompressed")
    compression_obj.compress_file_main(compression_obj._ASSET_FILE)