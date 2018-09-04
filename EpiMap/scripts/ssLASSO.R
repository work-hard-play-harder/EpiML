cat(getwd(),'\n')

library("BhGLM");
library("Matrix");
library("foreach");
library("glmnet");
source("EpiMap/scripts/cv.bh.R");
source("cv.bh.R");

workspace <- '~/Desktop/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
nFolds <- 5
seed <- 28213

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

set.seed(seed)

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
colnames(features) = seq(1,ncol(features));
pheno <- as.matrix(y);

geno_stand <- scale(features);
new_y <- scale(pheno);
new_y_in = new_y[,1,drop=F];

### Pre-specify s0 and s1:
s0 = 0.03;
s1 = 0.5;

###### Main effect-single locus:
sig_index = which(abs(t(new_y_in) %*% geno_stand/(nrow(geno_stand)-1)) > 0.20);
sig_main <- sig_index;

######Epistasis effect-single locus:
sig_epi_sum <- NULL;
for(k in 1:(ncol(features)-1)){
  single_new = features[,k,drop=FALSE];
  new=features[,(k+1):ncol(features)];
  new_combine = cbind(new,single_new);
  pseudo_allmat = transform(new_combine,subpseudo=new_combine[,1:(ncol(features)-k)] * new_combine[,ncol(new_combine)]);
  colnames(pseudo_allmat) <- paste(colnames(pseudo_allmat), colnames(single_new),sep = "*");
  pseudo_mat = pseudo_allmat[,grep("subpseudo",colnames(pseudo_allmat)),drop=FALSE];
  pseudo_mat = as.matrix(pseudo_mat);
  pseudo_mat_stand = scale(pseudo_mat);
  
  epi_index = which(abs(t(new_y_in) %*% pseudo_mat_stand/(nrow(pseudo_mat_stand)-1)) > 0.20);
  pseudo_mat_stand_epi = pseudo_mat[,epi_index,drop=FALSE];
  sig_epi_sum = c(sig_epi_sum,colnames(pseudo_mat_stand_epi));
}
res <- matrix(c(sig_main,sig_epi_sum),ncol=1);
res = gsub("subpseudo.","",res)

new_matrix <- NULL;
for(i in 1:nrow(res)){
  if(length(grep("\\*",res[i,1])) == 0){
    tmp1 = features[,(as.numeric(res[i,1])),drop=F];
    colnames(tmp1) = res[i,1];
    new_matrix <-cbind(new_matrix,tmp1);
  }
  if(length(grep("\\*",res[i,1])) == 1){
    indexes = strsplit(res[i,1],"\\*");
    tmp1 = features[,as.numeric(indexes[[1]][1]),drop=F] * features[,as.numeric(indexes[[1]][2]),drop=F];
    colnames(tmp1) = res[i,1];
    new_matrix <-cbind(new_matrix,tmp1);
  }
}
new_matrix = as.matrix(new_matrix);

f2 = bmlasso(new_matrix, new_y_in, family = "gaussian", prior = "mde", ss = c(s0,s1),verbose = TRUE);
cv = cv.bh(f2,ncv=1,nfolds = 3,verbose = TRUE);
tmp_mse =  cv$measures["mse"];
tmp_dev = cv$measures["deviance"];
Blup = matrix(f2$beta,ncol=1);
rownames(Blup) = res;

write.table(
  Blup,
  file = file.path(workspace, 'Beta_estimates.txt'),
  quote = F,
  sep = "\t",
  col.names = F,
  row.names = T
)

