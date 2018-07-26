library('EBEN')

workspace <- '~/Downloads/EBEN-epistasis-master-4/'
x_filename <- 'EBEN_BASIS.txt'
y_filename <- 'EBEN_y.txt'

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
nFolds <- args[4]
seed <- args[5]

cat('EBEN_train parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tseed:', seed, '\n')

set.seed(seed)

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
y <- as.numeric(as.matrix(y))

cat('Quantile normalization', '\n')
x3 <- t(x)
for (sl in 1:nrow(x3)) {
  mat = matrix(as.numeric(x3[sl,]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (ncol(x3) + 1))
  x3[sl,] = mat
}
rm(sl, mat)

cat('Main effect estimated using EBEN', '\n')
x4 <- matrix(as.numeric(x3), nrow = nrow(x3))
CV = EBelasticNet.GaussianCV(t(x4), y, nFolds = nFolds, Epis = "no")
Blup1 = EBelasticNet.Gaussian(
  t(x4),
  y,
  lambda = CV$Lambda_optimal,
  alpha = CV$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_main_sig = Blup1$weight

cat('Substract the main effect', '\n')
x5 <- t(x4)
index_main <- Blup_main_sig[, 1]
effect_main <- Blup_main_sig[, 3]
target_new <-
  as.matrix(y) - x5[, index_main] %*% (as.matrix(effect_main))

cat('Epistatic effect estimated using EBEN', '\n')
CV_epis = EBelasticNet.GaussianCV(t(x4), target_new, nFolds = nFolds, Epis = "yes")
Blup_epis = EBelasticNet.Gaussian(
  t(x4),
  target_new,
  lambda =  CV_epis$Lambda_optimal,
  alpha = CV_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
Blup_epis_sig = Blup_epis$weight


cat('Final run', '\n')
mir <- as.matrix(t(x3))
mir <- matrix(as.numeric(mir), nrow = nrow(mir))
main_epi_miR_id = rbind(Blup_main_sig[, 1:2], Blup_epis_sig[, 1:2])

new_x6 <- NULL
for (i in 1:nrow(main_epi_miR_id)) {
  if (main_epi_miR_id[i, 1] == main_epi_miR_id[i, 2]) {
    new_x6 <- cbind(new_x6, mir[, main_epi_miR_id[i, 1]])
  }
  if (main_epi_miR_id[i, 1] != main_epi_miR_id[i, 2]) {
    col <- mir[, main_epi_miR_id[i, 1]] * mir[, main_epi_miR_id[i, 2]]
    new_x6 <- cbind(new_x6, col)
  }
}

new_x7 <- t(new_x6)
for (sl in 1:nrow(new_x7)) {
  mat = matrix(as.numeric(new_x7[sl, ]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (ncol(new_x7) + 1))
  new_x7[sl, ] = mat
}
rm(sl, mat)

new_x8 <- t(new_x7)
CV_full = EBelasticNet.GaussianCV(new_x8, y, nFolds = nFolds, Epis = "no")
Blup_full = EBelasticNet.Gaussian(
  new_x8,
  y,
  lambda =  CV_full$Lambda_optimal,
  alpha = CV_full$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_full_sig =  Blup_full$weight

idma <- matrix(NA, nrow = nrow(Blup_full_sig), 6)
for (i in 1:nrow(Blup_full_sig)) {
  idma[i, ] = c(main_epi_miR_id[Blup_full_sig[i, 1], 1:2], Blup_full_sig[i, 3:6])
}

main_result <- NULL
epsi_result <- NULL
for (i in 1:nrow(idma)) {
  if (idma[i, 1] == idma[i, 2]) {
    main_result <-
      rbind(main_result, c(rownames(x3)[idma[i, 1]], idma[i, 3:6]))
  }
  if (idma[i, 1] != idma[i, 2]) {
    epsi_result <-
      rbind(epsi_result, c(rownames(x3)[idma[i, 1]], rownames(x3)[idma[i, 2]], idma[i, 3:6]))
  }
}

cat('Ouput the final result including main and epistatic effect', '\n')
write.table(
  main_result,
  file = file.path(workspace, 'EBEN.main_result.txt'),
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
  file = file.path(workspace, 'EBEN.epis_result.txt'),
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
  file = file.path(workspace, 'EBEN.blup_full_hyperparams.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = T
)

cat('Done!')
