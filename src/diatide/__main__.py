import argparse
import json
import hashlib
import datetime
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytz
import requests
import xlrd
import yaml


class Tidepool:
    API_URL = "https://api.tidepool.org/"
    UPLOAD_URL = "https://uploads.tidepool.org/"
    
    CBGdeviceId = None
    SMBGdeviceId = None

    timezone = pytz.timezone('Europe/London') # timezone

    # Generate unique upload ID for each upload session
    def gen_uploadId(self,deviceId):
        m = hashlib.md5()
        meta = deviceId + "_" + str(datetime.datetime.now())
        m.update(meta.encode('utf8'))
        self.uploadId = "upid_" + m.hexdigest()[0:12]

    # Login to tidepool account
    def login(self,email,passd):
        r = requests.post(self.API_URL+"auth/login", auth=(email, passd))
        token = r.headers['x-tidepool-session-token']
        response = json.loads(r.text)
        self.userid = response['userid']
        self.token = token

    # Refresh token
    def refresh(self):
        headers = {'x-tidepool-session-token':self.token}
        r = requests.get(self.API_URL+"auth/login",headers=headers)

    # Get the group which the current user is assigned to
    def get_groups(self):
        headers = {'x-tidepool-session-token':self.token}
        r = requests.get(self.API_URL+"access/groups/%s"%self.userid,headers=headers)
        groups = json.loads(r.text)
        self.groups = groups
        return groups

    def logout(self):
        headers = {'x-tidepool-session-token':self.token}
        r = requests.post(self.API_URL+"auth/logout",headers=headers)

    def upload_cbg(self,cbg):#,group):
        """Upload cbg data to tidepool

        :cbg: a list of (date,glucose) tuples
        """

        assert self.CBGdeviceId is not None
        #assert group in self.groups

        self.gen_uploadId(self.CBGdeviceId) # Generate new uploadId

        headers = {'x-tidepool-session-token':self.token,'Content-Type':'application/json'}

        for timestamp,glucose in cbg:
            deviceTime = timestamp.isoformat()  # Format time
    
            # Add UTC offset
            UTCtimestamp = self.timezone.localize(timestamp)
            tzoffset = int(UTCtimestamp.utcoffset().total_seconds()/60)

            # Create the data payload
            uploaddata = {
                "type": "cbg",
                "units": "mmol/L",
                "value": glucose,
                "clockDriftOffset": 0,
                "conversionOffset": 0,
                "deviceId": self.CBGdeviceId,
                "deviceTime": deviceTime,
                "time": UTCtimestamp.isoformat(),
                "timezoneOffset": tzoffset,
                "uploadId": self.uploadId
            }

            # Upload data
            print("Uploading..",deviceTime,glucose)
            r = requests.post(self.UPLOAD_URL+"data",headers=headers,json=uploaddata)
        return

    # Upload smbg data to tidepool
    # smbg is a list of tuple (date,glucose)
    def upload_smbg(self,smbg):#,group):
        assert self.SMBGdeviceId is not None
        #assert group in self.groups

        self.gen_uploadId(self.SMBGdeviceId) # Generate new uploadId

        headers = {'x-tidepool-session-token':self.token,'Content-Type':'application/json'}

        for timestamp,glucose in smbg:
            deviceTime = timestamp.isoformat()  # Format time
    
            # Add UTC offset
            UTCtimestamp = self.timezone.localize(timestamp)
            tzoffset = int(UTCtimestamp.utcoffset().total_seconds()/60)

            # Create the data payload
            uploaddata = {
                "type": "smbg",
                "subType": "manual",
                "units": "mmol/L",
                "value": glucose,
                "clockDriftOffset": 0,
                "conversionOffset": 0,
                "deviceId": self.SMBGdeviceId,
                "deviceTime": deviceTime,
                "time": UTCtimestamp.isoformat(),
                "timezoneOffset": tzoffset,
                "uploadId": self.uploadId
            }

            # Upload data
            print("Uploading..",deviceTime,glucose)
            r = requests.post(self.UPLOAD_URL+"data",headers=headers,json=uploaddata)
        return

# Function to convert Diasend timestamp to ISO
def parse_timestamp(timestamp: str, date_format: str) -> datetime.datetime:
    timestamp = datetime.datetime.strptime(timestamp, date_format)
    return timestamp

