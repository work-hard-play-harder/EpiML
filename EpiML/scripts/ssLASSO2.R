# load library
library('BhGLM');
library('Matrix');
library('foreach');
library('glmnet');
#source("cv.bh.R");

workspace <- '~/Desktop/samples/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
category <- 'Gene'
s0 <- 0.03;
s1 <- 0.5;
nFolds <- 5
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
category <- args[4]
nFolds <- as.integer(args[5])
seed <- as.integer(args[6])

cat('ssLasso parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tCategory:', category, '\n')
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
if (category == 'Gene') {
  # Gene data is categorical, no normlization
  x_preprocessed <- x_filtered
} else if (category == 'microRNA') {
  cat('Quantile normalization', '\n')
  x_filtered_normed <- x_filtered
  for (sl in 1:ncol(x_filtered_normed)) {
    mat = matrix(as.numeric(x_filtered_normed[, sl]), 1)
    mat = t(apply(mat, 1, rank, ties.method = "average"))
    mat = qnorm(mat / (nrow(x_filtered_normed) + 1))
    x_filtered_normed[, sl] = mat
  }
  x_preprocessed <- x_filtered_normed
} else{
  # no filtering and no normlization
  x_preprocessed <- x
}
# for y preprocess
y_preprocessed <- scale(y)

cat('Main effect estimated', '\n')
sig_main_index <- which(abs(t(y_preprocessed) %*% x_preprocessed/(nrow(x_preprocessed)-1)) > 0.20);
sig_main_names <- colnames(x_preprocessed)[sig_main_index];

cat('Epistatic effect estimated', '\n')
sig_epi_names <- NULL;
for(k in 1:(ncol(x_preprocessed)-1)){
  single <- x_preprocessed[, k]
  behind <- x_preprocessed[, (k + 1):ncol(x_preprocessed)]
  # single multiply each column of behind, use as.matrix to avoid pairwise is list when k = ncol(x_preprocessed)-1
  pairwise <- as.matrix(single * behind) 
  colnames(pairwise) <- paste(colnames(x_preprocessed)[k], colnames(x_preprocessed)[(k + 1):ncol(x_preprocessed)],sep = "*")
  sig_epi_index <- which(abs(t(y_preprocessed) %*% pairwise/(nrow(pairwise)-1)) > 0.20)
  sig_epi_names <- c(sig_epi_names, colnames(pairwise)[sig_epi_index])
}

# construct new x with significant variants
sig_x <- NULL
# for significated main variants
for (i in 1:length(sig_main_names)) {
  tmp1 = x_preprocessed[, sig_main_names[i], drop = F]
  sig_x <- cbind(sig_x, tmp1)
}
# for significated episitatic variants
for(i in 1:length(sig_epi_names)) {
  indexes = strsplit(sig_epi_names[i], "\\*")
  tmp1 = x_preprocessed[, indexes[[1]][1], drop = F] * x_preprocessed[, indexes[[1]][2], drop = F]
  colnames(tmp1) = sig_epi_names[i]
  sig_x <- cbind(sig_x, tmp1)
}

cat('Final run', '\n')
blup_full <- bmlasso(sig_x, y_preprocessed, family = "gaussian", prior = "mde", ss = c(s0,s1), verbose = TRUE)
full <- matrix(blup_full$beta,ncol=1)
rownames(full) <- c(sig_main_names, sig_epi_names)
sig_full <- full[which(full != 0),1,drop=F]

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
output_epi[, 1:2] <- matrix(unlist(strsplit(epi_ID, "\\*")), ncol = 2)
output_epi[, 3] <- sig_full[epi_index, 1]
colnames(output_epi) <- c("feature1", "feature2", "coefficent")


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

