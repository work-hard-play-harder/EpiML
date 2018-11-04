library("fdrtool");
library("Matrix");
library("foreach");
library("glmnet");

workspace <- '~/Desktop/samples/'
x_filename <- 'Geno.txt'
y_filename <- 'Pheno.txt'
nFolds <- 5
max_percentages_miss_val <- 0.2
seed <- 28213

args <- commandArgs(trailingOnly = TRUE)
workspace <- args[1]
x_filename <- args[2]
y_filename <- args[3]
nFolds <- as.integer(args[4])
max_percentages_miss_val <- as.numeric(args[5])
seed <- as.integer(args[6])

cat('EBEN_train parameters:', '\n')
cat('\tWorkspace:', workspace, '\n')
cat('\tx_filename:', x_filename, '\n')
cat('\ty_filename:', y_filename, '\n')
cat('\tnFolds:', nFolds, '\n')
cat('\tMax percentage of missing value:', max_percentages_miss_val,'\n')
cat('\tSeed:', seed, '\n')

set.seed(seed)

## Input the Yeast data and pathological data
mi <- read.table(file.path(workspace, x_filename),header=T);
mi <- as.matrix(mi);
target <- read.table(file.path(workspace, y_filename));
target <- as.matrix(target);

## Remove the samples without pathological data
mi2 <- mi[which(target[,1,drop=F]!='NA'),];
x11 <- mi2[,2:ncol(mi2)];

## Filter the Yeast data with more than 20% missing data
x1 <- NULL;
for(i in 1:nrow(x11)){
  if(sum(as.numeric(x11[i,]) != "NA")){x1 <- rbind(x1,mi2[i,]);}
}

x2 <- NULL;
criteria <- trunc((ncol(x1)-1) *0.8);  
for(i in 1:nrow(x1)){
  if(sum(as.numeric(x1[i,(2:ncol(x1))]) != "NA") > criteria){
    x2 <- rbind(x2,x1[i,]);
  }
}
new_matrix_miRNA <- cbind(x2,target);

## Main effect estimated using EBEN:);
CV = cv.glmnet(x2[,2:ncol(x2)], target, nfolds=nFolds);
Blup = glmnet(x2[,2:ncol(x2)], target,alpha=1,family=c("gaussian"), lambda=CV$lambda.min,intercept = TRUE);
main = t(as.matrix(Blup$beta));
Blup_main = t(main[,which(main != 0),drop=F]);

## Substract the main effect:
index_main <- rownames(Blup_main);
target_new <- as.matrix(target) - x2[,index_main,drop=F] %*% (as.matrix(Blup_main));

## Epistatic effect estimated using EBEN:
pseudo_matrix <- NULL;
mi3 = mi2[,2:ncol(x2)];
for(k in 1:(ncol(mi3)-1)){
  single_new = mi3[,k,drop=FALSE];
  new = mi3[,(k+1):ncol(mi3),drop=F];
  new_combine = cbind(new,single_new);
  pseudo_allmat = transform(new_combine,subpseudo = new_combine[,1:(ncol(mi3)-k)] * new_combine[,ncol(new_combine)]);
  colnames(pseudo_allmat) <- paste(colnames(pseudo_allmat), colnames(single_new),sep = "*");
  pseudo_mat = pseudo_allmat[,grep("subpseudo",colnames(pseudo_allmat)),drop=FALSE];
  pseudo_mat = as.matrix(pseudo_mat);
  pseudo_matrix <- rbind(pseudo_matrix,t(pseudo_mat));
  rownames(pseudo_matrix)[[length(rownames(pseudo_matrix))]] <- paste(paste("subpseudo.",sep=""),paste(colnames(mi3)[[length(colnames(mi3))]], colnames(mi3)[[length(colnames(mi3))-1]],sep = "*"),sep="");
}

CV_epi = cv.glmnet(t(pseudo_matrix), target_new, nfolds=nFolds);
Blup_epi = glmnet(t(pseudo_matrix), target_new,alpha=1,family=c("gaussian"), lambda=CV$lambda.min,intercept = TRUE);
Epis = t(as.matrix(Blup_epi$beta));
Blup_epis = t(Epis[,which(Epis != 0),drop=F]);

## Final run:
Blup_sum <- rbind(Blup_main,Blup_epis);
Blup_sum <- cbind(rownames(Blup_sum),Blup_sum);
new_matrix <- NULL;
for(i in 1:nrow(Blup_sum)){
  if(length(grep("\\*",Blup_sum[i,1])) == 0){
    tmp1 = mi3[,(Blup_sum[i,1]),drop=F];
    colnames(tmp1) = Blup_sum[i,1];
    new_matrix <-cbind(new_matrix,tmp1);
  }
  if(length(grep("\\*",Blup_sum[i,1])) == 1){
    tmp =  gsub("subpseudo.","",Blup_sum[i,1]);
    indexes = strsplit(tmp,"\\*");
    tmp1 = mi3[,indexes[[1]][1],drop=F] * mi3[,indexes[[1]][2],drop=F];
    colnames(tmp1) = tmp;
    new_matrix <-cbind(new_matrix,tmp1);
  }
}

CV_full = cv.glmnet(new_matrix, target, nfolds=nFolds);
Blup_full = glmnet(new_matrix, target,alpha=1,family=c("gaussian"), lambda=CV$lambda.min,intercept = TRUE);
res = as.matrix(Blup_full$beta);
Blup_full_sig =  res[which(res[,1,drop=F] != 0),,drop=F];
colnames(Blup_full_sig) <- "Effect";

Blup_estimate<-Blup_full_sig

# for main effect
main_index <- setdiff(1:nrow(Blup_estimate),grep("\\*",rownames(Blup_estimate)));
output_main <- matrix("NA",length(main_index),5);
output_main[,1] <- matrix(rownames(Blup_estimate),ncol=1)[main_index,,drop=F];
output_main[,2] <- Blup_estimate[main_index,1,drop=F]
colnames(output_main) <- c("feature", "coefficent value", "posterior variance",	"t-value","p-value");

# for epistasic effect
epi_index <- grep("\\*",rownames(Blup_estimate))
output_epi <- matrix("NA",length(epi_index),6);
epi_ID <- matrix(rownames(Blup_estimate),ncol=1)[epi_index,,drop=F];
output_epi[,1:2] <- matrix(unlist(strsplit(epi_ID,"\\*")),ncol=2);
output_epi[,3] <- Blup_estimate[epi_index,1,drop=F];
colnames(output_epi) <- c("feature1","feature2", "coefficent value", "posterior variance", "t-value","p-value");

## Ouput the final result including main and epistatic effect
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
