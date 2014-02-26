#!/usr/bin/env python

import csv
import json
import re
import os
import shutil

def get_schedule():
    """Get schedule for IDs"""
    data = {'by_address': {}, 'by_id': {}}
    with open('schedule.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in [row for row in csvreader if row[2] not in ('Name',)]:
            data['by_address'][row[1]] = row[:7]
            data['by_id'][row[0]] = row[:7]
    return data

def get_notes():
    """Get notes for image filenames"""
    notes = {'by_address': {}}
    previous_date = ''
    previous_who = ''
    with open('notes.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in [row for row in csvreader if row[3] != 'Property']:
            # Complete with previouses if we don't have date/who
            if row[0]: previous_date = row[0]
            if row[1]: previous_who = row[1]
            row[0] = previous_date
            row[1] = previous_who
            # Calculate images
            row[6] = split_images(row[6])
            # Substitute in... but could we
            try:
                for k in (5,6,7,8):
                    if row[k]:
                        try:
                            notes['by_address'][row[3]][k] += "\n" + row[0] + ': ' + row[k]
                        except TypeError:
                            notes['by_address'][row[3]][k] += row[k]
            except KeyError:
                notes['by_address'][row[3]] = row

    return notes

def split_images(images_field):
    """Return an array of image IDs, even with 'to' or 'and' in there"""
    images = re.split('\W+', images_field.strip())
    if len(images) == 3 and images[1] in ('to', 'and'):
        images = range(int(images[0]), int(images[2])+1)
    return images

def decompose_file_for(address, info, data):
    """Set up an address subfolder, get all images and save JSON"""
    # Make folder
    folder = 'by_address/%s' % re.sub('[^0-9a-zA-z]+', '_', address)
    if not os.path.exists(folder):
        os.mkdir(folder)

    for i in info[6]:
        try:
            fn = 'all_images/IR_%d.jpg' % int(i)
            to_fn = '%s/IR_%d.jpg' % (folder, int(i))
            if not os.path.exists(fn):
                print "Cannot find " + fn
            elif not os.path.exists(to_fn):
                shutil.copyfile(fn, to_fn)
            
        except ValueError, e:
            if info[3] == '26 Beech Road':
                print "Problem with 26 Beech Road: no images"
            elif info[1] == 'Commas!':
		print "Still awaiting rest of 2013"
            elif info[0] == "Date":
                return
            else:
                print info
                raise e

    # Now write JSON
    json_file = open('%s/info.json' % folder, 'w')

    # Data with friendly keys
    data_to_dump = {
      'date': info[0],
      'who': info[1],
      'time': info[2],
      'address': info[3],
      'problems': info[4],
      'recommendations': info[5],
      'images': info[6],
      'image_locations': info[7],
      'conditions': info[8],
    }
    # Can we get the info from the schedule into it?
    schedule = ('NO_ID', 'NO_ADDRESS', 'NO_NAME', 'NO_CONTACT')
    try:
        schedule = data['by_address'][data_to_dump['address']]
    except KeyError:
        try:
            schedule = data['by_address'][re.sub('Ave', 'Avenue', data_to_dump['address'])]
        except KeyError:
            print "No schedule found for '" + data_to_dump['address'] + "'"
    # Only pass in the ID; avoid personal data spreading around
    data_to_dump['schedule_id'] = schedule[0]
    # Amendment - we put "best image" on the wrong sheet, so add that too
    try:
        data_to_dump['best_image'] = "%d" % int(schedule[6])
    # Most of these are wrong for 2014
    except ValueError, e:
        pass
    # And some rows indicate we're still awaiting 2013
    except IndexError, e:
        if schedule[0] == 'NO_ID' and data_to_dump['who'] not in ('Commas!', 'Abandon!'):
            print data_to_dump
            print info
            raise e

    json_file.write(json.dumps(data_to_dump, sort_keys=True,
               indent=4, separators=(',', ': ')))
    json_file.close()

# Now decompose and process files
if __name__ == "__main__":
    notes = get_notes()
    data = get_schedule()
    #print data['by_id']['B1']
    #exitzorz
    for (address, info) in notes['by_address'].items():
        decompose_file_for(address, info, data)
