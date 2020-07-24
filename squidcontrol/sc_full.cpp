#include <iostream>
#include <time.h>
#include <thread>
#include <chrono>
#include <string>
#include "magsv.h"

using namespace std;

void errorout(unsigned short error) {
    if (error != 0)
        cout << "\nCommunication Error" << endl;
}

int setup(unsigned short channel, unsigned short error) {

    printf("WIN\tSetting Channel %d as active\n", channel);
    MA_SetActiveChannel(channel, &error);
    errorout(error);

    cout << "WIN\tReading Magnicon settings of Channel 1" << endl;
    unsigned short type_id, version_id, board_id, case_id;
    MA_channelInfo(channel, &error, &type_id, &version_id, &board_id, &case_id);
    errorout(error);
    printf("\t\t\tType ID: %d   Version ID: %d   Board ID: %d   Case ID: %d\n",
        type_id, version_id, board_id, case_id);

    cout << "WIN\tTurning off dummy SQUID if active." << endl;
    unsigned short dummy = 0;
    MA_read_Dummy(channel, &error, &dummy);
    errorout(error);
    if (dummy == 1) {
        dummy = 0;
        MA_write_Dummy(channel, &error, dummy);
        errorout(error);
    }
    MA_read_Dummy(channel, &error, &dummy);
    errorout(error);
    cout << "\t\t\tSQUID dummy state is " << dummy << endl;

    cout << "WIN\tReading electronics mode" << endl;
    unsigned short ampfll = 0;
    MA_read_Amp(channel, &error, &ampfll);
    if (ampfll == 0) {
        cout << "\t\t\tElectronics in AMP mode." << endl;
    }
    else {
        cout << "\t\t\tElectronics in FLL mode." << endl;
    }

    double ranges[3] = {0, 0, 0}; // array for Ib, Phib, and Vb range information
    long len = 3; // length of ranges[] array
    unsigned short Ib_range = 0; // meaningless, but a required argument
    double Ib = 0;
    MA_read_Ib(channel, &error, &ranges[0], len, &Ib_range, &Ib);
    errorout(error);
    cout << "WIN\tRead bias current through dummy:" << endl;
    cout << "\t\t\tIb value in uA: " << Ib << endl;
    printf("\t\t\tIb Max = %.3f   Ib Min = %.3f   Ib LSB = %.6f\n",
        ranges[0], ranges[1], ranges[2]);
    
    unsigned short PhibDisc = 0;
    double Phib = 0;
    MA_read_PhibDisc(channel, &error, &PhibDisc);
    errorout(error);
    if (PhibDisc == 1) {
        cout << "WIN\tFlux bias is connected. Read flux bias through dummy:" << endl;

        MA_read_Phiob(channel, &error, &ranges[0], len, &Phib);
        cout << "\t\t\tPhib value in uA: " << Phib << endl;
        printf("\t\t\tPhib Max = %.3f   Phib Min = %.3f   Phib LSB = %.6f\n",
            ranges[0], ranges[1], ranges[2]);
    }
    else {
        cout << "WIN\tFlux bias is disconnected" << endl;
    }

    double Vb = 0;
    MA_read_Vb(channel, &error, &ranges[0], len, &Vb);
    errorout(error);
    cout << "WIN\tRead bias voltage at preamplifier input:" << endl;
    cout << "\t\t\tVb value in uV: " << Vb << endl;
    printf("\t\t\tVb Max = %.3f   Vb Min = %.3f   Vb LSB = %.6f\n",
        ranges[0], ranges[1], ranges[2]);

    double Iaux = 0;
    unsigned short Iaux_range = 0;
    MA_read_Iaux(channel, &error, &ranges[0], len, &Iaux_range, &Iaux);
    errorout(error);
    cout << "WIN\tRead auxiliary current:" << endl;
    if (Iaux_range == 0) {
        cout << "\t\t\tIaux value in uA: " << Iaux << " (low mode)" << endl;
    }
    else {
        cout << "\t\t\tIaux value in uA: " << Iaux << " (high mode)" << endl;
    }
    
    cout << flush;
    return 0;
}



double setIb(unsigned short channel, unsigned short error, double Ib_new) {

    unsigned short Ib_range = 0;
    double Ib_out = 0;

    printf("WIN\tAttempting to set Ib = %.3f uA\n", Ib_new);
    MA_write_Ib(channel, &error, Ib_new, Ib_range, &Ib_out);
    errorout(error);
    printf("\t\t\tActually set Ib = %.3f uA\n", Ib_out);
    
    cout << flush;
    return Ib_out;
}



