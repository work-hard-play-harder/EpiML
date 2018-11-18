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

cat('Main effect estimated using ssLASSO', '\n')
sig_main_index <- which(abs(t(y_preprocessed) %*% x_preprocessed/(nrow(x_preprocessed)-1)) > 0.20);
sig_main_names <- colnames(x_preprocessed)[sig_main_index];

###### Epistasis effect-single locus:
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
sig_names <-c(sig_main_names, sig_epi_names)

new_x <- NULL;
for(i in 1:length(sig_names)){
  if(length(grep("\\*",sig_names[i])) == 0){
    tmp1 = x_preprocessed[, sig_names[i], drop=F]
    new_x <-cbind(new_x,tmp1)
  }
  if(length(grep("\\*",sig_names[i])) == 1){
    pair_names <- strsplit(sig_names[i],"\\*")
    tmp1 <- x_preprocessed[, pair_names[[1]][1], drop=F] * x_preprocessed[, pair_names[[1]][2], drop=F];
    colnames(tmp1) <- sig_names[i]
    new_x <- cbind(new_x,tmp1);
  }
}

f2 <- bmlasso(new_x, y_preprocessed, family = "gaussian", prior = "mde", ss = c(s0,s1), verbose = TRUE)
# cv <- cv.bh(f2, ncv=50, nfolds = 3, verbose = TRUE)
# tmp_mse <- cv$measures["mse"];
# tmp_dev <- cv$measures["deviance"];
Blup <- matrix(f2$beta,ncol=1)
rownames(Blup) <- sig_names
Blup_estimate <- Blup[which(Blup != 0),1,drop=F]

# generate main results
main_index <- setdiff(1:nrow(Blup_estimate),grep("\\*",rownames(Blup_estimate)))
output_main <- matrix("NA",length(main_index),2)
output_main[,1] <- rownames(Blup_estimate)[main_index]
output_main[,2] <- Blup_estimate[main_index,1]
colnames(output_main) <- c("feature", "coefficent");
# generate epistatic results
epi_index <- grep("\\*",rownames(Blup_estimate))
output_epi <- matrix("NA",length(epi_index),3)
epi_ID <- rownames(Blup_estimate)[epi_index]
output_epi[,1:2] <- matrix(unlist(strsplit(epi_ID,"\\*")),ncol=2)
output_epi[,3] <- Blup_estimate[epi_index,1]
colnames(output_epi) <- c("feature1","feature2", "coefficent");


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

