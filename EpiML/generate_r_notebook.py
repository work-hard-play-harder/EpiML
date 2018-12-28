import os
import nbformat as nbf

nb = nbf.v4.new_notebook()

# set R kernel
nb.metadata = {
    "kernelspec": {
        "display_name": "R",
        "language": "R",
        "name": "ir"
    },
    "language_info": {
        "codemirror_mode": "r",
        "file_extension": ".r",
        "mimetype": "text/x-r-source",
        "name": "R",
        "pygments_lexer": "r",
        "version": "3.5.0"
    }
}

title = '''\
# Epistatic Analysis Notebook | ShiLab
---'''
introduction = '''## This is a Jupyter Notebook based on R kernel.'''


def generate_EBEN_notebook(job_dir, input_x, input_y):
    load_library = '''\
# load library
library('EBEN')
library('r2d3')
quantile_normalisation <- function(df){
  df_rank <- apply(df,2,rank,ties.method="min")
  df_sorted <- data.frame(apply(df, 2, sort))
  df_mean <- apply(df_sorted, 1, mean)
  
  index_to_mean <- function(my_index, my_mean){
    return(my_mean[my_index])
  }
  
  df_final <- apply(df_rank, 2, index_to_mean, my_mean=df_mean)
  rownames(df_final) <- rownames(df)
  return(df_final)
}'''

    load_params = '''\
nFolds <- 5
pvalue <- 0.05
seed <- 28213
set.seed(seed)
datatype <- 'discrete'  # discrete or continuous'''

    load_data = '''\
# load data
workspace <- './'
x_filename <- '{0}'
y_filename <- '{1}'

x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names=FALSE,
  row.names = 1
)
sprintf('x size: (%d, %d)', nrow(x), ncol(x))
x <- as.matrix(x)

y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  row.names = 1
)
sprintf('y size: (%d, %d)', nrow(y), ncol(y))
y <- as.matrix(y)'''.format(input_x, input_y)

    preprocessing = '''\
# preprocessing depending on data type
x_preprocessed <- NULL
y_preprocessed <- NULL
# for x preprocess
cat('Filter data with missing data', '\n')
x_filtered <- t(na.omit(t(x)))
if (datatype == 'discrete') {
  # discrete data is categorical, no normlization
  x_preprocessed <- x_filtered
} else if (datatype == 'continuous') {
  cat('Quantile normalization', '\n')
  x_preprocessed <- quantile_normalisation(x_filtered)
}
# for y preprocess
y_preprocessed <- scale(y)'''

    estimate_main_effect = '''\
# Main effect estimated
cv_main = EBelasticNet.GaussianCV(x_preprocessed, y_preprocessed, nFolds = nFolds, Epis = "no")
blup_main = EBelasticNet.Gaussian(
  x_preprocessed,
  y_preprocessed,
  lambda = cv_main$Lambda_optimal,
  alpha = cv_main$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
main <- as.matrix(blup_main$weight)
sig_main <- main[which(main[, 6] <= pvalue),, drop = F]'''

    substract_main_effect = '''\
# Substract the main effect
index_main <- sig_main[, 1]
effect_main <- sig_main[, 3]
subtracted_y <- y_preprocessed - x_preprocessed[, index_main, drop=F] %*% effect_main
subtracted_y <- scale(subtracted_y)'''

    estimate_epis_effect = '''\
# Epistatic effect estimated. This step may need a long time.
cv_epis <- EBelasticNet.GaussianCV(x_preprocessed, subtracted_y, nFolds = nFolds, Epis = "yes")
blup_epis <- EBelasticNet.Gaussian(
  x_preprocessed,
  subtracted_y,
  lambda =  cv_epis$Lambda_optimal,
  alpha = cv_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
epi <- as.matrix(blup_epis$weight)
sig_epi <- epi[which(epi[, 6] <= pvalue),, drop = F]'''

    final_run = '''\
# Final run
full_id <- rbind(sig_main[, 1:2], sig_epi[, 1:2])

output_main <- matrix("NA", 0, 5)
colnames(output_main) <- c('feature', 'coefficient', 'posterior variance', 't-value', 'p-value')
output_epi <- matrix("NA", 0, 6)
colnames(output_epi) <- c('feature1', 'feature2', 'coefficient', 'posterior variance', 't-value', 'p-value')
# at least three 
if (!is.null(full_id) && nrow(full_id)>2)
{
  full_matrix <- NULL
  for (i in 1:nrow(full_id)) {
    if (full_id[i, 1] == full_id[i, 2]) {
      full_matrix <- cbind(full_matrix, x_preprocessed[, full_id[i, 1], drop=F])
    }
    if (full_id[i, 1] != full_id[i, 2]) {
      col <- x_preprocessed[, full_id[i, 1], drop=F] * x_preprocessed[, full_id[i, 2], drop=F]
      full_matrix <- cbind(full_matrix, col)
    }
  }
  if (datatype == 'continuous') {
    full_matrix <- quantile_normalisation(full_matrix)
  }
  #regression
  cv_full <- EBelasticNet.GaussianCV(full_matrix, y_preprocessed, nFolds = nFolds, Epis = "no")
  blup_full <- EBelasticNet.Gaussian(
    full_matrix,
    y_preprocessed,
    lambda =  cv_full$Lambda_optimal,
    alpha = cv_full$Alpha_optimal,
    Epis = "no",
    verbose = 0
  )
  full <- as.matrix(blup_full$weight)
  sig_full <- full[which(full[, 6] <= pvalue),, drop = F]
  sig_full[, 1:2] <- full_id[sig_full[, 1], 1:2]
  
  output_main <- matrix("NA", 0, 5)
  colnames(output_main) <- c('feature', 'coefficient', 'posterior variance', 't-value', 'p-value')
  output_epi <- matrix("NA", 0, 6)
  colnames(output_epi) <- c('feature1', 'feature2', 'coefficient', 'posterior variance', 't-value', 'p-value')
  for (i in 1:nrow(sig_full)) {
    if (sig_full[i, 1] == sig_full[i, 2]) {
      output_main <- rbind(output_main, c(colnames(x_preprocessed)[sig_full[i, 1]], sig_full[i, 3:6]))
    }
    if (sig_full[i, 1] != sig_full[i, 2]) {
      output_epi <- rbind(output_epi, 
                          c(colnames(x_preprocessed)[sig_full[i, 1]], 
                            colnames(x_preprocessed)[sig_full[i, 2]],
                            sig_full[i, 3:6])
                          )
    }
  }
}'''

    show_main_result = '''output_main'''

    show_epis_result = '''output_epi'''

    vis_circle_network = '''\
# generate json
# get all epsitasis nodes (unique)
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
json_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  f2 <- matrix(output_epi[output_epi[, 1] == f1, ],ncol=6)
  f2[,2]<-sprintf('"epis.%s"', f2[,2])
  element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
  json_str <- c(json_str,element)
}
json_str<-sprintf('[%s]',paste(json_str, collapse=',' ))
# circle network
r2d3(data=json_str, script = "../static/js/vis_CN.js", css = "../static/css/vis_CN.css")'''

    vis_adjacent_matrix = '''\
# for adjacent matrix
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
nodes_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  element<- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
  nodes_str <- c(nodes_str,element)
}
nodes_str<-sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
link_str<-NULL
for(i in 1:nrow(output_epi)){
  source_index<- match(output_epi[i,1], epsi_nodes)
  target_index<- match(output_epi[i,2], epsi_nodes)
  coff<-as.numeric(output_epi[i,3])
  element<-sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
  link_str <- c(link_str,element)
}

link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
am_json<-sprintf('{%s,%s}',nodes_str,link_str)
write(am_json,'am.json')
r2d3( d3_version = 4, script = "../static/js/vis_AM.js", css = "../static/css/vis_AM.css", dependencies = "../static/js/d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(preprocessing),
                   nbf.v4.new_code_cell(estimate_main_effect),
                   nbf.v4.new_code_cell(substract_main_effect),
                   nbf.v4.new_code_cell(estimate_epis_effect),
                   nbf.v4.new_code_cell(final_run),
                   nbf.v4.new_code_cell(show_main_result),
                   nbf.v4.new_code_cell(show_epis_result),
                   nbf.v4.new_code_cell(vis_circle_network),
                   nbf.v4.new_code_cell(vis_adjacent_matrix)
                   ]

    EBEN_nb = os.path.join(job_dir, 'EBEN_r_notebook.ipynb')
    with open(EBEN_nb, 'w') as f:
        nbf.write(nb, f)


def generate_LASSO_notebook(job_dir, input_x, input_y):
    load_library = '''\
