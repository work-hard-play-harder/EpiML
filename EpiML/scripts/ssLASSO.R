# load library
library('BhGLM');
library('Matrix');
library('foreach');
library('glmnet');
source('cv.bh.R');
library('r2d3')

workspace <- '~/Desktop/samples/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
s0 <- 0.03;
s1 <- 0.5;
nFolds <- 5
seed <- 28213
set.seed(seed)

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
nFolds <- as.integer(args[4])
seed <- as.integer(args[5])

cat('ssLasso parameters:', '\n')
cat('\tworkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tseed:', seed, '\n')

cat('read data','\n')
x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('features size: (%d, %d)', nrow(x), ncol(x))

y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('y size: (%d, %d)', nrow(y), ncol(y))

features <- as.matrix(x);
colnames(features) <- seq(1,ncol(features));
pheno <- as.matrix(y);

geno_stand <- features;
# ssLASSO requires to scale y
new_y <- scale(pheno);
new_y_in <- new_y[,1,drop=F];

###### Main effect-single locus:
sig_index <- which(abs(t(new_y_in) %*% geno_stand/(nrow(geno_stand)-1)) > 0.20);
sig_main <- sig_index;

######Epistasis effect-single locus:
sig_epi_sum <- NULL;
for(k in 1:(ncol(features)-1)){
  single_new <- features[,k,drop=FALSE];
  new <- features[,(k+1):ncol(features)];
  new_combine <- cbind(new,single_new);
  pseudo_allmat <- transform(new_combine,subpseudo=new_combine[,1:(ncol(features)-k)] * new_combine[,ncol(new_combine)]);
  colnames(pseudo_allmat) <- paste(colnames(pseudo_allmat), colnames(single_new),sep = "*");
  pseudo_mat <- pseudo_allmat[,grep("subpseudo",colnames(pseudo_allmat)),drop=FALSE];
  pseudo_mat <- as.matrix(pseudo_mat);
  pseudo_mat_stand <- scale(pseudo_mat);
  
  epi_index <- which(abs(t(new_y_in) %*% pseudo_mat_stand/(nrow(pseudo_mat_stand)-1)) > 0.20);
  pseudo_mat_stand_epi <- pseudo_mat[,epi_index,drop=FALSE];
  sig_epi_sum <- c(sig_epi_sum,colnames(pseudo_mat_stand_epi));
}
res <- matrix(c(sig_main,sig_epi_sum),ncol=1);
res <- gsub("subpseudo.","",res)

new_matrix <- NULL;
for(i in 1:nrow(res)){
  if(length(grep("\\*",res[i,1])) == 0){
    tmp1 = features[,(as.numeric(res[i,1])),drop=F];
    colnames(tmp1) <- res[i,1];
    new_matrix <-cbind(new_matrix,tmp1);
  }
  if(length(grep("\\*",res[i,1])) == 1){
    indexes <- strsplit(res[i,1],"\\*");
    tmp1 <- features[,as.numeric(indexes[[1]][1]),drop=F] * features[,as.numeric(indexes[[1]][2]),drop=F];
    colnames(tmp1) <- res[i,1];
    new_matrix <- cbind(new_matrix,tmp1);
  }
}
new_matrix <- as.matrix(new_matrix);

f2 <- bmlasso(new_matrix, new_y_in, family = "gaussian", prior = "mde", ss = c(s0,s1),verbose = TRUE);
cv <- cv.bh(f2,ncv=1,nfolds = 3,verbose = TRUE);
tmp_mse <- cv$measures["mse"];
tmp_dev <- cv$measures["deviance"];
Blup <- matrix(f2$beta,ncol=1);
rownames(Blup) <- res;
Blup_estimate <- Blup[which(Blup != 0),1,drop=F];
main_index <- setdiff(1:nrow(Blup_estimate),grep("\\*",rownames(Blup_estimate)));
epi_index <- grep("\\*",rownames(Blup_estimate))
output_main <- matrix("NA",length(main_index),2);
output_epi <- matrix("NA",length(epi_index),3);
output_main[,1] <- matrix(rownames(Blup_estimate),ncol=1)[main_index,,drop=F];
output_main[,2] <- Blup_estimate[main_index,1,drop=F]
epi_ID <- matrix(rownames(Blup_estimate),ncol=1)[epi_index,,drop=F];
output_epi[,1:2] <- matrix(unlist(strsplit(epi_ID,"\\*")),ncol=2);
output_epi[,3] <- Blup_estimate[epi_index,1,drop=F];
colnames(output_main) <- c("feature", "coefficent value");
colnames(output_epi) <- c("feature1","feature2", "coefficent value");
output_main[, 1] <- colnames(x)[as.integer(output_main[, 1])]
output_epi[, 1] <- colnames(x)[as.integer(output_epi[, 1])]
output_epi[, 2] <- colnames(x)[as.integer(output_epi[, 2])]


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

