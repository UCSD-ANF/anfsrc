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
import os
from struct import unpack
from collections import OrderedDict




class SegDException(Exception):
    """
    New exception for the SEGD class.
    Just empty for now.
    """
    pass

class SegD:
    schema = OrderedDict([('General Header',
                OrderedDict([('General Header Block #1',
                    OrderedDict([('block_length_in_bytes', 32),
                                 ('file_number',
                                        {'start': 1,
                                         'nibbles': 4,
                                         'type': 'bcd',
                                         'description': 'File number (0-9999)',
                                         'notes': 'Set to FFFF when the file '\
                                            'number is greater than 9999. The '\
                                            'expanded file number is contained'\
                                            ' in bytes 1-3 of General Header '\
                                            'Block #2.'
                                        }
                                 ),
                                 ('data_sample_format_code',
                                        {'start': 3,
                                        'nibbles': 4,
                                        'type': 'bcd',
                                        'description': 'Data sample format '\
                                            'code (8058)',
                                        'notes': ''
                                        }
                                 ),
                                 ('general_constants',
                                        {'start': 5,
                                         'nibbles': 12,
                                         'type': 'bcd',
                                         'description': 'General constants',
                                         'notes': ''
                                        }
                                 ),
                                 ('first_shot_last_two_digits_of_year',
                                        {'start': 11,
                                         'nibbles': 2,
                                         'type': 'bcd',
                                         'description': 'First shot point or '\
                                            'time slice last two digits of '\
                                            'year',
                                         'notes': ''
                                        }
                                 ),
                                 ('number_of_additional_general_header_blocks',
                                        {'start': 12,
                                         'nibbles': 1,
                                         'type': 'binary',
                                         'description': 'Number of additional '\
                                            'general header blocks (1)',
                                         'notes': ''
                                        }
                                 ),
                                 ('first_shot_julian_day',
                                        {'start': 12.5,
                                         'nibbles': 3,
                                         'type': 'bcd',
                                         'description': 'First shot point or '\
                                            'time slice Julian day in year',
                                         'notes': ''
                                        }
                                 ),
                                 ('first_shot_UTC_time',
                                        {'start': 14,
                                         'nibbles': 6,
                                         'type': 'bcd',
                                         'description': 'First shot point or '\
                                            'time slice UTC time (HHMMSS)',
                                         'notes': ''
                                        }
                                 ),
                                 ('manufacturers_code',
                                        {'start': 17,
                                         'nibbles': 2,
                                         'type': 'bcd',
                                         'description': 'Manufacturer\'s code '\
                                            '(20)',
                                         'notes': ''
                                        }
                                  ),
                                  ('manufacturers_serial_number',
                                        {'start': 18,
                                         'nibbles': 4,
                                         'type': 'bcd',
                                         'description': 'Manufacturer\'s '\
                                            'serial number',
                                         'notes': ''
                                        }
                                 ),
                                 ('not_used_1',
                                        {'start': 20,
                                         'nibbles': 6,
                                         'type': 'bcd',
                                         'description': 'Not used (0)',
                                         'notes': ''
                                        }
                                 ),
                                 ('base_scan_interval',
                                        {'start': 23,
                                         'nibbles': 2,
                                         'type': 'binary',
                                         'description': 'Base scan interval',
                                         'notes': ''
                                        }
                                 ),
                                 ('polarity_code',
                                        {'start': 24,
                                         'nibbles': 1,
                                         'type': 'binary',
                                         'description': 'Polarity code (0)',
                                         'notes': ''
                                        }
                                 ),
                                 ('not_used_2',
                                        {'start': 24.5,
                                         'nibbles': 3,
                                         'type': 'binary',
                                         'description': 'Not used (0)',
                                         'notes': ''
                                        }
                                 ),
                                 ('record_type',
                                        {'start': 26,
                                         'nibbles': 1,
                                         'type': 'binary',
                                         'description': 'Record type (0)',
                                         'notes': 'Moved to trace header (set '\
                                            'to 0)'
                                        }
                                 ),
                                 ('record_length_in_increments_of_512_1000ths_'\
                                    'of_a_second',
                                        {'start': 26.5,
                                         'nibbles': 3,
                                         'type': 'bcd',
                                         'description': 'Record length in '\
                                            'increments of 0.512 seconds (FFF)',
                                         'notes': 'Use value stored in '\
                                            'General Header Block #2 - bytes '\
                                            '15-17.'
                                        }
                                 ),
                                 ('scan_types_per_record',
                                        {'start': 28,
                                         'nibbles': 2,
                                         'type': 'bcd',
                                         'description': 'Scan types per '\
                                            'record (01)',
                                         'notes': ''
                                        }
                                 ),
                                 ('channel_sets_per_scan_type',
                                        {'start': 29,
                                         'nibbles': 2,
                                         'type': 'bcd',
                                         'description': 'Channel sets per '\
                                            'scan type',
                                         'notes': ''
                                        }
                                 ),
                                 ('number_of_32_byte_skew_blocks',
                                            {'start': 30,
                                             'nibbles': 2,
                                             'type': 'bcd',
                                             'description': 'Number of '\
                                                '32-byte skew blocks (0)',
                                             'notes': ''
                                            }
                                 ),
                                 ('number_of_32_byte_extended_header_blocks',
                                            {'start': 31,
                                             'nibbles': 2,
                                             'type': 'bcd',
                                             'description': 'Number of '\
                                                '32-byte Extended Header '\
                                                'Blocks (00-99 or FF... use '\
                                                'value in General Header '\
                                                'Block #2)',
                                             'notes': ''
                                            }
                                 ),
                                 ('number_of_32_byte_external_header_blocks',
                                            {'start': 32,
                                             'nibbles': 2,
                                             'type': 'bcd',
                                             'description': 'Number of of '\
                                                '32-byte External Header '\
                                                'Blocks (00-99 or FF... use '\
                                                'value in General Header '\
                                                'Block #2)',
                                             'notes': ''
                                            }
                                 )
                               ])),
                ('General Header Block #2',
                    OrderedDict([('block_length_in_bytes', 32),
                                 ('extended_file_number',
                                        {'start': 1,
                                         'nibbles': 6,
                                         'type': 'binary',
                                         'description': 'Extended file number',
                                         'notes': ''
                                        }
                                 ),
                                 ('extended_channel_sets_per_scan_type',
                                        {'start': 2,
                                         'nibbles': 4,
                                         'type': 'binary',
                                         'description': 'Extended channel '\
                                            'sets per scan type',
                                         'notes': ''
                                        }
                                 ),
                                 ('extended_header_blocks',
                                        {'start': 6,
                                         'nibbles': 4,
                                         'type': 'binary',
                                         'description': 'Extended header '\
                                            'blocks',
                                         'notes': ''
                                        }
                                 ),
                                 ('external_header_blocks',
                                        {'start': 8,
                                         'nibbles': 6,
                                         'type': 'binary',
                                         'description': 'External header '\
                                            'blocks',
                                         'notes': 'Now 3 bytes instead of 2.'
                                        }
                                 ),
                                 ('fairfield_file_version_number',
                                        {'start': 11,
                                         'nibbles': 4,
                                         'type': 'binary',
                                         'description': 'Fairfield file '\
                                            'version number',
                                         'notes': 'One byte unsigned binary '\
                                            'and one byte binary fraction. '\
                                            'This version: 0x0105'
                                        }
                                 ),
                                 ('number_of_32_byte_general_trailer_blocks',
                                        {'start': 13,
                                         'nibbles': 4,
                                         'type': 'binary',
                                         'description': 'Number of 32-byte '\
                                            'general trailer blocks (0)',
                                         'notes': ''
                                        }
                                 ),
                                 ('extended_record_length_in_milliseconds',
                                        {'start': 15,
                                         'nibbles': 6,
                                         'type': 'binary',
                                         'description': 'Extended record '\
                                            'length in milliseconds',
                                         'notes': ''
                                        }
                                 ),
                                 ('undefined_1',
                                        {'start': 18,
                                         'nibbles': 2,
                                         'type': 'binary',
                                         'description': 'Undefined (0)',
                                         'notes': ''
                                        }
                                 ),
                                 ('general_header_block_number',
                                        {'start': 19,
                                         'nibbles': 2,
                                         'type': 'binary',
                                         'description': 'General header '\
                                            'block number (2)',
                                         'notes': ''
                                        }
                                 ),
                                 ('undefined_2',
                                        {'start': 20,
                                         'nibbles': 26,
                                         'type': 'binary',
                                         'description': 'Undefined (0)',
                                         'notes': ''
                                        }
                                 )])
                            )])
                )])
    def __init__(self, path, debug=False):
        self.path  = os.path.abspath(path)
        self.debug = debug
        self.segdfile = open(self.path, 'rb')
        #the byte number of the end of the last block read
        self.end_of_last_block = 0
        for general_block in self.schema:
            for header_block in self.schema[general_block]:
                self._read_header_block(self.schema[general_block][header_block])
                self.end_of_last_block += \
                    self.schema[general_block][header_block]['block_length_in_bytes']
        self.segdfile.close()

