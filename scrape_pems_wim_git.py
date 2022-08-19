
# package 
# selenium==3.141.0

import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import datetime
import time
import os
import string
import numpy as np
import argparse



class autoPems:


    def __init__(self,savepath, username, password, cs_station, direction):

        self.savepath = savepath
        self.username = username
        self.password = password

        self.station_id = cs_station
        self.direction = direction

        self.init_driver()


    def random_user(self):

        random_str = list(string.ascii_lowercase[:])
        random.shuffle(random_str)
        agent = "".join(random_str)

        return agent

    def init_driver(self):

        agent_user = self.random_user()
        opts = webdriver.ChromeOptions()
        prefs = {'download.default_directory': self.savepath}  # set the default download path
        opts.add_experimental_option('prefs', prefs)
        opts.add_argument("user-agent={}".format(agent_user))
        self.driver = webdriver.Chrome("chromedriver.exe", options=opts)
        self.login()

    def login(self):

        self.driver.get("https://pems.dot.ca.gov/")
        # find username/email field and send the username itself to the input field
        self.driver.find_element_by_id("username").send_keys(self.username)
        # find password input field and insert password as well
        self.driver.find_element_by_id("password").send_keys(self.password)
        # click login button
        self.driver.find_element_by_name("login").click()

    def gen_input_params(self, start_date, end_date):


        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        if end_date >= start_date + datetime.timedelta(days = 8):

            print('please choose a new date range, the maximum range is 7 days')

        start_date_epoch = str(start_date.timestamp())
        end_date_epoch = str(end_date.timestamp())
        # 11%2F01%2F2021
        start_date_f = start_date.strftime('%m') + '%2F' + start_date.strftime('%d') + '%2F' + start_date.strftime("%Y")
        end_date_f = end_date.strftime('%m') + '%2F' + end_date.strftime('%d') + '%2F' + end_date.strftime("%Y")

        param_list = [start_date_epoch, start_date_f, end_date_epoch, end_date_f]

        return param_list


    def pemsURL(self, start_date, end_date, lanes):

        ''':returns
        generate url for target data'''

        start_date_, start_date_f_, end_date_, end_date_f_ = self.gen_input_params(start_date, end_date)
        vclass = list(np.arange(2, 16))
        vclass.insert(0, 0)  # vehicle classification id
        lanes_id = list(np.arange(lanes+1))  # 0 is all
        # init_url is used to trigger the web but we still need the direction information (i.e., tmg_sub_id)

        init_url = """ https://pems.dot.ca.gov/? 
                    report_form=1&dnode=tmgs&content=tmg_trucks& 
                    tab=tmg_wim_ts&export=&tmg_station_id={}& 
                    s_time_id={}&s_time_id_f={}& 
                    e_time_id={}&e_time_id_f={}&
                    tod=all&tod_from=0&tod_to=0&dow_0=on&
                    dow_1=on&
                    dow_2=on&
                    dow_3=on&
                    dow_4=on&
                    dow_5=on&
                    dow_6=on&
                    holidays=on&
                    gn=hour&
                    q=volume&
                    q2=avg_len&
                    """.format(self.station_id, start_date_, start_date_f_, end_date_, end_date_f_)

        self.driver.get(init_url)  # jump to the filter page

        # further we need to set the direction, vehicle type, and lanes
        # set the direction_id
        direction = self.driver.find_element_by_name("tmg_sub_id")
        dirlist = direction.find_elements_by_tag_name('option')
        direction_id = [x.get_attribute('value') for x in dirlist if x.text == self.direction][0]

        # generate a list of url
        url = {}
        for ln in lanes_id[1:]:
            for vc in vclass:
                temp_url = init_url + f'tmg_sub_id={direction_id}&' + f'lanes={ln}&' + f'vc={vc}&'
                print('URL....:', temp_url)
                # url.append({(ln, vc), temp_url})
                url[(ln, vc)] = temp_url
        print('Finishing generating all urls, total # of url is: ', len(url))

        return url


    def ignitor(self,start_date, end_date, lanes):

        ''':returns
        loop all url and download data
        '''

        URL = self.pemsURL(start_date, end_date, lanes)

        start_date_= datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_ = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()


        for key, url in URL.items():


            self.driver.get(url)
            self.driver.find_element_by_name('xls').click()

            new_name = os.path.join(self.savepath, start_date_.strftime('%Y%m%d') + '_' + end_date_.strftime('%Y%m%d') + f'.{key[0]}.{key[1]}.xlsx')
            old_name = os.path.join(self.savepath, 'pems_output.xlsx')

            time.sleep(3)
            while not os.path.exists(old_name):
                time.sleep(1)
            os.rename(old_name, new_name)



if __name__== '__main__':

    def set_parse():

        parser = argparse.ArgumentParser(description='scrape pems wim station data')
        parser.add_argument('-sp','--savepath', type = str, help = 'download path of data')
        parser.add_argument('-un','--username', type = str, help = 'username')
        parser.add_argument('-pwd', '--password',type= str, help= 'password')
        parser.add_argument('-cs','--cs_station',type = int, help = 'census station')
        parser.add_argument('-sd', '--start_date', type = str, help = 'start_date')
        # parser.add_argument('-ed', '--end_date', type = str, help='end_date')
        parser.add_argument('-d','--direction', type = str, help = 'direction')
        parser.add_argument('-ln','--lanes', type = int, help ='number of lanes')

        args = parser.parse_args()

        return args

    args = set_parse()

    savepath = args.savepath
    username = args.username
    password = args.password
    cs_station = args.cs_station
    direction = args.direction
    start_date = args.start_date
    # end_date = args.end_date
    end_date = datetime.datetime.strptime(start_date,'%Y-%m-%d') + datetime.timedelta(days = 6)
    end_date = datetime.datetime.strftime(end_date, '%Y-%m-%d')
    lanes = args.lanes

    print(cs_station, username)
    # savepath = r'C:\Users\guyan\Dropbox\Yangsong_Fifth_smester\TruckIdentification\Yangsong\PemsMonthData\WIM_Nov_2021_auto'
    #     # username = "***********"
    #     # password = "**********"
    #     # cs_station = '-----'
    #     # direction = 'Eastbound'
    #     # start_date = '2021-11-01'
    #     # end_date = '2021-11-07' # max search range is 7 days
    #     # lanes = 3

    WIM = autoPems(savepath, username, password, cs_station, direction)
    WIM.ignitor(start_date, end_date, lanes)



