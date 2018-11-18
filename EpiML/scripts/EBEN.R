library('EBEN')

workspace <- '~/Desktop/samples/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
category <- 'Gene'
nFolds <- 2
# max_percentages_miss_val <- 0.2
pvalue <- 0.05
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
category <- args[4]
nFolds <- as.integer(args[5])
seed <- as.integer(args[6])

cat('EBEN_train parameters:', '\n')
cat('\tWorkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tCategory:', category, '\n')
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
if (category == 'Gene') {
  # Gene data is categorical, no normlization
  x_preprocessed <- x_filtered
} else if (category == 'microRNA') {
  # Quantile normalization
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
cv_main = EBelasticNet.GaussianCV(x_preprocessed, y_preprocessed, nFolds = nFolds, Epis = "no")
blup_main = EBelasticNet.Gaussian(
  x_preprocessed,
  y_preprocessed,
  lambda = cv_main$Lambda_optimal,
  alpha = cv_main$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
sig_main = matrix(blup_main$weight[which(blup_main$weight[, 6] <= pvalue),], ncol = 6)

cat('Subtract the main effect', '\n')
index_main <- sig_main[, 1]
effect_main <- sig_main[, 3]
subtracted_y <- as.matrix(y_preprocessed) - x_preprocessed[, index_main] %*% (as.matrix(effect_main))

cat('Epistatic effect estimated', '\n')
CV_epis = EBelasticNet.GaussianCV(x_preprocessed, subtracted_y, nFolds = nFolds, Epis = "yes")
Blup_epis = EBelasticNet.Gaussian(
  x_preprocessed,
  subtracted_y,
  lambda =  CV_epis$Lambda_optimal,
  alpha = CV_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
Blup_epis_sig = matrix(Blup_epis$weight[which(Blup_epis$weight[, 6] <= pvalue),], ncol = 6)

cat('Final run', '\n')
main_epi_sig_id = rbind(sig_main[, 1:2], Blup_epis_sig[, 1:2])

x_sig <- NULL
for (i in 1:nrow(main_epi_sig_id)) {
  if (main_epi_sig_id[i, 1] == main_epi_sig_id[i, 2]) {
    x_sig <- cbind(x_sig, x_preprocessed[, main_epi_sig_id[i, 1]])
  }
  if (main_epi_sig_id[i, 1] != main_epi_sig_id[i, 2]) {
    col <-
      x_preprocessed[, main_epi_sig_id[i, 1]] * x_preprocessed[, main_epi_sig_id[i, 2]]
    x_sig <- cbind(x_sig, col)
  }
}

x_sig_qnormed <- x_sig
if (category == 'microRNA') {
  cat('Quantile normalization', '\n')
  for (sl in 1:ncol(x_sig_qnormed)) {
    mat = matrix(as.numeric(x_sig_qnormed[, sl]), 1)
    mat = t(apply(mat, 1, rank, ties.method = "average"))
    mat = qnorm(mat / (nrow(x_sig_qnormed) + 1))
    x_sig_qnormed[, sl] = mat
  }
  rm(x_sig, sl, mat)
}

CV_full = EBelasticNet.GaussianCV(x_sig_qnormed, y_preprocessed, nFolds = nFolds, Epis = "no")
Blup_full = EBelasticNet.Gaussian(
  x_sig_qnormed,
  y_preprocessed,
  lambda =  CV_full$Lambda_optimal,
  alpha = CV_full$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_full_sig =  Blup_full$weight[which(Blup_full$weight[, 6] <= pvalue), ]
Blup_full_sig[, 1:2] <- main_epi_sig_id[Blup_full_sig[, 1], 1:2]

main_result <- NULL
epsi_result <- NULL
for (i in 1:nrow(Blup_full_sig)) {
  if (Blup_full_sig[i, 1] == Blup_full_sig[i, 2]) {
    main_result <- rbind(main_result, c(colnames(x_preprocessed)[Blup_full_sig[i, 1]], Blup_full_sig[i, 3:6]))
  }
  if (Blup_full_sig[i, 1] != Blup_full_sig[i, 2]) {
    epsi_result <-
      rbind(epsi_result, c(
        colnames(x_preprocessed)[Blup_full_sig[i, 1]],
        colnames(x_preprocessed)[Blup_full_sig[i, 2]],
        Blup_full_sig[i, 3:6]
      ))
  }
}

cat('Ouput the final result including main and epistatic effect', '\n')
write.table(
  main_result,
  file = file.path(workspace, 'main_result.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = c(
    'feature',
    'coefficent',
    'posterior variance',
    't-value',
    'p-value'
  )
)
write.table(
  epsi_result,
  file = file.path(workspace, 'epis_result.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = c(
    'feature1',
    'feature2',
    'coefficent',
    'posterior variance',
    't-value',
    'p-value'
  )
)
write.table(
  Blup_full[2:6],
  file = file.path(workspace, 'blup_full_hyperparams.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = T
)

cat('Done!')
