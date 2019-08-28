import csv
import datetime
import lxml.etree as ET
import math
import re
import sys

NAME = 'Dave Cunningham'
QUALIFICATION = 'OW'
TIME_PATTERN = re.compile(r'([0-9]+):([0-9]+) min')
DISTANCE_PATTERN = re.compile(r'([0-9.]+) m')
VOLUME_PATTERN = re.compile(r'([0-9.]+) l')
PRESSURE_PATTERN = re.compile(r'([0-9.]+) bar')
BSAC_PO2 = 1.4

def MaxDepth(pp, nox):
    return (pp / nox - 1) * 10
    
AIR_MOD = MaxDepth(BSAC_PO2, 0.21)

if len(sys.argv) not in (2, 3):
    sys.stderr.write('Usage: python %s <from> [ <to> ]\n')
    sys.stderr.write('<from> and <to> are dates of the form 2019-01-31\n')
    sys.stderr.write('If <to> is omitted it defaults to the current date.\n')
    sys.exit(1)

def PrintDate(dt):
    return dt.strftime("%Y-%m-%d")

def ParseDate(text):
    return datetime.datetime.strptime(text, '%Y-%m-%d')

def ParseDateTime(text):
    return datetime.datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')

def PrintTime(dt):
    return dt.strftime("%H:%M:%S")

def ParseTime(text):
    return datetime.datetime.strptime(text, '%H:%M:%S')

def PrintDuration(delta):
    return '%02d:%02d' % (int(delta.seconds / 60), delta.seconds % 60)

def ParseDuration(text):
    match = TIME_PATTERN.search(text)
    mins, secs = match.groups()
    return datetime.timedelta(minutes=int(mins), seconds=int(secs))

def ParseDistance(text):
    match = DISTANCE_PATTERN.search(text)
    (metres,) = match.groups()
    return float(metres)

def ParseVolume(text):
    match = VOLUME_PATTERN.search(text)
    (litres,) = match.groups()
    return float(litres)

def ParsePressure(text):
    match = PRESSURE_PATTERN.search(text)
    (bar,) = match.groups()
    return float(bar)

from_date = ParseDate(sys.argv[1])
if len(sys.argv) >= 3:
    to_date = ParseDate(sys.argv[2])
else:
    to_date = datetime.datetime.today()


tree = ET.parse('dive_log.xml')

dive_site_by_id = {}
sites = tree.getroot().find('divesites')
for site in sites:
    dive_site_by_id[site.get('uuid')] = site

def DiveSiteCountry(site):
    for geo in site.findall('geo'):
        if geo.get('cat') == '2' and geo.get('origin') == '2':
            return geo.get('value')
    return None

def GetDiveStartDate(dive):
    return ParseDate(dive.get('date'))


with open('dive_log.csv', mode='w') as employee_file:
    writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    dives = tree.getroot().find('dives')
    for dive in dives:
        tags = [tag.strip().upper() for tag in dive.get('tags', '').split(',')]
        if 'BSAC' in tags:
            continue
        date = ParseDate(dive.get('date'))
        start_time = ParseTime(dive.get('time')) 
        if date < from_date or date > to_date:
            continue
        dive_site = dive_site_by_id[dive.get('divesiteid')]
        site_name = dive_site.get('name')
        country = DiveSiteCountry(dive_site)
        duration = ParseDuration(dive.get('duration'))
        stop_time = start_time + duration
        depth_max = None
        for divecomputer in dive.findall('divecomputer'):
            for depth in divecomputer.findall('depth'):
                depth_max = ParseDistance(depth.get('max'))
                break
            break
        for cylinder in dive.findall('cylinder'):
            start_text = cylinder.get('start') or cylinder.get('workpressure')
            end_text = ''
            if cylinder.get('end'):
                end_text = str(ParsePressure(cylinder.get('end')))
            writer.writerow([
                PrintDate(date) + ' @ ' + site_name + ' ' + country,
                NAME,
                QUALIFICATION,
                ParseVolume(cylinder.get('size')),
                ParsePressure(start_text),
                0.21,
                math.ceil(AIR_MOD),
                '',
                end_text,
                '',
                '',
                PrintTime(start_time),
                PrintTime(stop_time),
                math.ceil(depth_max),
                '',
                '',
                '',
                '',
                3,
                '',
                PrintDuration(duration),
                ', '.join(tags)
            ]) 
