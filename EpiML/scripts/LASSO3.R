library("fdrtool")
library("Matrix")
library("foreach")
library("glmnet")
source('qnorm.r')

workspace <- '~/Desktop/samples/'
x_filename <- 'yeast_Geno.txt'
y_filename <- 'yeast_Pheno.txt'
datatype <- 'discrete'  # discrete or continuous
nFolds <- 5
# max_percentages_miss_val <- 0.2
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

# preprocessing for different job categories
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
  x_filtered_normed <- qnorm(x_filtered)
  qnorm(x_filtered)
  for (sl in 1:ncol(x_filtered_normed)) {
    mat = matrix(as.numeric(x_filtered_normed[, sl]), 1)
    mat = t(apply(mat, 1, rank, ties.method = "average"))
    mat = qnorm(mat / (nrow(x_filtered_normed) + 1))
    x_filtered_normed[, sl] = mat
  }
  x_preprocessed <- x_filtered_normed
}
# for y preprocess
y_preprocessed <- scale(y)

cat('Main effect estimated', '\n')
cv_main = cv.glmnet(x_preprocessed, y_preprocessed, nfolds=nFolds)
blup_main = glmnet(
  x_preprocessed,
  y_preprocessed,
  alpha = 1,
  family = c("gaussian"),
  lambda = cv_main$lambda.min,
  intercept = TRUE
)
main = as.matrix(blup_main$beta)
sig_main = main[which(main != 0), 1, drop = F]

cat('Subtract the main effect', '\n')
index_main <- rownames(sig_main)
# Does subtracted_y need to be scaled?
subtracted_y <- y_preprocessed - x_preprocessed[, index_main, drop=F] %*% sig_main

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
  
  epi_matrix <- cbind(epi_matrix,pairwise)
}
# regression using lasso
cv_epi = cv.glmnet(epi_matrix, subtracted_y, nfolds=nFolds);
blup_epi = glmnet(
  epi_matrix,
  subtracted_y,
  alpha = 1,
  family = c("gaussian"),
  lambda = cv_epi$lambda.min,
  intercept = TRUE
)
epi = as.matrix(blup_epi$beta)
sig_epi = epi[which(epi != 0), 1, drop = F]

cat('Final run', '\n')
# construct new matrix from significant main and epistatic variants
full_matrix <- cbind(x_preprocessed[, rownames(sig_main)],epi_matrix[,rownames(sig_epi)])
# regression 
cv_full = cv.glmnet(full_matrix, y_preprocessed, nfolds=nFolds)
blup_full = glmnet(
  full_matrix,
  y_preprocessed,
  alpha = 1,
  family = c("gaussian"),
  lambda = cv_full$lambda.min,
  intercept = TRUE
)
full = as.matrix(blup_full$beta)
sig_full = full[which(full != 0), 1, drop = F]

cat('Generate result tables', '\n')
# for main effect
main_index <- setdiff(1:nrow(sig_full), grep("\\*", rownames(sig_full)))
output_main <- matrix("NA", length(main_index), 2)
output_main[, 1] <- matrix(rownames(sig_full), ncol = 1)[main_index, , drop = F]
output_main[, 2] <- sig_full[main_index, 1, drop = F]
colnames(output_main) <- c("feature", "coefficent")
# for epistasic effect
epi_index <- grep("\\*", rownames(sig_full))
output_epi <- matrix("NA", length(epi_index), 3)
epi_ID <- matrix(rownames(sig_full), ncol = 1)[epi_index, , drop = F]
output_epi[, 1:2] <- matrix(unlist(strsplit(epi_ID, "\\*")), ncol = 2)
output_epi[, 3] <- sig_full[epi_index, 1, drop = F]
colnames(output_epi) <- c("feature1", "feature2", "coefficent")

## Ouput the final result including main and epistatic effect
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