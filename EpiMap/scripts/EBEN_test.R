library('EBEN')
library('jsonlite')
library('sets')

workspace <- '~/Downloads/EBEN-epistasis-master-4/'
x_filename <- 'bc_x.txt'
main_filename <- 'bc_y.txt'
epis_filename <- 'bc_y.txt'

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
main_filename <- args[3]
epis_filename <- args[4]

cat('EBEN_train parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tmain_filename:', main_filename, '\n')
cat('\tepis_filename:', epis_filename, '\n')

x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  row.names = 1
)
sprintf('x size: (%d, %d)', nrow(x), ncol(x))

x <- t(x)
x11 <- matrix(as.numeric(x), nrow(x))