#    def __init__(self, path, debug=False):
#        self.type = False
#        self.path = os.path.abspath(path)
#        self.debug = debug
#
#        self.segdfile = open(self.path, 'rb')
#        self.last_byte_read = 0
#        #self._read_storage_unit_label()
#        self._read_receiver_record_header_general_header_block_1()
#        self._read_receiver_record_header_general_header_block_2()
#        self._read_channel_set_descriptor()
#        self.segdfile.close()

    def __str__(self):
        s = 'SEG-D Header contents\n---------------------\n'
        for general_block in self.schema:
            s = '%s\t%s\n\t%s\n' % (s, general_block, '-' * len(general_block))
            for header_block in self.schema[general_block]:
                s = '%s\t\t%s\n\t\t%s\n' % (s, header_block, '-' * len(header_block))
                for field in self.schema[general_block][header_block]:
                    if field == 'block_length_in_bytes': continue
                    s = '%s\t\t%s: %s\n' \
                            % (s,
                            self.schema[general_block][header_block][field]['description'],
                            getattr(self, field))
                s = '%s\n' % s
        return s


#    def __str__(self):
#        """
#        end-user/application display of content using print() or log.msg()
#        """
#        #s = 'Storage Unit Label\n------------------\n'
#        #s = '%sStorage unit sequence number: %s\n' \
#        #        % (s, self.storage_unit_sequence_number)
#        #s = '%sFairfield revision: %s\n' \
#        #        % (s, self.fairfield_revision_ff1_5)
#        #s = '%sStorage unit structure: %s\n' \
#        #        % (s, self.storage_unit_structure)
#        #s = '%sBinding edition: %s\n' \
#        #        % (s, self.binding_edition)
#        #s = '%sMaximum block size: %s\n' \
#        #        % (s, self.maximum_block_size)
#        #s = '%sAPI produce code: %s\n' \
#        #        % (s, self.api_producer_code)
#        #s = '%sCreation date: %s\n' \
#        #        % (s, self.creation_date)
#        #s = '%sSerial number: %s\n' \
#        #        % (s, self.serial_number)
#        #s = '%sReserved: %s \n' \
#        #        % (s, self.reserved)
#        #s = '%sExternal label name: %s\n' \
#        #        % (s, self.external_label_name)
#        #s = '%sRecording entity name: %s\n' \
#        #        % (s, self.recording_entity_name)
#        #s = '%sUser defined 1: %s\n' \
#        #        % (s, self.user_defined_1)
#        #s = '%sMax file size in MBytes: %s\n' \
#        #        % (s, self.max_file_size_in_MBytes)
#        #s = '%sLast byte read: %s\n' \
#        #        % (s, self.last_byte_read)
#        s = 'Receiver Record Header\n----------------------\n'
#        s = '%s\tGeneral Header\n\t--------------\n' % s
#        s = '%s\t\tGeneral Header Block #1\n\t\t-----------------------\n' % s
#        s = '%s\t\tFile number: %i\n' \
#                % (s, self.file_number)
#        s = '%s\t\tData sample format code: %i\n' \
#                % (s, self.data_sample_format_code)
#        s = '%s\t\tGeneral constants: %s\n' \
#                % (s, self.general_constants)
#        s = '%s\t\tFirst shot point last two digits of year: %i\n' \
#                % (s, self.first_shot_last_two_digits_of_year)
#        s = '%s\t\tNumber of additional General Header blocks: %i\n' \
#                % (s, self.number_of_additional_general_header_blocks)
#        s = '%s\t\tFirst shot point Julian day in year: %i\n' \
#                % (s, self.first_shot_julian_day)
#        s = '%s\t\tFirst shot UTC time: %i:%i:%i\n' \
#                % (s, self.first_shot_utc_time_hh,
#                      self.first_shot_utc_time_mm,
#                      self.first_shot_utc_time_ss)
#        s = '%s\t\tManufacturer\'s code: %i\n' \
#                % (s, self.manufacturers_code)
#        s = '%s\t\tManufacturer\'s serial numer: %i\n' \
#                % (s, self.manufacturers_serial_number)
#        s = '%s\t\tBase scan interval: %i\n' \
#                % (s, self.base_scan_interval)
#        s = '%s\t\tPolarity code: %i\n' \
#                % (s, self.polarity_code)
#        s = '%s\t\tScan types per record: %i\n' \
#                % (s, self.scan_types_per_record)
#        s = '%s\t\tChannel sets per scan type: %i\n' \
#                % (s, self.channel_sets_per_scan_type)
#        s = '%s\t\tNumber of 32-byte skew blocks: %i\n' \
#                % (s, self.number_of_32_byte_skew_blocks)
#        s = '%s\t\tNumber of 32-byte Extended Header Blocks: %s\n' \
#                % (s, self.number_of_32_byte_extended_header_blocks)
#        s = '%s\t\tNumber of 32-byte External Header Blocks: %s\n\n' \
#                % (s, self.number_of_32_byte_external_header_blocks)
#        s = '%s\t\tGeneral Header Block #2\n\t\t-----------------------\n' % s
#        s = '%s\t\tExtended file number: %i\n' \
#                % (s, self.extended_file_number)
#        s = '%s\t\tExtended channel sets per scan type: %i\n' \
#                % (s, self.extended_channel_sets_per_scan_type)
#        s = '%s\t\tExtended header blocks: %i\n' \
#                % (s, self.extended_header_blocks)
#        s = '%s\t\tExternal header blocks: %s\n' \
#                % (s, self.external_header_blocks)
#        s = '%s\t\tFairfield file version number: not yet implemented\n' % s
#        s = '%s\t\tNumber of 32-byte general trailer blocks: %i\n' \
#                % (s, self.number_of_32_byte_general_trailer_blocks)
#        s = '%s\t\tExtended record length in milliseconds: %i\n' \
#                % (s, self.extended_record_length_in_milliseconds)
#        s = '%s\t\tGeneral header block number: %i\n\n' \
#                % (s, self.general_header_block_number)
#        s = '%s\tChannel Set Descriptor\n\t----------------------\n' % s
#        s = '%s\tScan type number: %i\n' \
#                % (s, self.scan_type_number)
#        s = '%s\tChannel set number: %i\n' \
#                % (s, self.channel_set_number)
#        s = '%s\tChannel set start time in milliseconds / 2: %i\n' \
#                % (s, self.channel_set_start_time_in_milliseconds)
#        s = '%s\tChannel set end time in milliseconds / 2: %i\n' \
#                % (s, self.channel_set_end_time_in_milliseconds)
#        s = '%s\tOptional MP factor extension byte: %i\n' \
#                % (s, self.optional_mp_factor_extension_byte)
#        s = '%s\tNumber of channels in set: %i\n' \
#                % (s, self.number_of_channels_in_set)
#        s = '%s\tChannel type code: %i\n' \
#                % (s, self.channel_type_code)
#        s = '%s\tNumber of sub-scans: %i\n' \
#                % (s, self.number_of_subscans)
#        s = '%s\tGain control type: % i\n' \
#                % (s, self.gain_control_type)
#        s = '%s\tAlias filter frequency in hertz: %i\n' \
#                % (s, self.alias_filter_frequency_in_hertz)
#        s = '%s\tAlias filter slope in dB per octave: %i\n' \
#                % (s, self.alias_filter_slope_in_dB_per_octave)
#        s = '%s\tLow-cut filter frequency in Hertz: %i\n' \
#                % (s, self.low_cut_filter_frequency_in_hertz)
#        s = '%s\tLow-cut filter slope in dB per octave: %i\n' \
#                % (s, self.low_cut_filter_slope_in_db_per_octave)
#        s = '%s\tNotch filter frequency in Hertz x 10: %i\n' \
#                % (s, self.notch_filter_frequency_in_hertz_x10)
#        s = '%s\tSecond notch filter frequency in Hertz x 10: %i\n' \
#                % (s, self.second_notch_filter_frequency_in_hertz_x10)
#        s = '%s\tThird notch filter frequency in Hertz x 10: %i\n' \
#                % (s, self.third_notch_filter_frequency_in_hertz_x10)
#        s = '%s\tExtended channel set number: %i\n' \
#                % (s, self.extended_channel_set_number)
#        s = '%s\tExtended header flag: %i\n' \
#                % (s, self.extended_header_flag)
#        s = '%s\tNumber of 32-byte trace header extension: %i\n' \
#                % (s, self.number_of_32_byte_trace_header_extensions)
#        s = '%s\tVertical stack size: %i\n' \
#                % (s, self.vertical_stack_size)
#        s = '%s\tStreamer cable number: %i\n' \
#                % (s, self.streamer_cable_number)
#        s = '%s\tArray forming: %i\n' \
#                % (s, self.array_forming)
#        return s


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

    def _read_header_block(self, block_schema):
        for field in  block_schema:
            if field == 'block_length_in_bytes': continue
            if block_schema[field]['type'] == 'bcd':
                value = self._read_BCD(block_schema[field]['start'],
                                       block_schema[field]['nibbles'])
                setattr(self, field, value)
            elif block_schema[field]['type'] == 'binary':
                value = self._read_binary(block_schema[field]['start'],
                                          block_schema[field]['nibbles'])
                setattr(self, field, value)
            elif block_schema[field]['type'] == 'float':
                value = self._read_float(block_schema[field]['start'],
                                         block_schema[field]['nibbles'])
            else:
                self._problem('Data type %s not valid' \
                        % block_schema[field]['type'])

    def _read_BCD(self, start, nibbles):
        """
        Read BCD nibbles from file and return integer value.

        Arguments:
        start - the byte index of the starting nibble for the data field
        relative to the start of the header block

        nibbles - the number of nibbles of BCD data to be read

        Returns:
        return_data - the integer value represented by the BCD data

        Caveats:
        This method will return a string value when the BCD data does
        not convert to a integer value.
        """
        data,\
        ignore_first_nibble,\
        ignore_last_nibble,\
        n_bytes = self._get_raw_data(start, nibbles)
        is_first_byte, byte_count = True, 0
        unpacked_data = []
        for char in data:
            byte_count += 1
            char = ord(char)
            #unpack the first nibble of the byte, unless this is the
            #first byte, and the first nibble is to be ignored
            if not (is_first_byte and ignore_first_nibble):
                unpacked_data += ['%x' % (char >> 4)]
            #unpack the second nibble of the byte, unless this is the
            #last byte, and the last nibble is to be ignored
            if not (byte_count == n_bytes and ignore_last_nibble):
                unpacked_data += ['%x' % (char & 0xF)]
            is_first_byte = False
        return_data = ''
        for char in unpacked_data:
            return_data = '%s%s' % (return_data, char)
        try:
            return_data = int(return_data)
        except ValueError:
            pass
        return return_data

    def _read_binary(self, start, nibbles):
        data,\
        ignore_first_nibble,\
        ignore_last_nibble,\
        n_bytes = self._get_raw_data(start, nibbles)
        if n_bytes > 4:
            #self._problem('_read_binary() cannot read more than 4 '\
            #              'bytes of data at once.')
            return 0
        if n_bytes == 1:
            return_data = int(unpack('>B', data)[0])
            if ignore_first_nibble: return_data = return_data & 0x0F
            if ignore_last_nibble: return_data = return_data >> 4
            return return_data
        elif n_bytes == 2:
            return_data = int(unpack('>H', data)[0])
            if ignore_first_nibble: return_data = return_data & 0x0FFF
            if ignore_last_nibble: return_data = return_data >> 4
            return return_data
        elif n_bytes == 3:
            data = zero_pad(data, 4)
        return_data = int(unpack('>I', data)[0])
        if ignore_first_nibble: return_data = return_data & 0x0FFFFFFF
        if ignore_last_nibble: return_data = return_data >> 4
        return return_data


    def _read_float(self, start, nibbles):
        return None

    def _get_raw_data(self, start, nibbles):
        """
        Read and return raw data from file SEG-D file.

        Arguments:
        start - the byte index of the starting nibble for the data
        chunk to be read, relative to the beginning of the header block

        nibbles - the number of nibbles of data to be read

        Returns:
        data - the raw data requested

        ignore_first_nibble - a flag indicating whether or not to
        ignore the first nibble of data

        ignore_last_nibble - a flag indicating whether or not to ignore
        the last nibble

        n_bytes - the number of bytes of data returned
        """
        ignore_first_nibble, ignore_last_nibble = False, False
        #if the data field terminates at the middle of a byte,
        #create a flag to ignore the last nibble of data
        if (start + nibbles / 2.0) % 1 != 0: ignore_last_nibble = True
        #if the data begins at the middle of a byte,
        #create a flag to ignore the first nibble
        if start % 1 != 0:
            ignore_first_nibble = True
            #move the starting byte index to the beginning of the byte
            start = start - 0.5
        #determine the number of bytes to read
        if nibbles % 2 == 1: n_bytes = (nibbles + 1) / 2
        else: n_bytes = nibbles / 2
        self.segdfile.seek(self.end_of_last_block + start - 1)
        data = self.segdfile.read(n_bytes)
        return data, ignore_first_nibble, ignore_last_nibble, n_bytes

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
