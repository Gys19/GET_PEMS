
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import os
import time
import argparse

class pems_processing:


    def __init__(self, cs_station, lanes, readpath):

        self.lanes = lanes
        self.station_id = cs_station
        self.readpath = readpath

        savepath = os.path.join(readpath, 'TruckVolume')
        if not os.path.exists(savepath):
            os.makedirs(savepath)
            print('Making new folder now...')
        self.savepath = savepath

    def split_by_day(self, df):


        for date in df.Date.dt.date.unique():
            date_str = datetime.datetime.strftime(date, '%Y%m%d')
            temp_df = df[df.Date.dt.date == date].reset_index(drop=True)
            fn = 'cs_{}_{}.xlsx'.format(self.station_id, date_str)
            fpth = os.path.join(self.savepath, fn)
            temp_df.to_excel(fpth, index=None)

    def merge_vc(self, start_dt, end_dt):

        start_date = datetime.datetime.strptime(start_dt, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_dt, '%Y-%m-%d')

        sd_str = datetime.datetime.strftime(start_date, '%Y%m%d')
        ed_str = datetime.datetime.strftime(end_date, '%Y%m%d')


        sum_output = os.path.join(self.savepath, 'CS_{}_{}_{}.xlsx'.format(self.station_id, sd_str, ed_str))  # summary excel for one week data
        writer = pd.ExcelWriter(sum_output)

        TRUCK = pd.DataFrame()
        WIM_TOTAL = pd.DataFrame()

        vc = list(np.arange(2, 16))
        vc.insert(0, 0)
        fn = '{}_{}.{}.{}.xlsx'

        for lane in range(1, self.lanes+1):

            DF = pd.DataFrame()
            truck = pd.DataFrame()
            wim_lane = pd.DataFrame()

            for c in vc:  # loop class

                f = os.path.join(self.readpath, fn.format(sd_str, ed_str, lane, c))
                # print(f
                temp_df = pd.read_excel(f)
                DF[['v{}{}'.format(lane, c), 'len{}{}'.format(lane, c)]] = temp_df.iloc[:,1:]  # contain all vehicle types
                if c in range(8, 14):
                    truck[f'v{lane}{c}'] = temp_df.iloc[:, 1]  # only count truck volume
                if c == 0:
                    wim_lane[f'v{lane}{c}'] = temp_df.iloc[:, 1]  # only count the total volume

            DF['Date'] = temp_df.Date

            DF.to_excel(writer, 'Lane' + str(lane), index=None)
            sum_truck = truck.sum(axis=1)
            TRUCK[f'Lane{lane}Truck'] = sum_truck
            WIM_TOTAL[f'Lane{lane}Flow'] = wim_lane[f'v{lane}0']

        FINAL = pd.concat([TRUCK, WIM_TOTAL], ignore_index=False, axis=1)
        FINAL["Date"] = temp_df.Date

        self.split_by_day(FINAL)  # split truck data by day

        FINAL.to_excel(writer, 'summary', index=None)
        writer.save()


if __name__ == "__main__":

    def set_parse():

        parser = argparse.ArgumentParser(description='prepare truck volume')
        # parser.add_argument('-sp','--savepath', type = str, help = 'path of saving truck volume')
        parser.add_argument('-rp','--readpath', type = str, help = 'read path of raw vehicle classification')
        parser.add_argument('-cs','--cs_station',type = int, help = 'census station')
        parser.add_argument('-sd', '--start_date', type = str, help = 'start_date')
        # parser.add_argument('-ed', '--end_date', type = str, help='end_date')
        parser.add_argument('-ln','--lanes', type = int, help ='number of lanes')
        args = parser.parse_args()

        return args


    args = set_parse()
    cs_station = args.cs_station
    lanes = args.lanes
    readpath = args.readpath
    start_date = args.start_date
    end_date = datetime.datetime.strptime(start_date,'%Y-%m-%d') + datetime.timedelta(days = 6)
    end_date = datetime.datetime.strftime(end_date, '%Y-%m-%d')

    merge_pems = pems_processing(cs_station, lanes, readpath)

    merge_pems.merge_vc(start_date, end_date)