# load library
library("fdrtool")
library("Matrix")
library("foreach")
library("glmnet")
library('r2d3')
quantile_normalisation <- function(df){
  df_rank <- apply(df,2,rank,ties.method="min")
  df_sorted <- data.frame(apply(df, 2, sort))
  df_mean <- apply(df_sorted, 1, mean)
  
  index_to_mean <- function(my_index, my_mean){
    return(my_mean[my_index])
  }
  
  df_final <- apply(df_rank, 2, index_to_mean, my_mean=df_mean)
  rownames(df_final) <- rownames(df)
  return(df_final)
}'''

    load_params = '''\
# load parameters
nFolds <- 5
seed <- 28213
set.seed(seed)
datatype <- 'discrete'  # discrete or continuous'''

    load_data = '''\
# load data
workspace <- './'
x_filename <- '{0}'
y_filename <- '{1}'
x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('x size: (%d, %d)', nrow(x), ncol(x))
x <- as.matrix(x)

y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  row.names = 1
)
sprintf('y size: (%d, %d)', nrow(y), ncol(y))
y <- as.matrix(y)'''.format(input_x, input_y)

    preprocessing = '''\
# preprocessing depending on data type
x_preprocessed <- NULL
y_preprocessed <- NULL
# for x preprocess
# Filter data with missing data
x_filtered <- t(na.omit(t(x)))
if (datatype == 'discrete') {
  # discrete data is categorical, no normlization
  x_preprocessed <- x_filtered
} else if (datatype == 'continuous') {
  # Quantile normalization
  x_preprocessed <- quantile_normalisation(x_filtered)
}
# for y preprocess
y_preprocessed <- scale(y)
rm(x, y, x_filtered)'''

    estimate_main_effect = '''\
# Main effect estimated
cv_main <- cv.glmnet(x_preprocessed, y_preprocessed, nfolds=nFolds)
blup_main <- glmnet(
  x_preprocessed,
  y_preprocessed,
  alpha = 1,
  family = c("gaussian"),
  lambda = cv_main$lambda.min,
  intercept = TRUE
)
main <- as.matrix(blup_main$beta)
sig_main <- main[which(main != 0), 1, drop = F]'''

    substract_main_effect = '''\
# Subtract the main effect
index_main <- rownames(sig_main)
subtracted_y <- y_preprocessed - x_preprocessed[, index_main, drop=F] %*% sig_main
subtracted_y <- scale(subtracted_y)'''

    estimate_epis_effect = '''\
# Epistatic effect estimated
# construct epistatic matrix, pairwise of each column 
epi_matrix <- NULL
for(k in 1:(ncol(x_preprocessed)-1)){
  single <- x_preprocessed[, k]
  behind <- x_preprocessed[, (k + 1):ncol(x_preprocessed)]
  # single multiply each column of behind, use as.matrix to avoid pairwise is list when k = ncol(x_preprocessed)-1
  pairwise <- as.matrix(single * behind) 
  colnames(pairwise) <- paste(colnames(x_preprocessed)[k], 
                              colnames(x_preprocessed)[(k + 1):ncol(x_preprocessed)],
                              sep = "*")
  
  epi_matrix <- cbind(epi_matrix, pairwise)
}
if (datatype == 'continuous') {
  epi_matrix <- quantile_normalisation(epi_matrix)
}
# regression using lasso
cv_epi <- cv.glmnet(epi_matrix, subtracted_y, nfolds=nFolds);
blup_epi <- glmnet(
  epi_matrix,
  subtracted_y,
  alpha = 1,
  family = c("gaussian"),
  lambda = cv_epi$lambda.min,
  intercept = TRUE
)
epi <- as.matrix(blup_epi$beta)
sig_epi <- epi[which(epi != 0), 1, drop = F]'''

    final_run = '''\
# Final run to re-estimate coefficient
# construct new matrix from significant main and epistatic variants
full_matrix <- cbind(x_preprocessed[, rownames(sig_main), drop=F],epi_matrix[,rownames(sig_epi), drop=F])

output_main <- matrix("NA", 0, 2)
colnames(output_main) <- c("feature", "coefficient")
output_epi <- matrix("NA", 0, 3)
colnames(output_epi) <- c("feature1", "feature2", "coefficient")
# at least two columns
if (!is.null(full_matrix) && ncol(full_matrix)>2){
  if (datatype == 'continuous') {
    full_matrix <- quantile_normalisation(full_matrix)
  }
  # regression 
  cv_full <- cv.glmnet(full_matrix, y_preprocessed, nfolds=nFolds)
  blup_full <- glmnet(
    full_matrix,
    y_preprocessed,
    alpha = 1,
    family = c("gaussian"),
    lambda = cv_full$lambda.min,
    intercept = TRUE
  )
  full <- as.matrix(blup_full$beta)
  sig_full <- full[which(full != 0), 1, drop = F]
  
  # Generate result tables
  # for main effect
  main_index <- setdiff(1:nrow(sig_full), grep("\\\*", rownames(sig_full)))
  if(length(main_index)!=0){
    output_main <- matrix("NA", length(main_index), 2)
    output_main[, 1] <- matrix(rownames(sig_full), ncol = 1)[main_index, , drop = F]
    output_main[, 2] <- sig_full[main_index, 1, drop = F]
    colnames(output_main) <- c("feature", "coefficient")
  }
  # for epistasic effect
  epi_index <- grep("\\\*", rownames(sig_full))
  if(length(epi_index)!=0){
    output_epi <- matrix("NA", length(epi_index), 3)
    epi_ID <- matrix(rownames(sig_full), ncol = 1)[epi_index, , drop = F]
    output_epi[, 1:2] <- matrix(unlist(strsplit(epi_ID, "\\\*")), ncol = 2, byrow=T)
    output_epi[, 3] <- sig_full[epi_index, 1, drop = F]
    colnames(output_epi) <- c("feature1", "feature2", "coefficient")
  }
}'''

    show_main_effect = '''output_main'''

    show_epis_effect = '''output_epi'''

    # for data visualization
    vis_circle_network = '''\
# generate json
# get all epsitasis nodes (unique)
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
json_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  f2 <- matrix(output_epi[output_epi[, 1] == f1, ], ncol=6)
  f2[,2] <- sprintf('"epis.%s"', f2[,2])
  element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
  json_str <- c(json_str,element)
}
json_str <- sprintf('[%s]',paste(json_str, collapse=',' ))
# circle network
r2d3(data=json_str, script = "../static/js/vis_CN.js", css = "../static/css/vis_CN.css")'''

    vis_adjacent_matrix = '''\
# For adjacent matrix
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
nodes_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  element<- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
  nodes_str <- c(nodes_str,element)
}
nodes_str<-sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
link_str<-NULL
for(i in 1:nrow(output_epi)){
  source_index<- match(output_epi[i,1], epsi_nodes)
  target_index<- match(output_epi[i,2], epsi_nodes)
  coff<-as.numeric(output_epi[i,3])
  element<-sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
  link_str <- c(link_str,element)
}

link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
am_json<-sprintf('{%s,%s}',nodes_str,link_str)
write(am_json,'am.json')
r2d3( d3_version = 4, script = "../static/js/vis_AM.js", css = "../static/css/vis_AM.css", dependencies = "../static/js/d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(preprocessing),
                   nbf.v4.new_code_cell(estimate_main_effect),
                   nbf.v4.new_code_cell(substract_main_effect),
                   nbf.v4.new_code_cell(estimate_epis_effect),
                   nbf.v4.new_code_cell(final_run),
                   nbf.v4.new_code_cell(show_main_effect),
                   nbf.v4.new_code_cell(show_epis_effect),
                   nbf.v4.new_code_cell(vis_circle_network),
                   nbf.v4.new_code_cell(vis_adjacent_matrix)
                   ]

    LASSO_nb = os.path.join(job_dir, 'LASSO_r_notebook.ipynb')
    with open(LASSO_nb, 'w') as f:
        nbf.write(nb, f)
    pass


def generate_ssLASSO_notebook(job_dir, input_x, input_y):
    load_library = '''\
