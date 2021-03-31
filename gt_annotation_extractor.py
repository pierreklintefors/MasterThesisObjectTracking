import xml.etree.ElementTree as ET
import csv



tracker_name = "yolov4-deepsort"
dir = f'/home/pierre/Desktop/TrackersOutput/{tracker_name}_output/'

tree = ET.parse(f'{dir}annotations.xml')
root = tree.getroot()
with open(f'{dir}gt_bbox.csv', 'w' , newline='') as gt:
    columns = ['frame', 'occluded', 'outside', 'xmin', 'ymin', 'xmax', 'ymax', 'obj_center_x', 'obj_center_y']
    csv_writer = csv.DictWriter(gt, fieldnames= columns)
    csv_writer.writeheader()
    for bbox in root.findall('track/box'):
        frame = bbox.get('frame')
        xmin = bbox.get('xtl')
        ymin = bbox.get('ytl')
        xmax = bbox.get('xbr')
        ymax = bbox.get('ybr')
        occluded = bbox.get('occluded')
        outside = bbox.get('outside')
        obj_center_x = round(float(xmin) + ((float(xmax) - float(xmin))/2), 2)
        obj_center_y = round(float(ymin) + ((float(ymax) - float(ymin))/2), 2)
        csv_writer.writerow({'frame': frame, 'occluded': occluded, 'outside': outside, 'xmin': xmin, 'ymin':ymin,
                             'xmax': xmax, 'ymax': ymax, 'obj_center_x': obj_center_x, 'obj_center_y': obj_center_y})



    gt.close()

print(f"The extraction of ground truth bbox for {tracker_name} tracker is finished and saved in {dir}")
