'''
Purpose:
* Class for running the ROM extracting and inserting workflows.
'''

###################
##### IMPORTS #####
###################

import os
import subprocess
import zlib

from sandbox.generic_bin_file_class import Generic_Bin_File_Class
from sandbox.patching.compression_class import COMPRESSION_CLASS

########################
##### BT ROM CLASS #####
########################

class BT_ROM_CLASS(Generic_Bin_File_Class):
    '''
    Runs the ROM extracting and inserting workflows.
    '''
    def __init__(self, file_path:str):
        '''
        Constructor
        '''
        ### SUPER ###
        super().__init__(file_path)

        ### CONSTANTS ###
        self._ASSET_TABLE_START_INDEX:int = 0x5188
        # self._ASSET_TABLE_END_INDEX:int = 0x11A24
        self._ASSET_ID_START:int = 0x000
        self._ASSET_ID_END:int = 0x3666
        self._ASSET_TABLE_INTERVAL:int = 0x4
        self._ASSET_TABLE_OFFSET:int = 0x12B24
        self._ROM_END_INDEX:int = 0x0
        self._ASM_END:int = 0x0
        self._CIC = 0xDF26F436
        self._CRC1_INDEX_START:int = 0x10
        self._CRC2_INDEX_START:int = 0x14
        self._CHECK_ROM_START_INDEX:int = 0x1000
        self._CHECK_ROM_END_INDEX:int = 0x101000
        self._EXTRACTED_FILES_DIR:str = "sandbox/extracted_files/"
        self._BIN_EXTENSION:str = ".bin"
        self._COMPRESSED_BIN_EXTENSION:str = f"-Compressed{self._BIN_EXTENSION}"
        self._DECOMPRESSED_BIN_EXTENSION:str = f"-Decompressed{self._BIN_EXTENSION}"
        self._RAW_BIN_EXTENSION:str = f"-Raw{self._BIN_EXTENSION}"
        self._FILE_EMPTY_STR:str = "File Empty"
        self._DECOMPRESSED_STR:str = "Decompressed"
        self._COMPRESSED_STR:str = "Compressed"
        self._RAW_STR:str = "Raw"
        self._ASSET_FILE:str = "Asset"
        self._ASSEMBLY_FILE:str = "Assembly"
        ### SETUP ###
        self._create_extracted_files_directory()
    
    #################
    ##### SETUP #####
    #################
        
    def _create_extracted_files_directory(self):
        '''
        Creates an extracted files directory.
        '''
        print(f"INFO: _create_extracted_files_directory: Creating extracted files directory...")
        if(not os.path.exists(self._EXTRACTED_FILES_DIR)):
            os.mkdir(self._EXTRACTED_FILES_DIR)
        print(f"INFO: _create_extracted_files_directory: Creation complete!")

    ################################
    ##### EXTRACT & DECOMPRESS #####
    ################################

    def _asset_pointer_to_address(self, pointer_index_start:int):
        '''
        Pass
        '''
        asset_index:int = (self._read_bytes_as_int(pointer_index_start, 4) >> 8) * 4 + self._ASSET_TABLE_OFFSET
        return asset_index

    def _extract_asset_by_pointer(self, pointer_index_start:int, file_name:str):
        '''
        Pass
        '''
        asset_index_start:int = self._asset_pointer_to_address(pointer_index_start)
        asset_index_end:int = self._asset_pointer_to_address(pointer_index_start + self._ASSET_TABLE_INTERVAL)
        file_path:str = f"{self._EXTRACTED_FILES_DIR}{file_name}{self._COMPRESSED_BIN_EXTENSION}"
        with open(file_path, "wb+") as comp_file:
            comp_file.write(self._file_content[asset_index_start:asset_index_end])
        debug_pointer_index_start:str = self._convert_int_to_hex_str(pointer_index_start, byte_count=4)
        debug_asset_index_start:str = self._convert_int_to_hex_str(asset_index_start, byte_count=4)
        debug_asset_index_end:str = self._convert_int_to_hex_str(asset_index_end, byte_count=4)
        return debug_pointer_index_start, debug_asset_index_start, debug_asset_index_end

    def extract_asset_table_pointers(self):
        '''
        Pass
        '''
        for asset_id in range(
                self._ASSET_ID_START,
                self._ASSET_ID_END,
                self._ASSET_TABLE_INTERVAL):
            try:
                pointer_index_start:int = self._ASSET_TABLE_START_INDEX + 4 * asset_id
                if(asset_id >= 0x9F4 and asset_id < 0xB34):
                    continue
                if(asset_id % 500 == 0):
                    asset_id_hex_str:str = self._convert_int_to_hex_str(asset_id, 2)
                    pointer_hex_str:str = self._convert_int_to_hex_str(pointer_index_start, byte_count=4)
                    print(f"DEBUG: extract_asset_table_pointers: Asset Id '{asset_id_hex_str}' -> Pointer Address'{pointer_hex_str}'")
                file_name:str = self._convert_int_to_hex_str(pointer_index_start)
                debug_pointer_index_start, debug_asset_index_start, debug_asset_index_end =\
                    self._extract_asset_by_pointer(pointer_index_start, file_name)
                compressed_obj = COMPRESSION_CLASS(file_name, self._COMPRESSED_STR)
                decrypt_bool:bool = False
                compressed_obj.decompress_file_main(asset_id, decrypt_bool)
            except zlib.error as err:
                print(f"debug_pointer_index_start: {debug_pointer_index_start}")
                print(f"\tdebug_asset_index_start: {debug_asset_index_start}")
                print(f"\tdebug_asset_index_end: {debug_asset_index_end}")
                raise err

    #####################################
    ##### COMPRESSION AND INSERTION #####
    #####################################

    ####################
    ##### CHECKSUM #####
    ####################

    def _unsigned_long(self, int_val:int):
        '''
        Returns the last four bytes of the given integer.
        '''
        return int_val & 0xFFFFFFFF
    
    def _rotate_left(self, j:int, b:int):
        '''
        Rotate left machine language function.
        '''
        return self._unsigned_long(j << b) | (j >> (-b & 0x1F))

    def _calculate_new_crc(self):
        '''
        Calculates the new CRC checksum values for Banjo-Tooie.
        '''
        t1 = t2 = t3 = t4 = t5 = t6 = self._CIC
        for index_count, check_index in enumerate(range(self._CHECK_ROM_START_INDEX, self._CHECK_ROM_END_INDEX, 0x4)):
            d = self._read_bytes_as_int(check_index, byte_count=4)
            t6d = self._unsigned_long(t6 + d)
            if(t6d < t6):
                t4 = self._unsigned_long(t4 + 1)
            t6 = t6d
            t3 ^= d
            r = self._rotate_left(d, d & 0x1F)
            t5 = self._unsigned_long(t5 + r)
            if(t2 > d):
                t2 ^= r
            else:
                t2 ^= t6 ^ d
            byte_place:int = 0x0040 + 0x0710 + (index_count & 0xFF)
            byte_place_val:int = self._read_bytes_as_int(byte_place, byte_count=4)
            t1 = t1 + (self._unsigned_long(byte_place_val) ^ d)
        crc1 = self._unsigned_long(t6 ^ t4 ^ t3)
        crc2 = self._unsigned_long(t5 ^ t2 ^ t1)
        print(f"CRC1: {self._convert_int_to_hex_str(crc1, byte_count=4)}")
        print(f"CRC2: {self._convert_int_to_hex_str(crc2, byte_count=4)}")
        # self._write_bytes_from_int(self._CRC1_INDEX_START, crc1, 4)
        # self._write_bytes_from_int(self._CRC2_INDEX_START, crc2, 4)

    def _run_crc_tool(self, new_file_path:str):
        '''
        Pass
        '''
        cmd =  f"{os.getcwd()}/sandbox/patching/rn64crc.exe -u {new_file_path}"
        subprocess.Popen(cmd.split(),shell=True).communicate()

    ##########################
    ##### POST FUNCTIONS #####
    ##########################

    def save_as_new_rom(self, new_file_path:str):
        '''
        Saves the Banjo-Tooie Rom to new destination.
        '''
        print(f"INFO: save_as_new_rom: Saving new ROM to '{new_file_path}'...")
        self._save_changes(new_file_path)
        print(f"INFO: save_as_new_rom: New ROM saved!")
    
    def clear_extracted_files_dir(self, filter:str):
        '''
        Removes bin files from the extracted files directory that end with a certain filter
        '''
        print(f"INFO: _clear_extracted_files_dir: Cleaning files ending in {filter}...")
        bin_files_list = os.listdir(self._EXTRACTED_FILES_DIR)
        for file_name in bin_files_list:
            if(file_name.endswith(filter)):
                os.remove(os.path.join(self._EXTRACTED_FILES_DIR, file_name))
        print(f"INFO: _clear_extracted_files_dir: Cleaning complete!")

################
##### MAIN #####
################

if __name__ == '__main__':
    file_path:str = "C:/Users/Cyrus/Documents/VS_Code/Banjo_Tooie_Sandbox/Banjo-Tooie.z64"
    new_file_path:str = "C:/Users/Cyrus/Documents/VS_Code/Banjo_Tooie_Sandbox/Banjo-Tooie-TEST.z64"
    bt_rom = BT_ROM_CLASS(file_path)
    bt_rom.clear_extracted_files_dir(bt_rom._BIN_EXTENSION)
    bt_rom.extract_asset_table_pointers()
    # bt_rom.append_asset_table_pointers()
    # bt_rom._calculate_new_crc()
    bt_rom.save_as_new_rom(new_file_path)
    bt_rom._run_crc_tool(new_file_path)
    # bt_rom.clear_extracted_files_dir(bt_rom._BIN_EXTENSION)