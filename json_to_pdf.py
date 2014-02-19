#!/usr/bin/env python

import glob
import json
import subprocess

from decompose import get_schedule, get_notes, split_images

# Get schedule and notes from CSV, and all existing JSON filenames
schedule = get_schedule()
notes = get_notes()
filenames = glob.glob("by_address/*/*.json")

for filename_idx,json_filename in enumerate(filenames):
    print "Processing %002d/%002d: %s" % (
      filename_idx+1, 
      len(filenames), 
      json_filename.replace("/info.json", "").replace("by_address/", "")
    )

    # Get JSON
    json_file = open(json_filename)
    json_data = json.load(json_file)
    json_file.close()

    # Find schedule and notes entries
    try:
        my_schedule = schedule['by_id'][json_data['schedule_id']]
        my_notes = notes['by_address'][json_data['address']]
    except KeyError:
        print json_data
        raise Exception("Cannot process this record: key mismatch!")

    # Write HTML
    # Image HTML fragments
    tpl_img = "<figure %s><img src='IR_%d.jpg'/><figcaption>%s</figcaption></figure>"
    all_images = json_data['images']
    image_locations = json_data['image_locations'].split("\n")

    # Best image if exists, or just all images
    json_data['html_best_image'] = tpl_img % (
      'class="bigger"',
      int(json_data.has_key('best_image') and json_data['best_image'] or all_images[0]),
      "" 
    )

    # All images
    html_images = []
    caption = ''
    for i, iiii in enumerate(all_images):
        try:
            if image_locations[i]:
                caption = "Location: %s" % image_locations[i]
        except IndexError:
            pass
        html_images.append(tpl_img % ("", int(iiii), caption))
    json_data['html_images'] = "".join(html_images)

    # Metadata
    metadata = {
      "Taken by": (json_data["who"],),
      "Date": (json_data["date"],),
      "Time": (json_data["time"],),
      "Informal notes": (json_data["problems"],json_data["recommendations"]),
    }
    metadata_keys = ("Date", "Time", "Taken by",)
    json_data['html_metadata'] = "".join(["<tr><th>%s</th><td>%s</td></tr>" % (k, "<br/>".join([dd for dd in metadata[k]])) for k in metadata_keys])

    # HTML file
    html_filename = json_filename.replace("json", "html")
    html_file = open(html_filename, 'w')
    html_file.write("""<!DOCTYPE "html"><html><head>
      <link rel="stylesheet" href="../../styles.css"/>
      <title>Thermal imaging: %(address)s</title>
    </head><body>
      <header>
        <div>Thermal imaging property report by Sustainable Witney and West Oxfordshire District Council</div>
        <img src="http://sustainablewitney.org.uk/wp-content/uploads/2012/11/SW_banner.png" width="360" />
      </header>
      <h1>%(address)s</h1>
      <section id="main">
      %(html_best_image)s
        <div id="metadata">
          <h2>Information</h2>
          <table id="metadata-items">%(html_metadata)s</table>
          <h2>Space for notes</h2>
        </div>
      </section>
      <section id="rest">
      <h2>All images</h2>
      %(html_images)s
      </section>
    </body></html>""" % json_data)
    html_file.close()

    # HTML to PDF
    subprocess.call(["wkhtmltopdf", html_filename, json_filename.replace("json", "pdf")])