double setVb(unsigned short channel, unsigned short error, double Vb_new) {

    double Vb_out = 0;

    printf("WIN\tAttempting to set Vb = %.3f uV\n", Vb_new);
    MA_write_Vb(channel, &error, Vb_new, &Vb_out);
    errorout(error);
    printf("\t\t\tActually set Vb = %.3f uV\n", Vb_out);
    
    cout << flush;
    return Vb_out;
}



double setPhib(unsigned short channel, unsigned short error, double Phib_new) {

    double Phib_out = 0;

    printf("WIN\tAttempting to set Phib = %.3f uA\n", Phib_new);
    MA_write_Phiob(channel, &error, Phib_new, &Phib_out);
    errorout(error);
    printf("\t\t\tActually set Phib = %.3f uA\n", Phib_out);
    
    cout << flush;
    return Phib_out;
}



double setIaux(unsigned short channel, unsigned short error, double Iaux_new, double Iaux_mode_new) {

    double Iaux_out = 0;

    printf("WIN\tAttempting to set Iaux = %.3f uA\n", Iaux_new);
    MA_write_Iaux(channel, &error, Iaux_new, Iaux_mode_new, &Iaux_out);
    errorout(error);
    printf("\t\t\tActually set Iaux = %.3f uA\n", Iaux_out);
    
    cout << flush;
    return Iaux_out;
}



void setAmpMode(unsigned short channel, unsigned short error, unsigned short ampfll) {

    if (ampfll == 0) {
        cout << "WIN\tSetting mode to AMP" << endl;
    }
    else if (ampfll == 1) {
        cout << "WIN\tSetting mode to FLL" << endl;
    }
    MA_write_Amp(channel, &error, ampfll);
    errorout(error);

    return;
}


int readBiasesAndOutputs(unsigned short channel, unsigned short error, int amp_gain) {

    double ranges[3] = {0, 0, 0}; // array for Ib, Phib, and Vb range information
    long len = 3;
    unsigned short Ib_range = 0; // meaningless, but a required argument
    double Ib = 0, Phib = 0, Vb = 0, V_Vb = 0, Vout = 0;
    
    MA_read_Ib(channel, &error, &ranges[0], len, &Ib_range, &Ib);
    errorout(error);
    printf("WIN\tIb = %7.2f uA     ", Ib);
    
    MA_read_Phiob(channel, &error, &ranges[0], len, &Phib);
    errorout(error);
    printf("Phib = %7.2f uA     ", Phib);

    MA_read_Vb(channel, &error, &ranges[0], len, &Vb);
    errorout(error);
    printf("Vb = %7.2f uV     ", Vb);

    MA_read_V_Vb(channel, &error, &V_Vb);
    errorout(error);
    printf("V - Vb = %7.2f uV     ", V_Vb);

    MA_read_Vout(channel, &error, &Vout);
    errorout(error);
    printf("Vout (x%d) = %7.3f V\n", amp_gain, Vout);
    
    cout << flush;
    return 0;
}



