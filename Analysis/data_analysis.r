#Clear workspace
rm(list=ls(all=TRUE))
graphics.off()

# Check that required packages are installed:
want = c("dplyr", "ggplot2", "gridExtra", 'ggpubr')
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
  
  #check after doubles
  for (j in 2:nrow(gt)){
    if(gt$frame[j]==gt$frame[j-1] && gt$outside[j-1]==1){doubles = gt[j, 'outside']=1}
  }

  
  gt = distinct(gt)
  
  return(gt)
}

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

write.table(performance_matrix, file = 'performanceTable.txt', sep = ' & ', col.names = TRUE, row.names = TRUE)


library(ggplot2)

plot_trajectories <- function (df_list, tracker_list){
  plots = list()
  for (df in 1:length(df_list)){
    data = get(df_list[df])
    tracker_name = tracker_list[df]
    plot = ggplot(data,aes(Distance_x, Distance_y))+
      geom_path(mapping = aes(as.numeric(Distance_x + gt_object_center_xdiff), as.numeric(Distance_y + gt_object_center_ydiff)), color= 'green')+
      geom_path(color = 'blue')+
      xlab(paste0(tracker_name))+
      ylab("")+
      geom_hline(yintercept = 0,color = 'black') +
      geom_vline(xintercept = 0,color = 'black') 
      coord_fixed(xlim = 500, ylim = 800)
      plots [[df]] = assign(paste0(tracker_name, '_plot') , plot + theme_bw())
  }
  
  ggpubr::ggarrange(plotlist = plots, ncol = 2, nrow = 4, align = 'hv')
 
}

plot_trajectories(df_name_list, trackers_list)


