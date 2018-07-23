library('EBEN')

workspace <- '~/Downloads/EBEN-epistasis-master-4/'
x_filename <- 'bc_x.txt'
y_filename <- 'bc_y.txt'

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]

cat('EBEN_train parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')

x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names=FALSE,
  row.names = 1
)
sprintf('x size: (%d, %d)', nrow(x), ncol(x))

y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  row.names = 1
)
sprintf('y size: (%d, %d)', nrow(y), ncol(y))

y <- as.matrix(y)
target1 <- log(as.numeric(y), base = exp(1))
cat('Transform pathological stages into natural log values', '\n')

x <- t(x)
x11 <- matrix(as.numeric(x), nrow(x))

cat('Filter the miRNA data with more than 20% missing data', '\n')
x1 <- NULL
x1_rownames<-NULL
for (i in 1:nrow(x11)) {
  if (sum(as.numeric(x11[i, ]) != 0)) {
    x1 <- rbind(x1, x[i, ])
    x1_rownames<-c(x1_rownames,rownames(x)[i])
  }
}
rownames(x1)<-x1_rownames

x2 <- NULL
x2_rownames<-NULL
criteria <- trunc((ncol(x1) - 1) * 0.8)
for (i in 1:nrow(x1)) {
  if (sum(as.numeric(x1[i, (2:ncol(x1))]) != 0) > criteria) {
    x2 <- rbind(x2, x1[i, ])
    x2_rownames<-c(x2_rownames,x1_rownames[i])
  }
}
rownames(x2)<-x2_rownames
colnames(x2) <- colnames(x)

cat('Quantile normalization', '\n')
x3 <- x2
for (sl in 1:nrow(x3)) {
  mat = matrix(as.numeric(x3[sl, ]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (ncol(x3) + 1))
  x3[sl, ] = mat
}
rm(sl, mat)

cat('Main effect estimated using EBEN', '\n')
x4 <- matrix(as.numeric(x3), nrow = nrow(x3))
CV = EBelasticNet.GaussianCV(t(x4), target1, nFolds = 5, Epis = "no")
Blup1 = EBelasticNet.Gaussian(
  t(x4),
  target1,
  lambda = CV$Lambda_optimal,
  alpha = CV$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_main_sig = Blup1$weight[which(Blup1$weight[, 6] <= 0.05), ]

cat('Substract the main effect', '\n')
x5 <- t(x4)
index_main <- Blup_main_sig[, 1]
effect_main <- Blup_main_sig[, 3]
target_new <-
  as.matrix(target1) - x5[, index_main] %*% (as.matrix(effect_main))

cat('Epistatic effect estimated using EBEN', '\n')
CV_epis = EBelasticNet.GaussianCV(t(x4), target_new, nFolds = 5, Epis = "yes")
Blup_epis = EBelasticNet.Gaussian(
  t(x4),
  target_new,
  lambda =  CV_epis$Lambda_optimal,
  alpha = CV_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
Blup_epis_sig = Blup_epis$weight[which(Blup_epis$weight[, 6] <= 0.05), ]


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
  mat = matrix(as.numeric(new_x7[sl,]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (ncol(new_x7) + 1))
  new_x7[sl,] = mat
}
rm(sl, mat)

new_x8 <- t(new_x7)
CV_full = EBelasticNet.GaussianCV(new_x8, target1, nFolds = 5, Epis = "no")
Blup_full = EBelasticNet.Gaussian(
  new_x8,
  target1,
  lambda =  CV_full$Lambda_optimal,
  alpha = CV_full$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_full_sig =  Blup_full$weight[which(Blup_full$weight[, 6] <= 0.05),]

idma <- matrix(NA, nrow = nrow(Blup_full_sig), 6)
for (i in 1:nrow(Blup_full_sig)) {
  idma[i,] = c(main_epi_miR_id[Blup_full_sig[i, 1], 1:2], Blup_full_sig[i, 3:6])
}

main_result <- NULL
epsi_result <- NULL
for (i in 1:nrow(idma)) {
  if (idma[i, 1] == idma[i, 2]) {
    main_result <- rbind(main_result, c(rownames(x3)[idma[i, 1]],idma[i,3:6]))
  }
  if (idma[i, 1] != idma[i, 2]) {
    epsi_result <- rbind(epsi_result, c(rownames(x3)[idma[i, 1]],rownames(x3)[idma[i, 2]],idma[i,3:6]))
  }
}

cat('Ouput the final result including main and epistatic effect', '\n')
write.table(
  main_result,
  file = file.path(workspace, 'EBEN.main_result.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = c('features','coefficent value','posterior variance','t-value','p-value')
)
write.table(
  epsi_result,
  file = file.path(workspace, 'EBEN.epis_result.txt'),
  quote = F,
  sep = '\t',
  row.names = F,
  col.names = c('features1','features2','coefficent value','posterior variance','t-value','p-value')
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