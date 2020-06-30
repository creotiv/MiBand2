import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np

import csv

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mac', help='MAC address of the device', default="None")
parser.add_argument('-f', '--file', help='CSV data file containing data')
parser.add_argument('-d', '--debug', help='MAC address of the device', default=0)
args = parser.parse_args()

if args.file and args.mac != "None":
    print("Only one of -f/--file or -m/--mac can be specified!")
    exit(1)

if not args.file and args.mac == "None":
    print("One of -f/--file or -m/--mac must be specified!")
    exit(3)

FORMAT = '%(asctime)s.%(msecs)03d-%(levelname)s: %(message)s'
if args.debug == 0:
    logging.basicConfig(
        format=FORMAT, datefmt='%H:%M:%S', level=logging.INFO)
else:
    logging.basicConfig(
        format=FORMAT, datefmt='%H:%M:%S', level=logging.DEBUG)

def plot_file_type1(file_name):
    all_data = []
    time_start = 0
    time_end = time_start
    with open(file_name, 'r') as data_file:
        header = data_file.readline()
        data = data_file.readlines()
        for raw_row in data:
            # Input data is of the form: time, [csv array]
            # Extract the time
            first_comma = raw_row.index(',')
            time = raw_row[:first_comma]
            if time_start == 0:
                time_start = int(time)
            else:
                time_end = int(time)
            # Extract the csv_array
            # Strip spaces, and replace the 
            row_with_brackets = raw_row[first_comma+1:].strip()
            array_string = row_with_brackets.replace('[', '').replace(']','').replace(' ', '')
            logging.debug("%s | %s", time, array_string)
            array_int = [int(i) for i in array_string.split(',')]
            all_data += array_int

    times = np.array(range(len(all_data)))
    duration = time_end - time_start
    logging.debug("Data spans %d seconds", duration)
    timesd = times/(len(all_data)*1.0)
    timesd *= duration
    
    plot_data(timesd, all_data)
            
def start_plot():
    hl, = plt.plot([], [])
    return hl

def update_line(hl, new_data):
    #hl.set_xdata(np.append(hl.get_xdata(), new_data))
    hl.set_ydata(np.append(hl.get_ydata(), new_data))
    plt.draw()
    plt.pause(0.0001)

def plot_data(xdata, ydata):
    plt.plot(xdata, ydata)
    plt.title('Raw PPG data')
    plt.xlabel('Time (s)')
    plt.ylabel('Intensity (arb.)')    
    plt.show()

if args.file:
    print("Plotting data from file: %s " % args.file)
    plot_file_type1(args.file)

