#
# @authors:
# Juan Reyes <reyes@ucsd.edu>
# Malcolm White <mcwhite@ucsd.edu>
#
# @usage:
#   Create:
#      element = segd(path)             # Default mode
#      element = segd(path,debug=True)  # Enable Debug mode. Verbose output
#   Access:
#      print element                           # Nice print of values
#      element.info                            # return string value of description
#      element.path                            # return string value for path
#      element.file                            # return string value for filename
#      element.list()                          # return list of databases
#      element.purge(db)                       # cleanup object.
#
#   Note:
#
#

from __main__ import *
from struct import unpack

class SegDException(Exception):
    """
    New exception for the SEGD class.
    Just empty for now.
    """
    pass

class SegD:

    def __init__(self, path, debug=False):
        self.type = False
        self.path = os.path.abspath(path)
        self.debug = debug

        self.segdfile = open(self.path, 'rb')
        self.last_byte_read = 0
        #self._read_storage_unit_label()
        self._read_receiver_record_header_general_header_block_1()
        self._read_receiver_record_header_general_header_block_2()
        self._read_channel_set_descriptor()
        self.segdfile.close()


    def __str__(self):
        """
        end-user/application display of content using print() or log.msg()
        """
        #s = 'Storage Unit Label\n------------------\n'
        #s = '%sStorage unit sequence number: %s\n' \
        #        % (s, self.storage_unit_sequence_number)
        #s = '%sFairfield revision: %s\n' \
        #        % (s, self.fairfield_revision_ff1_5)
        #s = '%sStorage unit structure: %s\n' \
        #        % (s, self.storage_unit_structure)
        #s = '%sBinding edition: %s\n' \
        #        % (s, self.binding_edition)
        #s = '%sMaximum block size: %s\n' \
        #        % (s, self.maximum_block_size)
        #s = '%sAPI produce code: %s\n' \
        #        % (s, self.api_producer_code)
        #s = '%sCreation date: %s\n' \
        #        % (s, self.creation_date)
        #s = '%sSerial number: %s\n' \
        #        % (s, self.serial_number)
        #s = '%sReserved: %s \n' \
        #        % (s, self.reserved)
        #s = '%sExternal label name: %s\n' \
        #        % (s, self.external_label_name)
        #s = '%sRecording entity name: %s\n' \
        #        % (s, self.recording_entity_name)
        #s = '%sUser defined 1: %s\n' \
        #        % (s, self.user_defined_1)
        #s = '%sMax file size in MBytes: %s\n' \
        #        % (s, self.max_file_size_in_MBytes)
        #s = '%sLast byte read: %s\n' \
        #        % (s, self.last_byte_read)
        s = 'Receiver Record Header\n----------------------\n'
        s = '%s\tGeneral Header\n\t--------------\n' % s
        s = '%s\t\tGeneral Header Block #1\n\t\t-----------------------\n' % s
        s = '%s\t\tFile number: %i\n' \
                % (s, self.file_number)
        s = '%s\t\tData sample format code: %i\n' \
                % (s, self.data_sample_format_code)
        s = '%s\t\tGeneral constants: %s\n' \
                % (s, self.general_constants)
        s = '%s\t\tFirst shot point last two digits of year: %i\n' \
                % (s, self.first_shot_last_two_digits_of_year)
        s = '%s\t\tNumber of additional General Header blocks: %i\n' \
                % (s, self.number_of_additional_general_header_blocks)
        s = '%s\t\tFirst shot point Julian day in year: %i\n' \
                % (s, self.first_shot_julian_day)
        s = '%s\t\tFirst shot UTC time: %i:%i:%i\n' \
                % (s, self.first_shot_utc_time_hh,
                      self.first_shot_utc_time_mm,
                      self.first_shot_utc_time_ss)
        s = '%s\t\tManufacturer\'s code: %i\n' \
                % (s, self.manufacturers_code)
        s = '%s\t\tManufacturer\'s serial numer: %i\n' \
                % (s, self.manufacturers_serial_number)
        s = '%s\t\tBase scan interval: %i\n' \
                % (s, self.base_scan_interval)
        s = '%s\t\tPolarity code: %i\n' \
                % (s, self.polarity_code)
        s = '%s\t\tScan types per record: %i\n' \
                % (s, self.scan_types_per_record)
        s = '%s\t\tChannel sets per scan type: %i\n' \
                % (s, self.channel_sets_per_scan_type)
        s = '%s\t\tNumber of 32-byte skew blocks: %i\n' \
                % (s, self.number_of_32_byte_skew_blocks)
        s = '%s\t\tNumber of 32-byte Extended Header Blocks: %s\n' \
                % (s, self.number_of_32_byte_extended_header_blocks)
        s = '%s\t\tNumber of 32-byte External Header Blocks: %s\n\n' \
                % (s, self.number_of_32_byte_external_header_blocks)
        s = '%s\t\tGeneral Header Block #2\n\t\t-----------------------\n' % s
        s = '%s\t\tExtended file number: %i\n' \
                % (s, self.extended_file_number)
        s = '%s\t\tExtended channel sets per scan type: %i\n' \
                % (s, self.extended_channel_sets_per_scan_type)
        s = '%s\t\tExtended header blocks: %i\n' \
                % (s, self.extended_header_blocks)
        s = '%s\t\tExternal header blocks: %s\n' \
                % (s, self.external_header_blocks)
        s = '%s\t\tFairfield file version number: not yet implemented\n' % s
        s = '%s\t\tNumber of 32-byte general trailer blocks: %i\n' \
                % (s, self.number_of_32_byte_general_trailer_blocks)
        s = '%s\t\tExtended record length in milliseconds: %i\n' \
                % (s, self.extended_record_length_in_milliseconds)
        s = '%s\t\tGeneral header block number: %i\n\n' \
                % (s, self.general_header_block_number)
        s = '%s\tChannel Set Descriptor\n\t----------------------\n' % s
        s = '%s\tScan type number: %i\n' \
                % (s, self.scan_type_number)
        s = '%s\tChannel set number: %i\n' \
                % (s, self.channel_set_number)
        s = '%s\tChannel set start time in milliseconds / 2: %i\n' \
                % (s, self.channel_set_start_time_in_milliseconds)
        s = '%s\tChannel set end time in milliseconds / 2: %i\n' \
                % (s, self.channel_set_end_time_in_milliseconds)
        s = '%s\tOptional MP factor extension byte: %i\n' \
                % (s, self.optional_mp_factor_extension_byte)
        s = '%s\tNumber of channels in set: %i\n' \
                % (s, self.number_of_channels_in_set)
        s = '%s\tChannel type code: %i\n' \
                % (s, self.channel_type_code)
        s = '%s\tNumber of sub-scans: %i\n' \
                % (s, self.number_of_subscans)
        s = '%s\tGain control type: % i\n' \
                % (s, self.gain_control_type)
        s = '%s\tAlias filter frequency in hertz: %i\n' \
                % (s, self.alias_filter_frequency_in_hertz)
        s = '%s\tAlias filter slope in dB per octave: %i\n' \
                % (s, self.alias_filter_slope_in_dB_per_octave)
        s = '%s\tLow-cut filter frequency in Hertz: %i\n' \
                % (s, self.low_cut_filter_frequency_in_hertz)
        s = '%s\tLow-cut filter slope in dB per octave: %i\n' \
                % (s, self.low_cut_filter_slope_in_db_per_octave)
        s = '%s\tNotch filter frequency in Hertz x 10: %i\n' \
                % (s, self.notch_filter_frequency_in_hertz_x10)
        s = '%s\tSecond notch filter frequency in Hertz x 10: %i\n' \
                % (s, self.second_notch_filter_frequency_in_hertz_x10)
        s = '%s\tThird notch filter frequency in Hertz x 10: %i\n' \
                % (s, self.third_notch_filter_frequency_in_hertz_x10)
        s = '%s\tExtended channel set number: %i\n' \
                % (s, self.extended_channel_set_number)
        s = '%s\tExtended header flag: %i\n' \
                % (s, self.extended_header_flag)
        s = '%s\tNumber of 32-byte trace header extension: %i\n' \
                % (s, self.number_of_32_byte_trace_header_extensions)
        s = '%s\tVertical stack size: %i\n' \
                % (s, self.vertical_stack_size)
        s = '%s\tStreamer cable number: %i\n' \
                % (s, self.streamer_cable_number)
        s = '%s\tArray forming: %i\n' \
                % (s, self.array_forming)
        return s


    def info(self):
        """
        Method to print nicely the information contained in the object.
        """

        print "*segd*:\tsegd.type() => %s" % self.type
        print "*segd*:\tsegd.path() => %s" % self.path
        print "*segd*:\tsegd.list() => %s" % self.list()
        for element in sorted(self.dbs):
            print "*segd*:\t%s => %s" % (element,self.dbs[element]['times'])


    def __call__(self):
        """
        Method to intercepts data requests.
        """

        self.info()
        return False


    def __del__(self):
        """
        Method to clean database objects.
        """

        self.dbs = {}


    def _problem(self, log):
        """
        Method to print problems and raise exceptions
        """
        raise SegDException('*segd*: ERROR=> %s' % log)


    def _get_list(self):
        """
        Private method.
        """
        pass


    def list(self):
        """
        Method to list items.
        """

        try:
            return self.dbs.keys()
        except:
            raise dbcentralException('*segd*: ERROR=> Cannot check content of list!')


    def purge(self,tbl=None):
        """
        Method to clean object.
        """
        pass


    def _read_storage_unit_label(self):
        """
        Read Storage Unit Label header.
        """
        self.storage_unit_sequence_number = self.segdfile.read(4) #"  xx"
        self.fairfield_revision_ff1_5 = self.segdfile.read(5)     #"FF1.5"
        self.storage_unit_structure = self.segdfile.read(6)       #"RECORD"
        self.binding_edition = self.segdfile.read(4)              #"B2  "
        self.maximum_block_size = self.segdfile.read(10)          #"         0"
        self.api_producer_code = self.segdfile.read(10)           #set to blanks
        self.creation_date = self.segdfile.read(11)               #dd-MMM-yyy
        self.serial_number = self.segdfile.read(12)               #"         xxx"
        self.reserved = self.segdfile.read(6)                     #set to blanks
        self.external_label_name = self.segdfile.read(12)         #"         xxx"
        self.recording_entity_name = self.segdfile.read(24)       #(<crew#>,<recID>,<job>)
        self.user_defined_1 = self.segdfile.read(14)              #"Fairfield Z   "
        self.max_file_size_in_MBytes = self.segdfile.read(10)     #"      xxxx"
        self.last_byte_read = 128


    def _read_receiver_record_header_general_header_block_1(self):
        """
        Read General Header Block #1 of the Receiver Record Header.
        """
        self.segdfile.seek(self.last_byte_read)
        self.file_number =\
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(2)))
        self.data_sample_format_code =\
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(2)))
        data = self.segdfile.read(6)
        unpacked_bytes = [int('%x' % b) for b in unpack('>6b', data)]
        self.general_constants = unpacked_bytes
        self.first_shot_last_two_digits_of_year = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        data = BCD_bytes_2_decimal(self.segdfile.read(2))
        self.number_of_additional_general_header_blocks = int(data[0])
        self.first_shot_julian_day = int(data[1:])
        self.first_shot_utc_time_hh =\
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.first_shot_utc_time_mm = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.first_shot_utc_time_ss = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.manufacturers_code = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.manufacturers_serial_number = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(2)))
        self.segdfile.read(3)
        self.base_scan_interval = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        data = BCD_bytes_2_decimal(self.segdfile.read(2))
        self.polarity_code = int(data[0])
        data = self.segdfile.read(2)
        self.scan_types_per_record = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.channel_sets_per_scan_type = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.number_of_32_byte_skew_blocks = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.number_of_32_byte_extended_header_blocks = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.number_of_32_byte_external_header_blocks = \
                concat_ints(BCD_bytes_2_decimal(self.segdfile.read(1)))
        self.last_byte_read += 32


