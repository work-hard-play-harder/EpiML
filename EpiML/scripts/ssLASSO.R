# load library
library('BhGLM')
library('Matrix')
library('foreach')
library('glmnet')
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
}

# workspace <- '~/Desktop/samples/'
# x_filename <- 'yeast_Geno.txt'
# y_filename <- 'yeast_Pheno.txt'
workspace <- '~/Experiment/dataset/full_yeast dataset/'
x_filename <- 'geno_150_150_.txt'
y_filename <- 'pheno_150_150_.txt'
datatype <- 'discrete'  # discrete or continuous
s0 <- 0.03
s1 <- 0.5
nFolds <- 5
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
datatype <- args[4]
nFolds <- as.integer(args[5])
seed <- as.integer(args[6])

cat('ssLasso parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tDatatype:', datatype, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tseed:', seed, '\n')

set.seed(seed)

cat('reading data','\n')
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
y <- as.matrix(y)

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
y_preprocessed <- scale(y)

cat('Main effect estimated', '\n')
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
sig_main <- main_coef[which(main_coef != 0),1,drop=F]

cat('Subtract the main effect', '\n')
index_main <- rownames(sig_main)
subtracted_y <- y_preprocessed - x_preprocessed[, index_main, drop=F] %*% sig_main
subtracted_y <- scale(subtracted_y)

cat('Epistatic effect estimated', '\n')
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
epi_prior <- glmNet(epi_matrix,
                   subtracted_y,
                   family = "gaussian",
                   ncv = nFolds) 
s0 <- epi_prior$prior.scale 
blup_epi <- bmlasso(
  epi_matrix,
  subtracted_y,
  family = "gaussian",
  prior = "mde",
  ss = c(s0, s1),
  verbose = TRUE
)
epi_coef <- blup_epi$beta
sig_epi <- epi_coef[which(epi_coef != 0),1,drop=F]

cat('Final run', '\n')
# construct new matrix from significant main and epistatic variants
full_matrix <- cbind(x_preprocessed[, rownames(sig_main), drop=F],epi_matrix[,rownames(sig_epi),drop=F])

output_main <- matrix("NA", 0, 2)
colnames(output_main) <- c("feature", "coefficent")
output_epi <- matrix("NA", 0, 3)
colnames(output_epi) <- c("feature1", "feature2", "coefficent")
# at least two columns
if (!is.null(full_matrix) && ncol(full_matrix)>2){
  if (datatype == 'continuous') {
    full_matrix <- quantile_normalisation(full_matrix)
  }
  # regression 
  # get s0 prior
  full_prior <- glmNet(full_matrix,
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
  main_index <- setdiff(1:nrow(sig_full), grep("\\*", rownames(sig_full)))
  output_main <- matrix("NA", length(main_index), 2)
  output_main[, 1] <- rownames(sig_full)[main_index]
  output_main[, 2] <- sig_full[main_index, 1]
  colnames(output_main) <- c("feature", "coefficent")
  # generate epistatic results
  epi_index <- grep("\\*", rownames(sig_full))
  output_epi <- matrix("NA", length(epi_index), 3)
  epi_ID <- rownames(sig_full)[epi_index]
  output_epi[, 1:2] <- matrix(unlist(strsplit(epi_ID, "\\*")), ncol = 2, byrow=T)
  output_epi[, 3] <- sig_full[epi_index, 1]
  colnames(output_epi) <- c("feature1", "feature2", "coefficent")
}

cat('Write results', '\n')
write.table(
  output_main,
  file = file.path(workspace, 'main_result.txt'),
  quote = F,
  sep = "\t",
  col.names = T,
  row.names = F
)
write.table(
  output_epi,
  file = file.path(workspace, 'epis_result.txt'),
  quote = F,
  sep = "\t",
  col.names = T,
  row.names = F
)

cat('Done!')