# Function to read smbg and cbg data from Diasend xls file
def load_workbook(filename: Path, date_format: str):
    workbook = xlrd.open_workbook(filename)
    
    # Get smbg data from first tab
    sheet_smbg = workbook.sheet_by_index(0)
    Ndata = sheet_smbg.nrows

    smbg,cbg = [],[]

    for row in range(5,Ndata):
        timestamp = sheet_smbg.cell(row,0).value

        try:
            isotime   = parse_timestamp(timestamp, date_format)
        except ValueError as e:
            print(f"ERROR: error parsing timestamp {timestamp}: {e}; skipping record {row!r}", file=sys.stderr)
            continue

        glucose   = sheet_smbg.cell(row,1).value
        smbg.append((isotime,glucose))

    # Get cbg data from second tab
    sheet_cbg = workbook.sheet_by_index(1)
    Ndata = sheet_cbg.nrows

    for row in range(2,Ndata):
        timestamp = sheet_cbg.cell(row,0).value
        try:
            isotime   = parse_timestamp(timestamp, date_format)
        except ValueError as e:
            print(f"ERROR: error parsing timestamp {timestamp}: {e}; skipping record {row!r}", file=sys.stderr)
            continue
        glucose   = sheet_cbg.cell(row,1).value
        cbg.append((isotime,glucose))

    return smbg,cbg


@dataclass
class Config:
    email: str
    password: str
    cgm_device_id: str
    bg_meter_device_id: str
    date_format: str

    @classmethod
    def from_file_path(self, yaml_fpath: Path) -> 'Config':
        with open(yaml_fpath, 'r') as fp:
            yaml_data = yaml.load(fp, yaml.Loader)

        assert yaml_data is not None

        return Config(
            email=yaml_data['email'],
            password=yaml_data['password'],
            cgm_device_id=yaml_data['cgm_device_id'],
            bg_meter_device_id=yaml_data['bg_meter_device_id'],
            date_format=yaml_data['date_format'],
        )

    @classmethod
    def from_defaults(self) -> 'Config':
        return Config(
            email='example@example.com',
            password='your_password_here',
            cgm_device_id='yourcgmdevicename',
            bg_meter_device_id='yourbgmetername',
            date_format='%d/%m/%Y %H:%M',
        )

    def save_to_file_path(self, yaml_fpath: Path):
        dat = {
            'email': self.email,
            'password': self.password,
            'cgm_device_id': self.cgm_device_id,
            'bg_meter_device_id': self.bg_meter_device_id,
            'date_format': self.data_format,
        }

        with open(yaml_fpath, 'w') as fp:
            yaml.dump(dat, fp)

    def has_remnants_of(self, other) -> bool:
        # compare MOST fields; date_format could be OK when set to a
        # default or duplicate value, so we don't consider it a remant
        # of another Config object
        return (
            self.email == other.email
            or self.password == other.password
            or self.cgm_device_id == other.cgm_device_id
            or self.bg_meter_device_id == other.bg_meter_device_id
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('diasend_xls_file', default='diasend.xls')
    args = parser.parse_args(sys.argv[1:])

    config_file_path = Path(os.path.expanduser("~/.diatide.cfg"))

    default_config = Config.from_defaults()
    try:
        config = Config.from_file_path(config_file_path)
        if config.has_remnants_of(default_config):
            print(f"ERROR: the default configuration has not been fully edited. Please set your own settings in {config_file_path} to continue.", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"WARNING: couldn't find file {config_file_path}. Generating a template file for you. Please edit it before continuing.", file=sys.stderr)
        default_config.save_to_file_path(config_file_path)
        sys.exit(1)

    # Extract data from xls file
    smbg,cbg = load_workbook(Path(args.diasend_xls_file), config.date_format)

    # Create tidepool instance and login
    tp = Tidepool()
    tp.login(config.email, config.password)

    # Set device ID
    tp.CBGdeviceId  = config.cgm_device_id
    tp.SMBGdeviceId = config.bg_meter_device_id

    # Select group ID
    #groups = tp.get_groups()    # Get groups which the user belongs to
    #print(f"groups is {groups!r}", file=sys.stderr)
    #group  = groups.keys()[0]   # Select first one (usually with root privilege)

    # Upload data
    tp.upload_cbg(cbg)#,group)
    tp.upload_smbg(smbg)#,group)

    tp.logout()