# load library
library('BhGLM')
library('Matrix')
library('foreach')
library('glmnet')
library('r2d3')
quantile_normalisation <- function(df){
  df_rank <- apply(df,2,rank,ties.method="min")
  df_sorted <- data.frame(apply(df, 2, sort))
  df_mean <- apply(df_sorted, 1, mean)
  
  index_to_mean <- function(my_index, my_mean){
    return(my_mean[my_index])
  }
  
  df_final <- apply(df_rank, 2, index_to_mean, my_mean=df_mean)
  rownames(df_final) <- rownames(df)
  return(df_final)
}'''

    load_params = '''\
# load parameters
s0 <- 0.03
s1 <- 0.5
nFolds <- 5
seed <- 28213
set.seed(seed)
datatype <- 'discrete'  # discrete or continuous'''

    load_data = '''\
# load data
workspace <- './'
x_filename <- '{0}'
y_filename <- '{1}'
x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('x size: (%d, %d)', nrow(x), ncol(x))
x <- as.matrix(x)

y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  row.names = 1
)
sprintf('y size: (%d, %d)', nrow(y), ncol(y))
y <- as.matrix(y)'''.format(input_x, input_y)

    preprocessing = '''\
# preprocessing depending on data type
x_preprocessed <- NULL
y_preprocessed <- NULL
# for x preprocess
cat('Filter data with missing data', '\n')
x_filtered <- t(na.omit(t(x)))
if (datatype == 'discrete') {
  # discrete data is categorical, no normlization
  x_preprocessed <- x_filtered
} else if (datatype == 'continuous') {
  cat('Quantile normalization', '\n')
  x_preprocessed <- quantile_normalisation(x_filtered)
}
# for y preprocess
y_preprocessed <- scale(y)'''

    estimate_main_effect = '''\
# get s0 prior
main_prior <- glmNet(x_preprocessed,
                    y_preprocessed,
                    family = "gaussian",
                    ncv = nFolds) 
s0 <- main_prior$prior.scale 
blup_main <- bmlasso(
  x_preprocessed,
  y_preprocessed,
  family = "gaussian",
  prior = "mde",
  ss = c(s0, s1),
  verbose = TRUE
)
main_coef <- blup_main$beta
sig_main <- main_coef[which(main_coef != 0),1,drop=F]'''

    substract_main_effect = '''\
# Subtract the main effect
index_main <- rownames(sig_main)
subtracted_y <- y_preprocessed - x_preprocessed[, index_main, drop=F] %*% sig_main
subtracted_y <- scale(subtracted_y)'''

    estimate_epis_effect = '''\
# Epistatic effect estimated
# construct epistatic matrix, pairwise of each column 
epi_matrix <- NULL
for(k in 1:(ncol(x_preprocessed)-1)){
  single <- x_preprocessed[, k]
  behind <- x_preprocessed[, (k + 1):ncol(x_preprocessed)]
  # single multiply each column of behind, use as.matrix to avoid pairwise is list when k = ncol(x_preprocessed)-1
  pairwise <- as.matrix(single * behind) 
  colnames(pairwise) <- paste(colnames(x_preprocessed)[k], 
                              colnames(x_preprocessed)[(k + 1):ncol(x_preprocessed)], 
                              sep = "*")
  
  epi_matrix <- cbind(epi_matrix, pairwise)
}
if (datatype == 'continuous') {
  epi_matrix <- quantile_normalisation(epi_matrix)
}
# regression
# get s0 prior
epi_prior = glmNet(epi_matrix,
                   subtracted_y,
                   family = "gaussian",
                   ncv = nFolds) 
s0 = epi_prior$prior.scale 
blup_epi <- bmlasso(
  epi_matrix,
  subtracted_y,
  family = "gaussian",
  prior = "mde",
  ss = c(s0, s1),
  verbose = TRUE
)
epi_coef <- blup_epi$beta
sig_epi <- epi_coef[which(epi_coef != 0),1,drop=F]'''

    final_run = '''\
# Final run to re-estimate coefficient
# construct new matrix from significant main and epistatic variants
full_matrix <- cbind(x_preprocessed[, rownames(sig_main), drop=F],epi_matrix[,rownames(sig_epi),drop=F])

output_main <- matrix("NA", 0, 2)
colnames(output_main) <- c("feature", "coefficient")
output_epi <- matrix("NA", 0, 3)
colnames(output_epi) <- c("feature1", "feature2", "coefficient")
# at least two columns
if (!is.null(full_matrix) && ncol(full_matrix)>2){
  if (datatype == 'continuous') {
    full_matrix <- quantile_normalisation(full_matrix)
  }
  # regression 
  # get s0 prior
  full_prior = glmNet(full_matrix,
                      y_preprocessed,
                      family = "gaussian",
                      ncv = nFolds) 
  s0 <- full_prior$prior.scale 
  blup_full <- bmlasso(
      full_matrix,
      y_preprocessed,
      family = "gaussian",
      prior = "mde",
      ss = c(s0, s1),
      verbose = TRUE
    )
  full_coef <- as.matrix(blup_full$beta)
  rownames(full_coef) <- c(rownames(sig_main), rownames(sig_epi))
  sig_full <- full_coef[which(full_coef != 0),1,drop=F]
  
  # generate main results
  main_index <- setdiff(1:nrow(sig_full), grep("\\\*", rownames(sig_full)))
  output_main <- matrix("NA", length(main_index), 2)
  output_main[, 1] <- rownames(sig_full)[main_index]
  output_main[, 2] <- sig_full[main_index, 1]
  colnames(output_main) <- c("feature", "coefficient")
  # generate epistatic results
  epi_index <- grep("\\\*", rownames(sig_full))
  output_epi <- matrix("NA", length(epi_index), 3)
  epi_ID <- rownames(sig_full)[epi_index]
  output_epi[, 1:2] <- matrix(unlist(strsplit(epi_ID, "\\\*")), ncol = 2, byrow=T)
  output_epi[, 3] <- sig_full[epi_index, 1]
  colnames(output_epi) <- c("feature1", "feature2", "coefficient")
}'''

    show_main_effect = '''output_main'''

    show_epis_effect = '''output_epi'''

    # for data visualization
    vis_circle_network = '''\
# generate json
# get all epsitasis nodes (unique)
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
json_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  f2 <- matrix(output_epi[output_epi[, 1] == f1, ], ncol=6)
  f2[,2] <- sprintf('"epis.%s"', f2[,2])
  element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
  json_str <- c(json_str,element)
}
json_str <- sprintf('[%s]',paste(json_str, collapse=',' ))
# circle network
r2d3(data=json_str, script = "../static/js/vis_CN.js", css = "../static/css/vis_CN.css")'''

    vis_adjacent_matrix = '''\
# For adjacent matrix
epsi_nodes <- c(output_epi[, 1], output_epi[, 2])
epsi_nodes <- unique(epsi_nodes)
nodes_str <- NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  element <- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
  nodes_str <- c(nodes_str,element)
}
nodes_str <- sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
link_str <- NULL
for(i in 1:nrow(output_epi)){
  source_index <- match(output_epi[i,1], epsi_nodes)
  target_index <- match(output_epi[i,2], epsi_nodes)
  coff <- as.numeric(output_epi[i,3])
  element <- sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
  link_str <- c(link_str,element)
}

link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
am_json<-sprintf('{%s,%s}',nodes_str,link_str)
write(am_json,'am.json')
r2d3(d3_version = 4, script = "../static/js/vis_AM.js", css = "../static/css/vis_AM.css", dependencies = "../static/js/d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(preprocessing),
                   nbf.v4.new_code_cell(estimate_main_effect),
                   nbf.v4.new_code_cell(substract_main_effect),
                   nbf.v4.new_code_cell(estimate_epis_effect),
                   nbf.v4.new_code_cell(final_run),
                   nbf.v4.new_code_cell(show_main_effect),
                   nbf.v4.new_code_cell(show_epis_effect),
                   nbf.v4.new_code_cell(vis_circle_network),
                   nbf.v4.new_code_cell(vis_adjacent_matrix)
                   ]

    ssLasso_nb = os.path.join(job_dir, 'ssLASSO_r_notebook.ipynb')
    with open(ssLasso_nb, 'w') as f:
        nbf.write(nb, f)
