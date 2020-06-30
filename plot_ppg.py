import argparse
import logging
import matplotlib.pyplot as plt
import matplotlib.axes as plt_axes
import numpy as np
import time

from base import MiBand2
from bluepy.btle import BTLEException


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
    
    plot_all_data(timesd, all_data)

def plot_all_data(xdata, ydata):
    plt.plot(xdata, ydata)
    plt.title('Raw PPG data')
    plt.xlabel('Time (s)')
    plt.ylabel('Intensity (arb.)')    
    plt.show()
            
def start_plot():
    global ax
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    hl, = plt.plot([], [])
    plt.title('Raw PPG data')
    plt.xlabel('Time (s)')
    plt.ylabel('Intensity (arb.)')    
    return hl

def update_line(ax, hl, new_xdata, new_ydata):
    hl.set_xdata(np.append(hl.get_xdata(), new_xdata))
    hl.set_ydata(np.append(hl.get_ydata(), new_ydata))
    
    ax.relim()
    ax.autoscale_view() 
    
    plt.draw()
    plt.pause(0.0001)


def plot_data(time_offset, delta_t, data):
    global ax, plot
    new_times = np.array(range(len(data)))
    new_times = new_times/(len(data)*1.0)
    new_times *= delta_t*len(data)
    new_times += time_offset
    
    logging.info("dt: %s, Offset: %s", delta_t, time_offset)
    update_line(ax, plot, new_times, data)

def raw_data(data):
    global num_data_points, start_time, last_time, dt, old_data
    
    now = time.time()
    
    if num_data_points == 0:
        num_data_points = len(data)
        old_data = data
        last_time = now
        return


    if old_data is not None:
        dt = 0.04# (now - last_time)/len(data)
        start_time = now - dt*num_data_points
        logging.info("Initial dt: %s", dt)
        plot_data(0, dt, old_data)
        old_data = None

    dt = 0.04# (now - start_time)/(len(data)+num_data_points)
    logging.debug("Updated dt: %s", dt)

    time_offset = num_data_points * dt
    plot_data(time_offset, dt, data)
    
    num_data_points += len(data)
    last_time = now

def plot_live_test(MAC):
    raw_data([1,3,2])
    time.sleep(1)
    raw_data([4,3,5])
    plt.show()

def plot_live(MAC):
    try:
        band = MiBand2(MAC, debug=True)
        band.setSecurityLevel(level="medium")
        band.authenticate()
        band.start_ppg_data_realtime(sample_duration_seconds=60, heart_raw_callback=raw_data)
        band.disconnect()
        plt.show()
    except BTLEException:
        pass

if args.file:
    print("Plotting data from file: %s " % args.file)
    plot_file_type1(args.file)
elif args.mac != "None":
    print("Plotting live data from device: %s " % args.mac)
    num_data_points = 0
    plot = start_plot()
    plot_live(args.mac)

