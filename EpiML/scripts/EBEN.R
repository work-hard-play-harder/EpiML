library('EBEN')
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
x_filename <- 'yeast_Geno.txt'
y_filename <- 'yeast_Pheno.txt'
datatype <- 'discrete'  # discrete or continuous
nFolds <- 2
# max_percentages_miss_val <- 0.2
pvalue <- 0.05
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
datatype <- args[4]
nFolds <- as.integer(args[5])
seed <- as.integer(args[6])

cat('EBEN_train parameters:', '\n')
cat('\tWorkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tDatatype:', datatype, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tSeed:', seed, '\n')

set.seed(seed)

# reading data
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
  x_preprocessed <- quantile_normalisation(x_filtered)
}
# for y preprocess
y_preprocessed <- scale(y)

cat('Main effect estimated', '\n')
cv_main = EBelasticNet.GaussianCV(x_preprocessed, y_preprocessed, nFolds = nFolds, Epis = "no")
blup_main = EBelasticNet.Gaussian(
  x_preprocessed,
  y_preprocessed,
  lambda = cv_main$Lambda_optimal,
  alpha = cv_main$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
main = as.matrix(blup_main$weight)
sig_main = main[which(main[, 6] <= pvalue),, drop = F]

cat('Subtract the main effect', '\n')
index_main <- sig_main[, 1]
effect_main <- sig_main[, 3]
subtracted_y <- as.matrix(y_preprocessed) - x_preprocessed[, index_main] %*% (as.matrix(effect_main))
# Does subtracted_y need to be scaled?
subtracted_y <- scale(subtracted_y)

cat('Epistatic effect estimated', '\n')
cv_epis = EBelasticNet.GaussianCV(x_preprocessed, subtracted_y, nFolds = nFolds, Epis = "yes")
blup_epis = EBelasticNet.Gaussian(
  x_preprocessed,
  subtracted_y,
  lambda =  cv_epis$Lambda_optimal,
  alpha = cv_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
epi = as.matrix(blup_epis$weight)
sig_epi = epi[which(epi[, 6] <= pvalue),, drop = F]

cat('Final run', '\n')
full_id = rbind(sig_main[, 1:2], sig_epi[, 1:2])
full_matrix <- NULL
for (i in 1:nrow(full_id)) {
  if (full_id[i, 1] == full_id[i, 2]) {
    full_matrix <- cbind(full_matrix, x_preprocessed[, full_id[i, 1]])
  }
  if (full_id[i, 1] != full_id[i, 2]) {
    col <-
      x_preprocessed[, full_id[i, 1]] * x_preprocessed[, full_id[i, 2]]
    full_matrix <- cbind(full_matrix, col)
  }
}
if (ncol(full_matrix)==0){
  # for not significant effect
  output_main <- matrix("NA", 0, 5)
  colnames(output_main) <- c('feature', 'coefficent', 'posterior variance', 't-value', 'p-value')
  output_epi <- matrix("NA", 0, 6)
  colnames(output_epi) <- c('feature1', 'feature2', 'coefficent', 'posterior variance', 't-value', 'p-value')
}else{
  if (datatype == 'continuous') {
    full_matrix <- quantile_normalisation(full_matrix)
  }
  #regression
  cv_full = EBelasticNet.GaussianCV(full_matrix, y_preprocessed, nFolds = nFolds, Epis = "no")
  blup_full = EBelasticNet.Gaussian(
    full_matrix,
    y_preprocessed,
    lambda =  cv_full$Lambda_optimal,
    alpha = cv_full$Alpha_optimal,
    Epis = "no",
    verbose = 0
  )
  full = as.matrix(blup_full$weight)
  sig_full = full[which(full[, 6] <= pvalue),, drop = F]
  sig_full[, 1:2] <- full_id[sig_full[, 1], 1:2]
  
  output_main <- NULL
  output_epi <- NULL
  for (i in 1:nrow(sig_full)) {
    if (sig_full[i, 1] == sig_full[i, 2]) {
      output_main <- rbind(output_main, c(colnames(x_preprocessed)[sig_full[i, 1]], sig_full[i, 3:6]))
    }
    if (sig_full[i, 1] != sig_full[i, 2]) {
      output_epi <-
        rbind(output_epi, c(
          colnames(x_preprocessed)[sig_full[i, 1]],
          colnames(x_preprocessed)[sig_full[i, 2]],
          sig_full[i, 3:6]
        ))
    }
  }
  colnames(output_main) <- c('feature', 'coefficent', 'posterior variance', 't-value', 'p-value')
  colnames(output_epi) <- c('feature1', 'feature2', 'coefficent', 'posterior variance', 't-value', 'p-value')
}
cat('Ouput the final result', '\n')
write.table(
  output_main,
  file = file.path(workspace, 'output_main.txt'),
  quote = F,
  sep = '\t',
  col.names = T,
  row.names = F
)
write.table(
  output_epi,
  file = file.path(workspace, 'epis_result.txt'),
  quote = F,
  sep = '\t',
  col.names = T,
  row.names = F
)

cat('Done!')