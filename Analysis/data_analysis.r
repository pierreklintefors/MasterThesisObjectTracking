#Clear workspace
rm(list=ls(all=TRUE))
graphics.off()

# Check that required packages are installed:
want = c("dplyr", "ggplot2", "gridExtra", 'ggpubr', 'extrafont')
have = want %in% rownames(installed.packages())
if ( any(!have) ) { install.packages( want[!have] ) }

library(dplyr)
#Set working directory that contains output files
setwd("~/MasterThesisObjectTracking/Analysis")

trackers_list = c('CSRT', 'GOTURN', 'KCF', 'MEDIANFLOW', 'MIL', 'MOSSE','TLD', 'yolov4deepsort')


for (tracker in 1:length(trackers_list)){
  assign(paste(trackers_list[tracker],'_data', sep = ''), 
         read.csv2(file = paste('TrackersOutput/', trackers_list[tracker], '_output/output.csv', sep = ''), sep = ',', stringsAsFactors = FALSE))
  assign(paste('gt_', trackers_list[tracker], sep = ''), 
          read.csv2(file = paste('TrackersOutput/', trackers_list[tracker], '_output/gt_bbox.csv', sep = ''), sep = ',', stringsAsFactors = FALSE))
}

#correct in roi for yolov4-deepsort
for (row in 1:nrow(yolov4deepsort_data)){ 
  if(abs(yolov4deepsort_data$Distance_x[row]) <= 30 && abs(yolov4deepsort_data$Distance_y[row]) <= 30 && abs(yolov4deepsort_data$bbox_xmax[row]) > 0){
   yolov4deepsort_data$In_roi[row] = 'True'} 
  #else{
   #  yolov4deepsort_data$In_roi='False'}
  }

correct_gt_dataset <- function(gt){
  gt$frame = gt$frame +1
  doubles = c()
  
  for (j in 2:nrow(gt)){
    if(gt$frame[j]==gt$frame[j-1] && gt$outside[j-1]==1){
      doubles = c(doubles, gt$frame[j])
    }
  }
  print(paste0("The following frames were doubles and these rows were removed:" , doubles))
  gt = gt %>% distinct(frame, .keep_all = TRUE)

 

  
  return(gt)
}
  


gt_GOTURN_corr = correct_gt_dataset(gt_GOTURN)

calculate_performance <- function(dataframe, gt){
  
  xdiff = 0
  ydiff = 0
  roi = 30
    

  dataframe$bbox_center_x = dataframe$img_center_x + dataframe$Distance_x
  dataframe$bbox_center_y = dataframe$img_center_y + dataframe$Distance_y
  dataframe$gt_object_center_xdiff = NA
  dataframe$gt_object_center_xdiff = NA
  dataframe$gt_in_roi = NA
  dataframe$object_in_frame = 0
  

  
  for (j in 1:nrow(gt)){
    xdiff = as.numeric(dataframe[gt[j,'frame'], 'bbox_center_x']) - as.numeric(gt[j,'obj_center_x'])
    ydiff = as.numeric(dataframe[gt[j,'frame'], 'bbox_center_y']) - as.numeric(gt[j,'obj_center_y'])
    dataframe[gt[j,'frame'], 'gt_object_center_xdiff'] = xdiff
    dataframe[gt[j,'frame'], 'gt_object_center_ydiff'] = ydiff
    
    if(gt[j, 'outside']==0){dataframe[gt[j,'frame'], 'object_in_frame'] = 1}
    
    if (abs(xdiff)+abs(dataframe$Distance_x) < roi && abs(ydiff) + abs(dataframe$Distance_y) < roi ){dataframe[gt[j,'frame'], 'gt_in_roi'] = TRUE}
    else {dataframe[gt[j,'frame'], 'gt_in_roi'] = FALSE}
  }
  
  
  


  return(dataframe)
}

performance_table <- function(df_list){
  per_mat = matrix(nrow = length(df_list) , ncol = 9 )
  colnames(per_mat) = c('fps', 'mean GT obj center xdiff', 'mean GT obj center ydiff', 
                        'prop frames in tracked ROI', 'prop frames in GT ROI'
                        , 'tracking loss', 'recovered tracking', 'RT/TL', 'prop frames object visible')
  rownames(per_mat)= trackers_list
  for (df in 1:length(df_list)){
    data = get(df_list[df])
    last_row = nrow(data)
    fps = with(data, as.numeric(Frame[last_row])/as.numeric(Time[last_row]))
    xdiff = with (data, mean(abs(gt_object_center_xdiff), na.rm = TRUE ))
    ydiff = with (data, mean(abs(gt_object_center_ydiff), na.rm = TRUE ))
    prop_track_roi = (sum(data$In_roi=='True', na.rm = TRUE))/last_row
    prop_gt_roi = (sum(data$gt_in_roi=='True', na.rm = TRUE))/last_row
    prop_obj_in_frame = (sum(data$object_in_frame))/last_row
    
    num_track_loss = 0
    num_track_rec = 0
    for(row in 2:nrow(data)){
      if(data$Tracking_success[row]=='False' && data$Tracking_success[row-1]=='True' ){num_track_loss = num_track_loss +1}
      if(data$Tracking_success[row]=='True' && data$Tracking_success[row-1]=='False'){num_track_rec = num_track_rec +1}
      }
    
    per_mat[df,'fps'] = round(fps, 2)
    per_mat[df,'mean GT obj center xdiff'] = round(xdiff, 2)
    per_mat[df,'mean GT obj center ydiff'] = round(ydiff, 2)
    per_mat[df, 'prop frames in tracked ROI'] = round(prop_track_roi,2 ) 
    per_mat[df,'prop frames in GT ROI'] = round(prop_gt_roi, 2)
    per_mat[df,'tracking loss'] = num_track_loss
    per_mat[df,'recovered tracking'] = num_track_rec
    if(num_track_loss == 0){per_mat[df,'RT/TL'] = NA}
    else{per_mat[df,'RT/TL'] = round(num_track_rec/num_track_loss, 2) }
    
    per_mat[df,'prop frames object visible'] = round(prop_obj_in_frame, 2)
   
    
  }
  return(per_mat)
}




