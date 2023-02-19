# diatide

Uploads Diasend.com Excel exports to Tidepool.org

## Full Description

Over the past number of years I have accumalated a number of different blood testing meters, and each one requires it own software to download results. Then Diasend.com (used by various hospitals) have a portal that includes and Uploader including driver for most Blood Glucose Meters, which makes it extremely useful however the graphs and analysis tools (in my personal opinion) could use some improvement. At this point I came across an Opensource project Tidepool.org which among other things have good analytic and graph capabilities, but currently limited to only two specific BGM's. Therefore this script is to bridge the gap between the number of devices that Diasend can communicate with, and the analytical capabilities of Tidepool.

I hope you find this as useful as I have.

Authors:
- github.com/j666gak and tk2@Freelancer.com who worked on the original project code
- github.com/lee-b who modernized it with a port from python 2.x to python 3.10 and poetry, added command line arguments, config files, improved error handling and robustness, etc.

## Configuration

When you run this for the first time, it will generate a config file, and tell you to edit that file.  Open the file in a text editor like notepad or Visual Studio Code, and
set your own values. The `email` and `password` fields are for Tidepool, of course. The `date_format` field is according to the python strptime format codes, but generally you'll just want to move the %d (the day) and the %m (the month) depdending on whether you're in the US or elsewhere, and what way dates are formatted in your Excel file.  If you don't do this, you'll get errors about unrecognised date formats, and the records with the incorrect date formats won't be uploaded, but unfortunately we can't detect the correct day/month format for dates like 12/12, so
those would be uploaded incorrectly if you failed to follow these instructions.  However, re-running with the correct format set will probably mostly correct it, depending on how many readings you have for each day.

## Sucessfuly Tested On
O/S = Windows 10
Python = 3.10
Diasend export format, as of 2023-03-19

## Terms & Conditions

All use is at your own risk. No warranty is expressed or implied. For personal use ONLY (per j666gak's original license).
