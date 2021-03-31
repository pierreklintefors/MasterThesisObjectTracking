#Clear workspace
rm(list=ls(all=TRUE))
graphics.off()

# Check that required packages are installed:
#want = c("")
#have = want %in% rownames(installed.packages())
#if ( any(!have) ) { install.packages( want[!have] ) }

#Set working directory that contains output files
setwd("~/MasterThesisObjectTracking/Analysis")

trackers_list = c('CSRT', 'GOTURN', 'KCF', 'MEDIANFLOW', 'MIL', 'MOSSE','TLD', 'yolov4-deepsort')

for (tracker in 1:length(trackers_list)){
  assign(paste(trackers_list[tracker],'_data', sep = ''), 
         read.csv2(file = paste('TrackersOutput/', trackers_list[tracker], '_output/output.csv', sep = ''), sep = ','))
  assign(paste('gt_', trackers_list[tracker], sep = ''), 
          read.csv2(file = paste('TrackersOutput/', trackers_list[tracker], '_output/gt_bbox.csv', sep = ''), sep = ','))
}


calculate_performance <- function(dataframe, gt){
  
  in_roi = c()
  xdiff = c()
  ydiff = c()
    
  for (i in 2:nrow(gt)){
    if(gt$frame[i]==gt$frame[i-1] && gt$outside[i-1]==1){gt = gt[-i,]}
  }
  
  dataframe$bbox_center_x = dataframe$img_center_x + dataframe$Distance_x
  dataframe$bbox_center_y = dataframe$img_center_y + dataframe$Distance_y
  dataframe$gt_object_center_xdiff = NA
  dataframe$gt_object_center_xdiff = NA
  

  
  for (j in 2:nrow(gt)){
    xdiff = as.numeric(dataframe[gt[j,'frame'], 'bbox_center_x']) - as.numeric(gt[j,'obj_center_x'])
    ydiff = as.numeric(dataframe[gt[j,'frame'], 'bbox_center_y']) - as.numeric(gt[j,'obj_center_y'])
    dataframe[gt[j,'frame'], 'gt_object_center_xdiff'] = xdiff
  }
  
  
  
  #dataframe$gt_object_center_xdiff = xdiff
  #dataframe$gt_object_center_ydiff = ydiff

  return(dataframe)
}

CSRT_data = calculate_performance(CSRT_data, gt_CSRT)


  