df_name_list = c("CSRT_data", "GOTURN_data", "KCF_data", "MEDIANFLOW_data", "MIL_data", "MOSSE_data", "TLD_data", "yolov4deepsort_data")
gt_df_list = c("gt_CSRT", "gt_GOTURN", "gt_KCF", "gt_MEDIANFLOW", "gt_MIL", "gt_MOSSE", "gt_TLD", "gt_yolov4deepsort")

#Lopping the data frames through function that corrects ground truth data frames
for(df in 1:length(gt_df_list)) {assign(paste(gt_df_list[df], '_corr', sep = ''), correct_gt_dataset(get(gt_df_list[df])))}


#Adding performance measures to the data frames
for(df in 1:length(df_name_list)) {
  assign(paste0(df_name_list[df]),calculate_performance(dataframe = get(df_name_list[df]), gt =  get(paste0(gt_df_list[df],'_corr'))))
  
}


performance_matrix = performance_table(df_name_list)  

write.table(performance_matrix, file = 'performanceTable.txt', sep = ' & ', col.names = TRUE, row.names = TRUE, quote = FALSE)


library(ggplot2)

library(extrafont)
loadfonts(device = "win")




plot_trajectories <- function (df_list, tracker_list){
  plots = list()

  for (df in 1:length(df_list)){
    data = get(df_list[df])
    tracker_name = tracker_list[df]
    xlab = paste0(tracker_name)
    if (paste0(tracker_name)=='yolov4deepsort'){xlab = "YOLOv4-DeepSORT"}
    plot = ggplot(data,aes(Distance_x, Distance_y))+
      geom_path(mapping = aes(as.numeric(Distance_x + gt_object_center_xdiff), as.numeric(Distance_y + gt_object_center_ydiff)), color= 'green3')+
      geom_path(color = 'blue')+
      xlab(xlab)+
      ylab("")+
      xlim(-500,500)+
      ylim(-400,400)+
      geom_hline(yintercept = 0,color = 'black') +
      geom_vline(xintercept = 0,color = 'black') 

      plots [[df]] = assign(paste0(tracker_name, '_plot') , plot + theme_bw() + theme(text=element_text(size=12,  family="serif")))
  }
  
  ggpubr::ggarrange(plotlist = plots, ncol = 2, nrow = 4, align = 'hv')
 
}

plot_trajectories(df_name_list, trackers_list)


gt_corr_df_list = c("gt_CSRT_corr", "gt_GOTURN_corr", "gt_KCF_corr", "gt_MEDIANFLOW_corr", "gt_MIL_corr", "gt_MOSSE_corr", "gt_TLD_corr", "gt_yolov4deepsort_corr")

intersection_over_union <- function (df_list, gt_list){
  
  average_ious = matrix(nrow = length(df_list),  ncol = 1)
  rownames(average_ious) = df_list
  
  for (df in 1:length(df_list)){
    pred_data = get(df_list[df])
    gt_data= get(gt_list[df])
    
    gt_boxes = subset(gt_data, select = c('frame', 'xmin', 'ymin', 'xmax', 'ymax')) 
    
    pred_boxes = subset(pred_data, select = c('Frame','bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax'))
    
    iou_list = c()
    
    for (i in 1:nrow(gt_boxes)){
      boxA = as.numeric(gt_boxes[gt_boxes$frame == i, 2:5])
      boxB = round(as.numeric(pred_boxes[pred_boxes$Frame == i, 2:5]), 0)
      
      xA = max(boxA[1], boxB[1])
      yA = max(boxA[2], boxB[2])
      xB = min(boxA[3], boxB[3])
      yB = min(boxA[4], boxB[4])
      # compute the area of intersection rectangle
      interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
      # compute the area of both the prediction and ground-truth
      # rectangles
      boxAArea = (boxA[3] - boxA[1] + 1) * (boxA[4] - boxA[2] + 1)
      boxBArea = (boxB[3] - boxB[1] + 1) * (boxB[4] - boxB[2] + 1)
      # compute the intersection over union by taking the intersection
      # area and dividing it by the sum of prediction + ground-truth
      # areas - the interesection area
      iou = interArea / (boxAArea + boxBArea - interArea)
      # return the intersection over union value
      
      iou_list = c(iou_list , iou)
    }
    
    average_iou = sum(iou_list, na.rm = TRUE) / nrow(pred_boxes)
    
    average_ious[df,1] = average_iou
  }
  
  return(average_ious)
}

average_ious = intersection_over_union(df_list = df_name_list, gt_list = gt_corr_df_list)  