// Params, in order are: mode, Iaux_range, Iaux, Vb, Ib, Phib, time to run
void loadConfig(int argc, char** argv, double* params) {

    double tmp = 0;
    string s = "";
    string s1 = "";

    for (int i = 1; i < argc; i++) {
        s = argv[i];
        if (i != (argc - 1))
            s1 = argv[i+1];

        if (s.compare("-mode") == 0) {
            if (s1.compare("AMP") == 0) {
                params[0] = 0;
            }
            else if (s1.compare("FLL") == 0) {
                params[0] = 1;
            }
            else {
                cout << "WIN\tWarning: You entered an inappropriate mode. The mode should be either AMP or FLL." << endl;
                cout << "\t\t\tContinuing without setting mode." << endl;
            }
        }
        if (s.compare("-Iaux") == 0) {
            int Iaux_range;
            if (s1.compare("low") == 0) {
                params[1] = 0;
                params[2] = stod(argv[i+2]);
            }
            else if (s1.compare("high") == 0) {
                params[1] = 1;
                params[2] = stod(argv[i+2]);
            }
            else {
                cout << "WIN\tWarning: You entered an inappropriate Iaux_range. The Iaux_range should be either low or high." << endl;
                cout << "\t\t\tContinuing without setting Iaux." << endl;
            }
        }
        if (s.compare("-Vb") == 0) {
            tmp = stod(argv[i+1]);
            if (tmp < 0 || tmp > 1300) {
                cout << "WIN\tWarning: You entered an inappropriate Vb. Vb should be between 0 - 1300." << endl;
                cout << "\t\t\tContinuing without setting Vb." << endl;
            }
            else {
                params[3] = tmp;
            }
        }
        if (s.compare("-Ib") == 0) {
            tmp = stod(argv[i+1]);
            if (tmp < 0 || tmp > 180) {
                cout << "WIN\tWarning: You entered an inappropriate Ib. Ib should be between 0 - 180." << endl;
                cout << "\t\t\tContinuing without setting Ib." << endl;
            }
            else {
                params[4] = tmp;
            }
        }
        if (s.compare("-Phib") == 0) {
            tmp = stod(argv[i+1]);
            if (tmp < -125 || tmp > 125) {
                cout << "WIN\tWarning: You entered an inappropriate Phib. Phib should be between -125 - +125." << endl;
                cout << "\t\t\tContinuing without setting Phib." << endl;
            }
            else {
                params[5] = tmp;
            }
        }
        if (s.compare("-time") == 0) {
            params[6] = stod(argv[i+1]);
            cout << "WIN\tSetting time = " << params[6] << " seconds" << endl;
        }
    }

    if (params[6] <= 0 || params[6] > 9e8) {
        cout << "WIN\tWarning: You entered an inappropriate runtime or did not set a runtime. Setting runtime to 1 hour." << endl;
        params[6] = 3600.;
    }

}



int main(int argc, char** argv) {
    
    if (argc == 1) {
        cout << "WIN\tWarning: The program will execute, but you have not set any parameters." << endl;
        cout << "\t\t\tRun like this: .\\squidcontrol.exe [-mode mode(AMP/FLL)] [-Iaux range(low/high) Iaux] [-Vb Vb] [-Ib Ib] [-Phib Phib]" << endl;
    }

    unsigned short error = 0, channel = 1;
    unsigned long baud = 57600, timeout = 100; // default settings
    int status = 0;
    long t_start = time(NULL);
    
    // Connect to electronics
    cout << "WIN\tInitializing USB connection to electronics" << endl;
    MA_initUSB(&error, baud, timeout);
    errorout(error);
    
    // Set active channel, de-activate dummy, and read existing biases
    cout << "WIN\tReading current electronics settings" << endl;
    status = setup(channel, error);
    if (status != 0)
        return status;
    cout << endl << "Pausing for 5 seconds" << endl;
    this_thread::sleep_for(chrono::milliseconds(5000));

    // Set user-defined params
    // Params, in order are: mode, Iaux_range, Iaux, Vb, Ib, Phib, time to run
    cout << endl << "WIN\tSetting user-defined parameters" << endl;
    double params[7] = {1e9, 1e9, 1e9, 1e9, 1e9, 1e9, 1e9};
    loadConfig(argc, argv, params);
    
    if (params[0] < 9e8) {
        setAmpMode(channel, error, params[0]);
    }
    if (params[1] < 9e8 && params[2] < 9e8) {
        setIaux(channel, error, params[2], params[1]);
    }
    if (params[3] < 9e8) {
        setVb(channel, error, params[3]);
    }
    if (params[4] < 9e8) {
        setIb(channel, error, params[4]);
    }
    if (params[5] < 9e8) {
        setPhib(channel, error, params[5]);
    }

    // Read amplification gain
    unsigned short amp_gain = 0, amp_bw = 0;
    int amp_gain_dict[4] = {1100, 1400, 1700, 2000};
    double amp_bw_dict[7] = {0.2, 0.7, 1.4, 0, 100, 0, 0};
    MA_read_AmpMode(channel, &error, &amp_gain, &amp_bw);

    // Set Ib = 0, read biases and output
    cout << endl << endl;
    t_start = time(NULL);
    while ((time(NULL) - t_start) < params[6]) {
        readBiasesAndOutputs(channel, error, amp_gain_dict[amp_gain]);
        this_thread::sleep_for(chrono::milliseconds(2000));
    }

    // Close electronics connection
    cout << endl << endl;
    cout << "WIN\tClosing connection to electronics" << endl;
    MA_closeUSB(&error);
    errorout(error);
    
    return 0;    
}