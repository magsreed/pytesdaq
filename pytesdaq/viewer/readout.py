import time
import numpy as np
from PyQt5.QtCore import QCoreApplication
from matplotlib import pyplot as plt
import pytesdaq.daq as daq
import pytesdaq.config.settings as settings
from pytesdaq.utils import  arg_utils
import pytesdaq.io.redis as redis
import pytesdaq.io.hdf5 as hdf5

class Readout:
    
    def __init__(self):
            
        
        #self._web_scope = web_scope

        # data source: 
        self._data_source = 'niadc'


        # ADC device 
        self._adc_name = 'adc1'


        # initialize db/adc
        self._daq = None
        self._redis = None
        self._hdf5 = None

        # Is running flag
        self._is_running = False

        # data configuration
        self._data_config = dict()

        # qt UI / trace display
        self._is_qt_ui = False
        self._first_draw = True
        self._plot_ref = None
        self._selected_channel_list = list()
        self._axes=[]
        self._canvas = []
        self._status_bar = []
        self._colors = dict()
     
        


    def register_ui(self,axes,canvas,status_bar,colors):
        self._is_qt_ui = True
        self._axes = axes
        self._canvas = canvas
        self._status_bar = status_bar

        # need to divide by 255
        for key,value in colors.items():
            color = (value[0]/255, value[1]/255,value[2]/255)
            self._colors[key] = color
  
    def select_channels(self, channels):

        self._first_draw = True
        self._selected_channel_list = channels



    def configure(self,data_source, adc_name = 'adc1', channel_list=[],
                  sample_rate=[], trace_length=[],
                  voltage_min=[], voltage_max=[],trigger_type=3,
                  file_list=[]):
        

        
        # check if running
        if self._is_running:
            print('WARNING: Need to stop display first')
            return False
            
        # data source 
        self._data_source = data_source

        # adc name 
        self._adc_name = adc_name


        # read configuration file
        self._config = settings.Config()
        self._data_config = dict()

        # NI ADC source
        if self._data_source == 'niadc':

            # check
            if not channel_list or not adc_name:
                error_msg = 'ERROR: Missing channel list or adc name!'
                return error_msg

            # instantiate daq
            self._daq  = daq.DAQ(driver_name = 'pydaqmx',verbose = False)
            self._daq.lock_daq = True
            
            # configuration
            adc_list = self._config.get_adc_list()
            if adc_name not in adc_list:
                self._daq.clear()
                error_msg = 'ERROR: ADC name "' + adc_name + '" unrecognized!'
                return error_msg
                
                
            self._data_config = self._config.get_adc_setup(adc_name)
            self._data_config['channel_list'] = channel_list
            if sample_rate:
                self._data_config['sample_rate'] = int(sample_rate)
            if trace_length:
                nb_samples = round(self._data_config['sample_rate']*trace_length/1000)
                self._data_config['nb_samples'] = int(nb_samples)
            if voltage_min:
                self._data_config['voltage_min'] = float(voltage_min)
            if voltage_max:
                self._data_config['voltage_max'] = float(voltage_max)
            
            self._data_config['trigger_type'] = int(trigger_type)

            adc_config = dict()
            adc_config[adc_name] =  self._data_config
            self._daq.set_adc_config_from_dict(adc_config)

  
        # Redis
        elif self._data_source == 'redis':

            self._redis = redis.RedisCore()
            self._redis.connect()
        
        
        # hdf5
        elif self._data_source == 'hdf5':

            if not file_list:
                error_msg = 'ERROR from readout: No files provided'
                return error_msg

            self._hdf5 = hdf5.H5Core()
            self._hdf5.set_files(file_list)
            
                
    
        return True



    def stop_run(self):
        self._do_stop_run = True


    def clear_daq(self):
        self._do_stop_run = True
        if self._data_source == 'niadc':
            self._daq.clear()    
       

    def is_running(self):
        return self._is_running


    def run(self,save_redis=False,do_plot=False):
        

        # =========================
        # Initialize data container
        # =========================\
        self._data_array = []
        self._data_array_avg  = []
        if self._data_source == 'niadc':
            nb_channels = len(self._data_config['channel_list'])
            nb_samples =  self._data_config['nb_samples']
            self._data_array = np.zeros((nb_channels,nb_samples), dtype=np.int16)
            self._data_array_avg = np.zeros((nb_channels,nb_samples), dtype=np.int16)
            

        # =========================
        # LOOP Events
        # =========================
        self._do_stop_run = False
        self._is_running = True
        self._first_draw = True
        
        while (not self._do_stop_run):
            
            # event QT process
            if self._is_qt_ui:
                QCoreApplication.processEvents()
                

            # get traces
            if self._data_source == 'niadc':
                self._daq.read_single_event(self._data_array, do_clear_task=False)

            elif self._data_source == 'hdf5':

                self._data_array, self._data_config = self._hdf5.read_event(include_metadata=True,
                                                                            adc_name=self._adc_name)
                
                if isinstance(self._data_array,str):
                    if self._is_qt_ui:
                        self._status_bar.showMessage('INFO: ' + self._data_array)
                    break
                self._data_config['channel_list'] = self._data_config['adc_channel_indices']

                if 'event_num' in self._data_config and self._is_qt_ui:
                    self._status_bar.showMessage('INFO: EventNumber = ' + str(self._data_config['event_num']))
            
            else:
                print('Not implemented')
                
            if do_plot:
                self._plot_data()
         
       
        # clear
        if self._data_source == 'niadc':
            self._daq.clear()    
        self._is_running = False





    def _plot_data(self):


        if self._do_stop_run:
            return

        # check if seletect channels can be display
        channel_num_list = list()
        channel_index_list = list()
        counter = 0
        for chan in self._data_config['channel_list']:
            if chan in self._selected_channel_list:
                channel_num_list.append(chan)
                channel_index_list.append(counter)
            counter+=1
                
        nchan_display = len(channel_num_list)
        if nchan_display==0:
            return
    
        # chan/bins
        nchan =  np.size(self._data_array,0)
        nbins =  np.size(self._data_array,1)
    
        if self._first_draw:
            dt = 1/self._data_config['sample_rate']
            self._axes.clear()
            self._axes.set_xlabel('ms')
            self._axes.set_ylabel('ADC bins')
            self._axes.set_title('Pulse')
            x_axis=np.arange(0,nbins)*1e3*dt
            self._plot_ref = [None]*nchan_display
            for ichan in range(nchan_display):
                chan = channel_num_list[ichan]
                idx = channel_index_list[ichan]
                self._plot_ref[ichan], = self._axes.plot(x_axis,self._data_array[idx],
                                                         color = self._colors[chan])  
            self._canvas.draw()
            self._first_draw = False
        else:
            for ichan in range(nchan_display):
                chan = channel_num_list[ichan]
                idx = channel_index_list[ichan]
                self._plot_ref[ichan].set_ydata(self._data_array[idx])
                        
        self._axes.relim()
        self._axes.autoscale_view()
        self._canvas.draw()
        self._canvas.flush_events()
            