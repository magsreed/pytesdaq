import math
import time
import pyvisa as visa
from enum import Enum


_HEADER = "c4d"
_FOOTER = "00zx"
_READ_COMMAND = "c2x"



class FEBSettings(Enum):
    SENSORBIAS  = 1
    SQUIDBIAS   = 2
    SQUIDLOCK   = 3
    SQUIDGAIN   = 4
    SQUIDDRIVER = 5
    
class FEBChannels(Enum):
    A = 10
    B = 11
    C = 12
    D = 13



class FEB(object):
    """
    FEB control
    """

    def __init__(self,gpib_address):
    
        # open instrument
        rm=visa.ResourceManager()
        self.inst=rm.open_resource(gpib_address)
        


    def _fourdigit(self,input_str):
        """
        makes strings that are shorter than 4 digits 4 digits by filling the front with "0"s
        """
        while len(input_str) < 4:
            input_str = "0" + input_str
        return input_str


    def _write(self,subrack, address, data):
        subrack_with_address_bit = subrack | 8
        address_str = _HEADER + _fourdigit(format(address, "x")) + "0" + format(subrack_with_address_bit, "x") + _FOOTER
        data_str = _HEADER + format(data, "x") + "0" + format(subrack, "x") + _FOOTER
        self.inst.write(address_str)
        self.inst.write(data_str)
        time.sleep(0.16)
	

    def _read(self,subrack, address):
        subrack_with_address_bit = subrack | 8
        address_str = _HEADER + fourdigit(format(address, "x")) + "0" + format(subrack_with_address_bit, "x") + _FOOTER
        self.inst.write(address_str)
        self.inst.write(_READ_COMMAND)
        data = self.inst.read()
        return data[:4]


    def _set_feb(self,subrack, slot, setting, channel, value, millisec_delay = 0.160):
        address = (slot << 8) + (setting << 4) + channel
        data = 0
        if setting == FEBSettings.SENSORBIAS:
            data = int(round(4095.0 * (2000.0 + value) / 4000.0))
        if setting == FEBSettings.SQUIDBIAS:
            data = int(round(4095.0 * (200.0 + value) / 400.0))
        if setting == FEBSettings.SQUIDLOCK:
            data = int(round(4095.0 * (8.0 - value) / 16.0))
        if setting == FEBSettings.SQUIDGAIN:
            data = int(round(4095.0 * (5.0 - value / 20.0) / 10.0))
        if setting == FEBSettings.SQUIDDRIVER:
            data = int(round(4095.0 * (5.0 - value) / 10.0))
        
        time.sleep(millisec_delay)
        self._write(subrack, address, data)

    def _get_feb(self,subrack, slot, setting, channel, millisec_delay = 0.160):
        volt_current = -9999.9
        address = (slot << 8) + (setting << 4) + channel #the original java code also catch some exception here
        time.sleep(millisec_delay)
        bias_val_hex = self._read(subrack, address)
        decimal_result = int(bias_val_hex, 16) & 4095

        if setting == FEBSettings.SENSORBIAS:
            volt_current = 4000.0 * float(decimal_result) / 4095.0 - 2000.0
        elif setting == FEBSettings.SQUIDBIAS:
            volt_current = 400.0 * float(decimal_result) / 4095.0 - 200.0
        elif setting == FEBSettings.SQUIDLOCK:
            volt_current = -16.0 * float(decimal_result) / 4095.0 + 8.0
        elif setting == FEBSettings.SQUIDGAIN:
            volt_current = 20.0 * (5.0 - 10.0 * float(decimal_result) / 4095)
        elif setting == FEBSettings.SQUIDDRIVER:
            volt_current = -(10.0 * float(decimal_result) / 4095.0 - 5.0)
        return volt_current

    def _get_feb_driver_CSR(subrack, slot):
        output_driver_CSR = [True] * 16
        address = (slot << 8) + (14 << 4) + 2
        time.sleep(0.16)
        driver_csr = self._read(subrack, address)
        decimal_result = int(driver_csr, 16)
        
        output_driver_CSR[0] = (decimal_result & 1) != 0
        output_driver_CSR[1] = (decimal_result & 2) != 0
        output_driver_CSR[2] = (decimal_result & 4) != 0
        output_driver_CSR[3] = (decimal_result & 8) != 0
        output_driver_CSR[4] = (decimal_result & 16) != 0
        output_driver_CSR[5] = (decimal_result & 32) != 0
        output_driver_CSR[6] = (decimal_result & 64) != 0
        output_driver_CSR[7] = (decimal_result & 128) != 0
        output_driver_CSR[8] = (decimal_result & 256) != 0
        output_driver_CSR[9] = (decimal_result & 512) != 0
        output_driver_CSR[10] = (decimal_result & 1024) != 0
        output_driver_CSR[11] = (decimal_result & 2048) != 0
        output_driver_CSR[12] = (decimal_result & 4096) != 0
        output_driver_CSR[13] = (decimal_result & 8192) != 0
        output_driver_CSR[14] = (decimal_result & 16384) != 0
        output_driver_CSR[15] = (decimal_result & 32768) != 0
        return output_driver_CSR

    def _get_feb_CSR(self,subrack, slot, millisec_delay = 0.16):
        output_CSR = [True] * 16
        address = (slot << 8) + (14 << 4) + 1
        time.sleep(millisec_delay)
        driver_csr = self._read(subrack, address)
        decimal_result = int(driver_csr, 16)
        
        output_CSR[0] = (decimal_result & 1) != 0
        output_CSR[1] = (decimal_result & 2) != 0
        output_CSR[2] = (decimal_result & 4) != 0
        output_CSR[3] = (decimal_result & 8) != 0
        output_CSR[4] = (decimal_result & 16) != 0
        output_CSR[5] = (decimal_result & 32) != 0
        output_CSR[6] = (decimal_result & 64) != 0
        output_CSR[7] = (decimal_result & 128) != 0
        output_CSR[8] = (decimal_result & 256) != 0
        output_CSR[9] = (decimal_result & 512) != 0
        output_CSR[10] = (decimal_result & 1024) != 0
        output_CSR[11] = (decimal_result & 2048) != 0
        output_CSR[12] = (decimal_result & 4096) != 0
        output_CSR[13] = (decimal_result & 8192) != 0
        output_CSR[14] = (decimal_result & 16384) != 0
        output_CSR[15] = (decimal_result & 32768) != 0
        return output_CSR

    def _get_sense_bias(self,subrack, slot, millisec_delay = 0.16):
        output_sense_bias_CSR = [True] * 16
        address = (slot << 8) + (14 << 4)
        time.sleep(millisec_delay)
        sense_bias_csr = self._read(subrack, address)
        decimal_result = int(sense_bias_csr, 16)
        output_sense_bias_CSR[0] = (decimal_result & 1) != 0
        output_sense_bias_CSR[1] = (decimal_result & 2) != 0
        output_sense_bias_CSR[2] = (decimal_result & 4) != 0
        output_sense_bias_CSR[3] = (decimal_result & 8) != 0
        output_sense_bias_CSR[4] = (decimal_result & 16) != 0
        output_sense_bias_CSR[5] = (decimal_result & 32) != 0
        output_sense_bias_CSR[6] = (decimal_result & 64) != 0
        output_sense_bias_CSR[7] = (decimal_result & 128) != 0
        output_sense_bias_CSR[8] = (decimal_result & 256) != 0
        output_sense_bias_CSR[9] = (decimal_result & 512) != 0
        output_sense_bias_CSR[10] = (decimal_result & 1024) != 0
        output_sense_bias_CSR[11] = (decimal_result & 2048) != 0
        output_sense_bias_CSR[12] = (decimal_result & 4096) != 0
        output_sense_bias_CSR[13] = (decimal_result & 8192) != 0
        output_sense_bias_CSR[14] = (decimal_result & 16384) != 0
        output_sense_bias_CSR[15] = (decimal_result & 32768) != 0
        return output_sense_bias_CSR
                

    ### this value should be from -2000 to 2000
    def set_phonon_qet_bias(self,subrack, slot, channel, value, millisec_delay = 0.160):
        self._set_feb(subrack, slot, FEBSettings.SENSORBIAS, channel, value, millisec_delay)
                
    ### this value should be from -200 to 200 microamps
    def set_phonon_squid_bias(self,subrack, slot, channel, value, millisec_delay = 0.160):
        self._set_feb(subrack, slot, FEBSettings.SQUIDBIAS, channel, value, millisec_delay)
                
    ### this value should be from -8 to 8 (millivolt)
    def set_phonon_lock_point(self,subrack, slot, channel, value, millisec_delay = 0.160):
        self._set_feb(subrack, slot, FEBSettings.SQUIDLOCK, channel, value, millisec_delay)

    ### this value should be from 20 to 100
    def set_phonon_feedback_gain(self,subrack, slot, channel, value, millisec_delay = 0.160):
        self._set_feb(subrack, slot, FEBSettings.SQUIDGAIN, channel, value, millisec_delay)

    ### this is just SquidDriver in the Java code
    ### this value shousld be from -5V to 5V
    def set_phonon_offset(self,subrack, slot, channel, value, millisec_delay = 0.160):
        self._set_feb(subrack, slot, FEBSettings.SQUIDDRIVER, channel, value, millisec_delay)


    def set_phonon_output_gain(self,subrack, slot, channel, gain):
        if gain >= -50.0 and gain <= 50.0:
            address = (slot << 8) + (14 << 4) + 2
            channel -= 10
            old_driver_CSR = self._get_feb_driver_CSR(subrack, slot)
            data = 0
            
            if gain == 1.43:
                data += 1 << channel * 4
            elif gain == 2.0:
                data += 2 << channel * 4
            elif gain == 5.0:
                data += 3 << channel * 4
            elif gain == 10.0:
                data += 4 << channel * 4
            elif gain == 14.3:
                data += 5 << channel * 4
            elif gain == 20.0:
                data += 6 << channel * 4
            elif gain == 50.0:
                data += 7 << channel * 4
            elif gain == -1.0:
                data += 8 << channel * 4
            elif gain == -1.43:
                data += 9 << channel * 4
            elif gain == -2.0:
                data += 10 << channel * 4
            elif gain == -5.0:
                data += 11 << channel * 4
            elif gain == -10.0:
                data += 12 << channel * 4
            elif gain == -14.3:
                data += 13 << channel * 4
            elif gain == -20.0:
                data += 14 << channel * 4
            elif gain == -50.0:
                data += 15 << channel * 4
            elif gain != 1.0:
                raise Exception("FEB: Invalid gain specified for a phonon channel: " + str(gain))
		
            for i in range(16):
                if i != channel * 4 and i != channel * 4 + 1 and i != channel * 4 + 2 and i != channel * 4 + 3:
                    data += int(old_driver_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)

	
        else:
            raise Exception("FEB: Invalid gain specified for a phonon channel: " + str(gain))

    # This method sets a whether a given phonon channel's feedback loop is closed (false) or open (true).
    def set_phonon_feedback_loop(self,subrack, slot, channel, closed):
        if channel >= FEBChannels.A and channel <= FEBChannels.D:
            address = (slot << 8) + (14 << 4) + 1
            data = 0
            squid_CSR = self._get_feb_CSR(subrack, slot)
            if channel == FEBChannels.A:
                data += int(not closed)
                for i in range (1, len(squid_CSR)):
                    data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.B:
                data += int(not closed) << 1
                for i in range(0, len(squid_CSR)):
                    if i!= 1:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.C:
                data += int(not closed) << 2
                for i in range(0, len(squid_CSR)):
                    if i != 2:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.D:
                data += int(not closed) << 3
                for i in range(0, len(squid_CSR)):
                    if i != 3:
                        data += int(squid_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)
        else:
            raise Exception("FEB: Invalid channel value specified for setSquidFeedbackCO(): " + str(channel))


    def set_phonon_feedback_polarity(self,subrack, slot, channel, inverted):
        if (channel >= FEBChannels.A and channel <= FEBChannels.D):
            address = (slot << 8) + (14 << 4) + 1
            data = 0
            squid_CSR = self._get_feb_CSR(subrack, slot)
            if channel == FEBChannels.A:
                data += int(not inverted) << 4
                for i in range (0, len(squid_CSR)):
                    if i != 4:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.B:
                data += int(not inverted) << 5
                for i in range(0, len(squid_CSR)):
                    if i!= 5:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.C:
                data += int(not inverted) << 6
                for i in range(0, len(squid_CSR)):
                    if i != 6:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.D:
                data += int(not inverted) << 7
                for i in range(0, len(squid_CSR)):
                    if i != 7:
                        data += int(squid_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)
        else: 
            raise Exception("FEB: Invalid channel value specified for setSquidFeedbackPolarity(): " + str(channel))



    def set_phonon_source_preamp(self,subrack, slot, channel, enabled):
        if (channel >= FEBChannels.A and channel <= FEBChannels.D):
            address = (slot << 8) + (14 << 4) + 1
            data = 0
            squid_CSR = self._get_feb_CSR(subrack, slot)
            if channel == FEBChannels.A:
                data += int(not enabled) << 12
                for i in range (0, len(squid_CSR)):
                    if i != 12:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.B:
                data += int(not enabled) << 13
                for i in range(0, len(squid_CSR)):
                    if i!= 13:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.C:
                data += int(not enabled) << 14
                for i in range(0, len(squid_CSR)):
                    if i != 14:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.D:
                data += int(not enabled) << 15
                for i in range(0, len(squid_CSR)):
                    if i != 15:
                        data += int(squid_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)
        else: 
            raise Exception("FEB: Invalid channel value specified for setSquidFeedbackPreamp(): " + str(channel))

    def connect_signal_generator_feedback(self,subrack, slot, channel, enabled):
        if (channel >= FEBChannels.A and channel <= FEBChannels.D):
            address = (slot << 8) + (14 << 4) + 1
            data = 0
            squid_CSR = self._get_feb_CSR(subrack, slot)
            if channel == FEBChannels.A:
                data += int(enabled) << 8
                for i in range (0, len(squid_CSR)):
                    if i != 8:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.B:
                data += int(enabled) << 9
                for i in range(0, len(squid_CSR)):
                    if i!= 9:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.C:
                data += int(enabled) << 10
                for i in range(0, len(squid_CSR)):
                    if i != 10:
                        data += int(squid_CSR[i]) << i
            elif channel == FEBChannels.D:
                data += int(enabled) << 11
                for i in range(0, len(squid_CSR)):
                    if i != 11:
                        data += int(squid_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)
        else: 
            raise Exception("FEB: Invalid channel value specified for setSquidExternalSignal(): " + str(channel))

    def connect_signal_generator_tes(self,subrack, slot, channel, enable):
        if (channel >= FEBChannels.A and channel <= FEBChannels.D):
            enable = not enable
            address = (slot << 8) + (14 << 4)
            data = 0
            sense_bias_CSR = self._get_sense_bias(subrack, slot)
            if channel == FEBChannels.A:
                data += int(enable)
                for i in range (1, len(sense_bias_CSR)):
                    data += int(sense_bias_CSR[i]) << i
            elif channel == FEBChannels.B:
                data += int(enable) << 1
                for i in range(0, len(sense_bias_CSR)):
                    if i!= 1:
                        data += int(sense_bias_CSR[i]) << i
            elif channel == FEBChannels.C:
                data += int(enable) << 2
                for i in range(0, len(sense_bias_CSR)):
                    if i != 2:
                        data += int(sense_bias_CSR[i]) << i
            elif channel == FEBChannels.D:
                data += int(enable) << 3
                for i in range(0, len(sense_bias_CSR)):
                    if i != 3:
                        data += int(sense_bias_CSR[i]) << i
            time.sleep(0.16)
            self._write(subrack, address, data)
        else: 
            raise Exception("FEB: Invalid channel value specified for setExternalEnable(): " + str(channel))



    def get_phonon_qet_bias(self,subrack, slot, channel, millisec_delay = 0.160):
        return self._get_feb(subrack, slot, FEBSettings.SENSORBIAS, channel, millisec_delay)
        
    def get_phonon_squid_bias(self,subrack, slot, channel, millisec_delay = 0.160):
        return self._get_feb(subrack, slot, FEBSettings.SQUIDBIAS, channel, millisec_delay)
        
    def get_phonon_lock_point(self,subrack, slot, channel, millisec_delay = 0.160):
        return self._get_feb(subrack, slot, FEBSettings.SQUIDLOCK, channel, millisec_delay)
            
    def get_phonon_feedback_gain(self,subrack, slot, channel, millisec_delay = 0.160):
        return self._get_feb(subrack, slot, FEBSettings.SQUIDGAIN, channel, millisec_delay)

    #this is just SquidDriver in the Java code
    def get_phonon_offset(self,subrack, slot, channel, millisec_delay = 0.160):
        return self._get_feb(subrack, slot, FEBSettings.SQUIDDRIVER, channel, millisec_delay)
        
    def get_phonon_output_gain(self,subrack, slot, channel):
        address = (slot << 8) + (14 << 4) + 2
        channel -= 10
        old_driver_CSR = self._get_feb_driver_CSR(subrack, slot)
        data = 0
        for i in range(channel * 4, channel * 4 + 4):
            if old_driver_CSR[i]:
                data += 1 << (i % 4)
        if data == 0:
            return 1.0
        elif data == 1:
            return 1.43
        elif data == 2:
            return 2.0
        elif data == 3:
            return 5.0
        elif data == 4:
            return 10.0
        elif data == 5:
            return 14.3
        elif data == 6:
            return 20.0
        elif data == 7:
            return 50.0
        elif data == 8:
            return -1.0
        elif data == 9:
            return -1.43
        elif data == 10:
            return -2.0
        elif data == 11:
            return -5.0
        elif data == 12:
            return -10.0
        elif data == 13:
            return -14.3
        elif data == 14:
            return -20.0
        elif data == 15:
            return -50.0
        else:
            raise Exception("FEB: Unable to return a valid phonon channel's gain. Readval: " + str(data))		

    def is_phonon_feedback_open(self,subrack, slot, channel):
        squid_CSR = self._get_feb_CSR(subrack, slot)
        if channel == FEBChannels.A:
            return not squid_CSR[0]
        elif channel == FEBChannels.B:
            return not squid_CSR[1]
        elif channel == FEBChannels.C:
            return not squid_CSR[2]
        elif channel == FEBChannels.D:
            return not squid_CSR[3]
        else:
            raise Exception("FEB: Invalid channel value specified for getSquidFeedbackCO() " + str(channel))

    def get_phonon_feedback_polarity(self,subrack, slot, channel):
        squid_CSR = self._get_feb_CSR(subrack, slot)
        if channel == FEBChannels.A:
            return not squid_CSR[4]
        elif channel == FEBChannels.B:
            return not squid_CSR[5]
        elif channel == FEBChannels.C:
            return not squid_CSR[6]
        elif channel == FEBChannels.D:
            return not squid_CSR[7]
        else:
            raise Exception("FEB: Invalid channel value specified for getSquidFeedbackPolarity() " + str(channel))
	
    def is_phonon_source_preamp(self,subrack, slot, channel):
        squid_CSR = self._get_feb_CSR(subrack, slot)
        if channel == FEBChannels.A:
            return not squid_CSR[12]
        elif channel == FEBChannels.B:
            return not squid_CSR[13]
        elif channel == FEBChannels.C:
            return not squid_CSR[14]
        elif channel == FEBChannels.D:
            return not squid_CSR[15]
        else:
            raise Exception("FEB: Invalid channel value specified for getSquidFeedbackPreamp() " + str(channel))
                
    def is_signal_generator_feedback_connected(self,subrack, slot, channel):
        squid_CSR = self._get_feb_CSR(subrack, slot)
        if channel == FEBChannels.A:
            return squid_CSR[8]
        elif channel == FEBChannels.B:
            return squid_CSR[9]
        elif channel == FEBChannels.C:
            return squid_CSR[10]
        elif channel == FEBChannels.D:
            return squid_CSR[11]
        else:
            raise Exception("FEB: Invalid channel value specified for getSquidExternalSignal() " + str(channel))

    def is_signal_generator_tes_connected(self,subrack, slot, channel):
        sense_bias_CSR = self._get_sense_bias(subrack, slot)
        if channel == FEBChannels.A:
            return not sense_bias_CSR[0]
        elif channel == FEBChannels.B:
            return not sense_bias_CSR[1]
        elif channel == FEBChannels.C:
            return not sense_bias_CSR[2]
        elif channel == FEBChannels.D:
            return not sense_bias_CSR[3]
        else:
            raise Exception("FEB: Invalid channel value specified for getExternalEnable() " + str(channel))






