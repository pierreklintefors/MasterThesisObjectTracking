import xml.etree.ElementTree as ET
import csv

tree = ET.parse("/home/pierre/Downloads/annotations.xml")
root = tree.getroot()

tracker_name = "MOSSE"
dir = f'/home/pierre/Desktop/TrackersOutput/{tracker_name}_output/'
with open(f'{dir}gt_bbox.csv', 'a' , newline='') as gt:
    columns = ['frame', 'xmin', 'ymin', 'xmax', 'ymin']
    csv_writer = csv.DictWriter(gt, fieldnames= columns)
    csv_writer.writeheader()
    for bbox in root.findall('track/box'):
        frame = bbox.get('frame')
        xmin = bbox.get('xtl')
        ymin = bbox.get('ytl')
        xmax = bbox.get('xbr')
        ymax = bbox.get('ybr')
        csv_writer.writerow({'frame': frame, 'xmin': xmin, 'ymin':ymin, 'xmax': xmax, 'ymin': ymin})
        csv_writer


    gt.close()

print(f"The extraction of ground truth bbox is finished and saved in {dir}")
