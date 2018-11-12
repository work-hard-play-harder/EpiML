library('EBEN')

workspace <- '~/Desktop/samples/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
category <- 'Gene'
nFolds <- 5
max_percentages_miss_val <- 0.2
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
category <- args[4]
nFolds <- as.integer(args[5])
max_percentages_miss_val <- as.numeric(args[6])
seed <- as.integer(args[7])

cat('EBEN_train parameters:', '\n')
cat('\tWorkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tCategory:', category, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tMax percentage of missing value:', max_percentages_miss_val, '\n')
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
if (category == 'Gene') {
  cat('Filter data with missing data', '\n')
  x_filtered <- t(na.omit(t(x)))
  # no normlization
  x_preprocessed <- x_filtered
  
  y_preprocessed <- y
} else if (category == 'microRNA') {
  cat('Filter data with more than 20% missing data', '\n')
  x_filtered <- x[,colMeans(is.na(x)) < max_percentages_miss_val]
  
  # x_filtered_colnames <- NULL
  # criteria <- trunc(nrow(x) * (1 - max_percentages_miss_val))
  # for (i in 1:ncol(x)) {
  #   if (sum(as.numeric(x[, i]) != 0) > criteria) {
  #     x_filtered <- cbind(x_filtered, x[, i])
  #     x_filtered_colnames <- c(x_filtered_colnames, colnames(x)[i])
  #   }
  # }
  # colnames(x_filtered) <- x_filtered_colnames
  
  cat('Quantile normalization', '\n')
  x_filtered_normed <- x_filtered
  for (sl in 1:ncol(x_filtered_normed)) {
    mat = matrix(as.numeric(x_filtered_normed[, sl]), 1)
    mat = t(apply(mat, 1, rank, ties.method = "average"))
    mat = qnorm(mat / (nrow(x_filtered_normed) + 1))
    x_filtered_normed[, sl] = mat
  }
  x_preprocessed <- x_filtered_normed
  rm(x_filtered, x_filtered_normed, sl, mat)
  
  y_preprocessed <- y
  
} else{
  # no filtering and no normlization
  x_preprocessed <- x
  y_preprocessed <- y
}

cat('Main effect estimated using EBEN', '\n')
CV = EBelasticNet.GaussianCV(x_preprocessed, y_preprocessed, nFolds = nFolds, Epis = "no")
Blup1 = EBelasticNet.Gaussian(
  x_preprocessed,
  y_preprocessed,
  lambda = CV$Lambda_optimal,
  alpha = CV$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_main_sig = matrix(Blup1$weight[which(Blup1$weight[, 6] <= 0.05),], ncol = 6)

cat('Subtract the main effect', '\n')
index_main <- Blup_main_sig[, 1]
effect_main <- Blup_main_sig[, 3]
y_preprocessed_subtracted <- as.matrix(y_preprocessed) - x_preprocessed[, index_main] %*% (as.matrix(effect_main))

cat('Epistatic effect estimated using EBEN', '\n')
CV_epis = EBelasticNet.GaussianCV(x_preprocessed, y_preprocessed_subtracted, nFolds = nFolds, Epis = "yes")
Blup_epis = EBelasticNet.Gaussian(
  x_preprocessed,
  y_preprocessed_subtracted,
  lambda =  CV_epis$Lambda_optimal,
  alpha = CV_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
Blup_epis_sig = matrix(Blup_epis$weight[which(Blup_epis$weight[, 6] <= 0.05),], ncol = 6)


cat('Final run', '\n')
main_epi_sig_id = rbind(Blup_main_sig[, 1:2], Blup_epis_sig[, 1:2])

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
cat('Quantile normalization', '\n')
for (sl in 1:ncol(x_sig_qnormed)) {
  mat = matrix(as.numeric(x_sig_qnormed[, sl]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (nrow(x_sig_qnormed) + 1))
  x_sig_qnormed[, sl] = mat
}
rm(x_sig, sl, mat)

CV_full = EBelasticNet.GaussianCV(x_sig_qnormed, y_preprocessed, nFolds = nFolds, Epis = "no")
Blup_full = EBelasticNet.Gaussian(
  x_sig_qnormed,
  y_preprocessed,
  lambda =  CV_full$Lambda_optimal,
  alpha = CV_full$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_full_sig =  Blup_full$weight[which(Blup_full$weight[, 6] <= 0.05), ]
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
    'coefficent value',
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
    'coefficent value',
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