#    def _read_receiver_record_header_general_header_block_1(self):
#        """
#        Read General Header Block #1 of the Receiver Record Header.
#        """
#        self.segdfile.seek(self.last_byte_read)

#        bytes_read = self.segdfile.read(2)
#        self.file_number = int('%x' % unpack('>H', bytes_read)[0])
#        bytes_read = self.segdfile.read(2)
#        self.data_sample_format_code = int('%x' % unpack('>H', bytes_read)[0])
#        bytes_read = self.segdfile.read(6)
#        unpacked_bytes = [int('%x' % b) for b in unpack('>6b', bytes_read)]
#        self.general_constants = unpacked_bytes
#        bytes_read = self.segdfile.read(1)
#        self.first_shot_last_two_digits_of_year = \
#                int('%x' % unpack('>b', bytes_read)[0])
#        bytes_read = self.segdfile.read(2)
#        unpacked_bytes = '%x' % unpack('>H', bytes_read)[0]
#        self.number_of_additional_general_header_blocks = int(unpacked_bytes[0])
#        self.first_shot_julian_day = int(unpacked_bytes[1:])
#        bytes_read = self.segdfile.read(3)
#        unpacked_bytes = unpack('>3B', bytes_read)
#        self.first_shot_utc_time_hh = int('%x' % unpacked_bytes[0])
#        self.first_shot_utc_time_mm = int('%x' % unpacked_bytes[1])
#        self.first_shot_utc_time_ss = int('%x' % unpacked_bytes[2])
#        bytes_read = self.segdfile.read(1)
#        self.manufacturers_code = int('%x' % unpack('>B', bytes_read)[0])
#        bytes_read = self.segdfile.read(2)
#        self.manufacturers_serial_number = \
#                int('%x' % unpack('>H', bytes_read)[0])
#        bytes_read = self.segdfile.read(3)
#        bytes_read = self.segdfile.read(1)
#        self.base_scan_interval = int('%x' % unpack('>B', bytes_read)[0])
#        bytes_read = self.segdfile.read(2)
#        unpacked_bytes = '%x' % unpack('>H', bytes_read)[0]
#        self.polarity_code = int(unpacked_bytes[0])
#        bytes_read = self.segdfile.read(2)
#        bytes_read = self.segdfile.read(1)
#        self.scan_types_per_record = int('%x' % unpack('>B', bytes_read)[0])
#        bytes_read = self.segdfile.read(1)
#        self.channel_sets_per_scan_type = int('%x' % unpack('>B', bytes_read)[0])
#        bytes_read = self.segdfile.read(1)
#        self.number_of_32_byte_skew_blocks = \
#                int('%x' % unpack('>B', bytes_read)[0])
#        bytes_read = self.segdfile.read(1)
#        self.number_of_32_byte_extended_header_blocks = \
#                '%x' % unpack('>B', bytes_read)[0]
#        try:
#            self.number_of_32_byte_extended_header_blocks = \
#                    int(self.number_of_32_byte_extended_header_blocks)
#        except ValueError:
#            pass
#        bytes_read = self.segdfile.read(1)
#        self.number_of_32_byte_external_header_blocks = \
#                '%x' % unpack('>B', bytes_read)[0]
#        try:
#            self.number_of_32_byte_external_header_blocks = \
#                    int(self.number_of_32_byte_external_header_blocks)
#        except ValueError:
#            pass
#        self.last_byte_read += 32

    def _read_receiver_record_header_general_header_block_2(self):
        """
        Read General Header Block #2 of the Receiver Record Header.
        """
        self.segdfile.seek(self.last_byte_read)
        bytes_read = self.segdfile.read(3)
        bytes_read = zero_pad(bytes_read, 4)
        self.extended_file_number = unpack('>I', bytes_read)[0]
        bytes_read = self.segdfile.read(2)
        self.extended_channel_sets_per_scan_type = \
                int('%x' % unpack('>H', bytes_read))
        bytes_read = self.segdfile.read(2)
        self.extended_header_blocks = unpack('>H', bytes_read)[0]
        bytes_read = self.segdfile.read(3)
        #come back here
        bytes_read = zero_pad(bytes_read, 4)
        self.external_header_blocks = unpack('>I', bytes_read)[0]
        #self.external_header_blocks = int('%x' % unpack('>I', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        #come back here
        #self.fairfield_file_version_number =
        bytes_read = self.segdfile.read(2)
        self.number_of_32_byte_general_trailer_blocks = \
                unpack('>H', bytes_read)[0]
        bytes_read = self.segdfile.read(3)
        bytes_read = zero_pad(bytes_read, 4)
        self.extended_record_length_in_milliseconds = \
                unpack('>I', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        bytes_read = self.segdfile.read(1)
        self.general_header_block_number = \
                unpack('>B', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        self.last_byte_read += 32

    def _read_channel_set_descriptor(self):
        """
        Read Channel Set Descriptor of the Receiver Record Header.
        """
        self.segdfile.seek(self.last_byte_read)
        bytes_read = self.segdfile.read(1)
        self.scan_type_number = \
                int('%x' % unpack('>B', bytes_read)[0])
        bytes_read = self.segdfile.read(1)
        self.channel_set_number = \
                int('%x' % unpack('>B', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.channel_set_start_time_in_milliseconds = \
                unpack('>H', bytes_read)[0]
        bytes_read = self.segdfile.read(2)
        self.channel_set_end_time_in_milliseconds = \
                unpack('>H', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        self.optional_mp_factor_extension_byte = \
                unpack('>B', bytes_read)[0]
        bytes_read = self.segdfile.read(2)
        self.number_of_channels_in_set = \
                int('%x' %  unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(1)
        unpacked_bytes = unpack('>B', bytes_read)
        self.channel_type_code = unpacked_bytes[0]
        bytes_read = self.segdfile.read(1)
        unpacked_bytes = unpack('>B', bytes_read)
        self.number_of_subscans = int(('%d' % unpacked_bytes)[0])
        self.gain_control_type = int(('%d' % unpacked_bytes)[1])
        bytes_read = self.segdfile.read(2)
        self.alias_filter_frequency_in_hertz = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.alias_filter_slope_in_dB_per_octave = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.low_cut_filter_frequency_in_hertz = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.low_cut_filter_slope_in_db_per_octave = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.notch_filter_frequency_in_hertz_x10 = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.second_notch_filter_frequency_in_hertz_x10 = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.third_notch_filter_frequency_in_hertz_x10 = \
                int('%x' % unpack('>H', bytes_read)[0])
        bytes_read = self.segdfile.read(2)
        self.extended_channel_set_number = unpack('>H', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        unpacked_bytes = unpack('>B', bytes_read)[0]
        self.extended_header_flag = int(('%02d' % unpacked_bytes)[0])
        self.number_of_32_byte_trace_header_extensions = \
                int(('%02d' % unpacked_bytes)[1])
        bytes_read = self.segdfile.read(1)
        self.vertical_stack_size = unpack('>B', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        self.streamer_cable_number = unpack('>B', bytes_read)[0]
        bytes_read = self.segdfile.read(1)
        self.array_forming = unpack('>B', bytes_read)[0]
        self.last_byte_read += 32

def BCD_bytes_2_decimal(chars):
    """
    Reads a string of BCD formatted data and returns string of decimal values.
    """
    results = ''
    for char in chars:
        char = ord(char)
        for val in (char >> 4, char & 0xF):
            results = '%s%x' % (results, val)
    return results
    #return [int('%x' % unpack('>B', byte)[0]) for byte in bytes_in]

def binary_bytes_2_decimal(bytes_in):
    """
    Reads a string of binary data and returns integer value.
    Input string must have length of 1, 2, 3 or 4 bytes.
    """
    if len(bytes_in) == 1:
        return unpack('>B', bytes_in)[0]
    elif len(bytes_in) == 2:
        return unpack('>H', bytes_in)[0]
    else:
        if len(bytes_in) == 3:
            bytes_in = zero_pad(bytes_in, 4)
        if len(bytes_in) != 4:
            raise Exception
        return unpack('>I', bytes_in)[0]

def concat_ints(data):
    """
    Concatenate a string of integers together and type-cast to int.
    To be used with string returned by BCD_bytes_2_decimal.
    """
    s =  ''
    for d in data:
        s = '%s%s' % (s, d)
    try:
        s = int(s)
    except ValueError:
        pass
    return s

def zero_pad(s, size):
    """
    Pad a hex-string with leading zeroes until string is 'size' bytes.
    Return padded string.
    """
    if len(s) == size:
        return s
    else:
        while len(s) != size:
            s = '\x00%s' % s
    return s

if __name__ == '__main__':
    """
    This will run if the file is called directly.
    """

    segdobject = SegD('./my_segd_file.segd')

    print 'segdobject = segd("%s")' % (segdobject.path)
    print ''
    print '%s' % segdobject
    print ''
    print 'segdobject.list() => %s' % segdobject.list()
    print ''
    try:
        segdobject.purge()
    except Exception, e:
        print 'segdobject.purge() => %s' % e

    print ''
