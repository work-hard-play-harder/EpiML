import os
import nbformat as nbf

nb = nbf.v4.new_notebook()

# set R kernel
nb.metadata = {
    "kernelspec": {
        "display_name": "R",
        "language": "R",
        "name": "ir"
    },
    "language_info": {
        "codemirror_mode": "r",
        "file_extension": ".r",
        "mimetype": "text/x-r-source",
        "name": "R",
        "pygments_lexer": "r",
        "version": "3.5.0"
    }
}

title = '''\
# Epistatic Analysis Notebook | ShiLab
---'''
introduction = '''## This is a Jupyter Notebook based on R kernel.'''


def generate_EBEN_notebook(job_dir, input_x, input_y):
    load_library = '''\
# load library
library('EBEN')
library('r2d3')'''

    load_params='''\
nFolds <- 5
max_percentages_miss_val <- 0.2
seed <- 28213
set.seed(seed)'''

    load_data = '''\
# load data
workspace <- './'
x_filename <- '{0}'
y_filename <- '{1}'

x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names=FALSE,
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
y <- as.matrix(y)'''.format(input_x, input_y)

    preprocessing='''\
# Filter the miRNA data with more than 20% missing data
x_filtered <- NULL
x_filtered_colnames <- NULL
criteria <- trunc(nrow(x) * (1 - max_percentages_miss_val))
for (i in 1:ncol(x)) {
  if (sum(as.numeric(x[, i]) != 0) > criteria) {
    x_filtered <- cbind(x_filtered, x[, i])
    x_filtered_colnames<-c(x_filtered_colnames, colnames(x)[i])
  }
}
colnames(x_filtered)<-x_filtered_colnames
# colnames of x_filtered is same with x

# Quantile normalization
x_filtered_normed <- x_filtered
for (sl in 1:ncol(x_filtered_normed)) {
  mat = matrix(as.numeric(x_filtered_normed[, sl]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (nrow(x_filtered_normed) + 1))
  x_filtered_normed[, sl] = mat
}

x_preprocessed <- x_filtered_normed
rm(x_filtered, x_filtered_normed, sl, mat)'''

    main_effect='''\
# Main effect estimated using EBEN
CV = EBelasticNet.GaussianCV(x_preprocessed, y, nFolds = nFolds, Epis = "no")
Blup1 = EBelasticNet.Gaussian(
  x_preprocessed,
  y,
  lambda = CV$Lambda_optimal,
  alpha = CV$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_main_sig = Blup1$weight[which(Blup1$weight[, 6] <= 0.05), ]'''

    substract_main_effect='''\
# Substract the main effect
index_main <- Blup_main_sig[, 1]
effect_main <- Blup_main_sig[, 3]
y_new <- as.matrix(y) - x_preprocessed[, index_main] %*% (as.matrix(effect_main))'''

    epis_effect='''\
# Epistatic effect estimated using EBEN. This step may need a long time.
CV_epis = EBelasticNet.GaussianCV(x_preprocessed, y_new, nFolds = nFolds, Epis = "yes")
Blup_epis = EBelasticNet.Gaussian(
  x_preprocessed,
  y_new,
  lambda =  CV_epis$Lambda_optimal,
  alpha = CV_epis$Alpha_optimal,
  Epis = "yes",
  verbose = 0
)
Blup_epis_sig = Blup_epis$weight[which(Blup_epis$weight[, 6] <= 0.05), ]'''

    final_run='''\
# Final run
main_epi_sig_id = rbind(Blup_main_sig[, 1:2], Blup_epis_sig[, 1:2])

x_sig <- NULL
for (i in 1:nrow(main_epi_sig_id)) {
  if (main_epi_sig_id[i, 1] == main_epi_sig_id[i, 2]) {
    x_sig <- cbind(x_sig, x_preprocessed[, main_epi_sig_id[i, 1]])
  }
  if (main_epi_sig_id[i, 1] != main_epi_sig_id[i, 2]) {
    col <- x_preprocessed[, main_epi_sig_id[i, 1]] * x_preprocessed[, main_epi_sig_id[i, 2]]
    x_sig <- cbind(x_sig, col)
  }
}

# Quantile normalization 
x_sig_qnormed <- x_sig
for (sl in 1:ncol(x_sig_qnormed)) {
  mat = matrix(as.numeric(x_sig_qnormed[, sl]), 1)
  mat = t(apply(mat, 1, rank, ties.method = "average"))
  mat = qnorm(mat / (nrow(x_sig_qnormed) + 1))
  x_sig_qnormed[, sl] = mat
}
rm(x_sig, sl, mat)

CV_full = EBelasticNet.GaussianCV(x_sig_qnormed, y, nFolds = nFolds, Epis = "no")
Blup_full = EBelasticNet.Gaussian(
  x_sig_qnormed,
  y,
  lambda =  CV_full$Lambda_optimal,
  alpha = CV_full$Alpha_optimal,
  Epis = "no",
  verbose = 0
)
Blup_full_sig =  Blup_full$weight[which(Blup_full$weight[, 6] <= 0.05),]
Blup_full_sig[,1:2] <- main_epi_sig_id[Blup_full_sig[,1],1:2]

main_result <- NULL
epsi_result <- NULL
for (i in 1:nrow(Blup_full_sig)) {
  if (Blup_full_sig[i, 1] == Blup_full_sig[i, 2]) {
    main_result <- rbind(main_result, c(colnames(x_preprocessed)[Blup_full_sig[i, 1]],Blup_full_sig[i,3:6]))
  }
  if (Blup_full_sig[i, 1] != Blup_full_sig[i, 2]) {
    epsi_result <- rbind(epsi_result, c(colnames(x_preprocessed)[Blup_full_sig[i, 1]],colnames(x_preprocessed)[Blup_full_sig[i, 2]],Blup_full_sig[i,3:6]))
  }
}'''

    show_main_result='''\
# show head of main results
colnames(main_result)<- c('feature','coefficent value','posterior variance','t-value','p-value')
head(main_result)'''

    show_epis_result='''\
# show head of epis results
colnames(epsi_result)<- c('feature1','feature2','coefficent value','posterior variance','t-value','p-value')
head(epsi_result)'''

    vis_circle_network='''\
# generate json
# get all epsitasis nodes (unique)
epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
epsi_nodes <- unique(epsi_nodes)
json_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  f2 <- matrix(epsi_result[epsi_result[, 1] == f1, ],ncol=6)
  f2[,2]<-sprintf('"epis.%s"', f2[,2])
  element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
  json_str <- c(json_str,element)
}
json_str<-sprintf('[%s]',paste(json_str, collapse=',' ))
# circle network
r2d3(data=json_str, script = "vis_CN.js", css = "vis_CN.css")'''

    vis_adjacent_matrix='''\
# for adjacent matrix
epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
epsi_nodes <- unique(epsi_nodes)
nodes_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  element<- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
  nodes_str <- c(nodes_str,element)
}
nodes_str<-sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
link_str<-NULL
for(i in 1:nrow(epsi_result)){
  source_index<- match(epsi_result[i,1], epsi_nodes)
  target_index<- match(epsi_result[i,2], epsi_nodes)
  coff<-as.numeric(epsi_result[i,3])
  element<-sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
  link_str <- c(link_str,element)
}

link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
am_json<-sprintf('{%s,%s}',nodes_str,link_str)
write(am_json,'am.json')
r2d3( d3_version = 4, script = "vis_AM.js", css = "vis_AM.css", dependencies = "d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(preprocessing),
                   nbf.v4.new_code_cell(main_effect),
                   nbf.v4.new_code_cell(substract_main_effect),
                   nbf.v4.new_code_cell(epis_effect),
                   nbf.v4.new_code_cell(final_run),
                   nbf.v4.new_code_cell(show_main_result),
                   nbf.v4.new_code_cell(show_epis_result),
                   nbf.v4.new_code_cell(vis_circle_network),
                   nbf.v4.new_code_cell(vis_adjacent_matrix)
                   ]

    EBEN_nb = os.path.join(job_dir, 'EBEN_r_notebook.ipynb')
    with open(EBEN_nb, 'w') as f:
        nbf.write(nb, f)


def generate_LASSO_notebook(job_dir, input_x, input_y):
    load_library = '''\
    # load library
    library('BhGLM');
    library('Matrix');
    library('foreach');
    library('glmnet');
    source('cv.bh.R');
    library('r2d3')'''

    load_params = '''\
    # load parameters
    s0 <- 0.03;
    s1 <- 0.5;
    nFolds <- 5;
    seed <- 28213;
    set.seed(seed);'''

    load_data = '''\
    # load data
    workspace <- './'
    x_filename <- '{0}'
    y_filename <- '{1}'

    x <- read.table(
      file = file.path(workspace, x_filename),
      header = TRUE,
      check.names = FALSE,
      row.names = 1
    )
    sprintf('Geno size: (%d, %d)', nrow(x), ncol(x))
    y <- read.table(
      file = file.path(workspace, y_filename),
      header = TRUE,
      check.names = FALSE,
      row.names = 1
    )
    sprintf('Pheno size: (%d, %d)', nrow(y), ncol(y))

    features <- as.matrix(x);
    colnames(features) <- seq(1, ncol(features));
    pheno <- as.matrix(y);

    geno_stand <- scale(features);
    new_y <- scale(pheno);
    new_y_in <- new_y[, 1, drop = F];
    '''.format(input_x, input_y)

    main_effect = '''\
    # Main effect-single locus:
    sig_index <- which(abs(t(new_y_in) %*% geno_stand/(nrow(geno_stand)-1)) > 0.20);
    sig_main <- sig_index;'''

    epis_effect = '''\
    #Epistasis effect-single locus:
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
      if(length(grep("\\\*",res[i,1])) == 0){
        tmp1 = features[,(as.numeric(res[i,1])),drop=F];
        colnames(tmp1) <- res[i,1];
        new_matrix <-cbind(new_matrix,tmp1);
      }
      if(length(grep("\\\*",res[i,1])) == 1){
        indexes <- strsplit(res[i,1],"\\\*");
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
    main_index <- setdiff(1:nrow(Blup_estimate),grep("\\\*",rownames(Blup_estimate)));
    epi_index <- grep("\\\*",rownames(Blup_estimate))
    output_main <- matrix("NA",length(main_index),5);
    output_epi <- matrix("NA",length(epi_index),6);
    output_main[,1] <- matrix(rownames(Blup_estimate),ncol=1)[main_index,,drop=F];
    output_main[,2] <- Blup_estimate[main_index,1,drop=F]
    epi_ID <- matrix(rownames(Blup_estimate),ncol=1)[epi_index,,drop=F];
    output_epi[,1:2] <- matrix(unlist(strsplit(epi_ID,"\\\*")),ncol=2);
    output_epi[,3] <- Blup_estimate[epi_index,1,drop=F];
    colnames(output_main) <- c("feature", "coefficent value", "posterior variance", "t-value","p-value");
    colnames(output_epi) <- c("feature1","feature2", "coefficent value", "posterior variance", "t-value","p-value");
    output_main[, 1] <- colnames(x)[as.integer(output_main[, 1])]
    output_epi[, 1] <- colnames(x)[as.integer(output_epi[, 1])]
    output_epi[, 2] <- colnames(x)[as.integer(output_epi[, 2])]'''

    # for data visualization
    visu_cn = '''\
    # generate json
    # get all epsitasis nodes (unique)
    epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
    epsi_nodes <- unique(epsi_nodes)
    json_str<-NULL
    for (i in 1:length(epsi_nodes)) {
      f1 <- epsi_nodes[i]
      f2 <- matrix(epsi_result[epsi_result[, 1] == f1, ], ncol=6)
      f2[,2] <- sprintf('"epis.%s"', f2[,2])
      element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
      json_str <- c(json_str,element)
    }
    json_str <- sprintf('[%s]',paste(json_str, collapse=',' ))
    # circle network
    r2d3(data=json_str, script = "vis_CN.js", css = "vis_CN.css")'''

    visu_am = '''\
    # For adjacent matrix
    epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
    epsi_nodes <- unique(epsi_nodes)
    nodes_str<-NULL
    for (i in 1:length(epsi_nodes)) {
      f1 <- epsi_nodes[i]
      element<- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
      nodes_str <- c(nodes_str,element)
    }
    nodes_str<-sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
    link_str<-NULL
    for(i in 1:nrow(epsi_result)){
      source_index<- match(epsi_result[i,1], epsi_nodes)
      target_index<- match(epsi_result[i,2], epsi_nodes)
      coff<-as.numeric(epsi_result[i,3])
      element<-sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
      link_str <- c(link_str,element)
    }

    link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
    am_json<-sprintf('{%s,%s}',nodes_str,link_str)
    write(am_json,'am.json')
    r2d3( d3_version = 4, script = "vis_AM.js", css = "vis_AM.css", dependencies = "d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(main_effect),
                   nbf.v4.new_code_cell(epis_effect),
                   nbf.v4.new_code_cell(visu_cn),
                   nbf.v4.new_code_cell(visu_am)
                   ]

    LASSO_nb = os.path.join(job_dir, 'LASSO_r_notebook.ipynb')
    with open(LASSO_nb, 'w') as f:
        nbf.write(nb, f)
    pass

def generate_ssLASSO_notebook(job_dir, input_x, input_y):
    load_library = '''\
# load library
library('BhGLM');
library('Matrix');
library('foreach');
library('glmnet');
source('cv.bh.R');
library('r2d3')'''

    load_params = '''\
# load parameters
s0 <- 0.03;
s1 <- 0.5;
nFolds <- 5;
seed <- 28213;
set.seed(seed);'''

    load_data = '''\
# load data
workspace <- './'
x_filename <- '{0}'
y_filename <- '{1}'

x <- read.table(
  file = file.path(workspace, x_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('Geno size: (%d, %d)', nrow(x), ncol(x))
y <- read.table(
  file = file.path(workspace, y_filename),
  header = TRUE,
  check.names = FALSE,
  row.names = 1
)
sprintf('Pheno size: (%d, %d)', nrow(y), ncol(y))

features <- as.matrix(x);
colnames(features) <- seq(1, ncol(features));
pheno <- as.matrix(y);

geno_stand <- scale(features);
new_y <- scale(pheno);
new_y_in <- new_y[, 1, drop = F];
'''.format(input_x, input_y)

    main_effect = '''\
# Main effect-single locus:
sig_index <- which(abs(t(new_y_in) %*% geno_stand/(nrow(geno_stand)-1)) > 0.20);
sig_main <- sig_index;'''

    epis_effect = '''\
#Epistasis effect-single locus:
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
  if(length(grep("\\\*",res[i,1])) == 0){
    tmp1 = features[,(as.numeric(res[i,1])),drop=F];
    colnames(tmp1) <- res[i,1];
    new_matrix <-cbind(new_matrix,tmp1);
  }
  if(length(grep("\\\*",res[i,1])) == 1){
    indexes <- strsplit(res[i,1],"\\\*");
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
main_index <- setdiff(1:nrow(Blup_estimate),grep("\\\*",rownames(Blup_estimate)));
epi_index <- grep("\\\*",rownames(Blup_estimate))
output_main <- matrix("NA",length(main_index),5);
output_epi <- matrix("NA",length(epi_index),6);
output_main[,1] <- matrix(rownames(Blup_estimate),ncol=1)[main_index,,drop=F];
output_main[,2] <- Blup_estimate[main_index,1,drop=F]
epi_ID <- matrix(rownames(Blup_estimate),ncol=1)[epi_index,,drop=F];
output_epi[,1:2] <- matrix(unlist(strsplit(epi_ID,"\\\*")),ncol=2);
output_epi[,3] <- Blup_estimate[epi_index,1,drop=F];
colnames(output_main) <- c("feature", "coefficent value", "posterior variance", "t-value","p-value");
colnames(output_epi) <- c("feature1","feature2", "coefficent value", "posterior variance", "t-value","p-value");
output_main[, 1] <- colnames(x)[as.integer(output_main[, 1])]
output_epi[, 1] <- colnames(x)[as.integer(output_epi[, 1])]
output_epi[, 2] <- colnames(x)[as.integer(output_epi[, 2])]'''


    # for data visualization
    visu_cn = '''\
# generate json
# get all epsitasis nodes (unique)
epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
epsi_nodes <- unique(epsi_nodes)
json_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  f2 <- matrix(epsi_result[epsi_result[, 1] == f1, ], ncol=6)
  f2[,2] <- sprintf('"epis.%s"', f2[,2])
  element <- sprintf('{"name":"epis.%s","size":%d,"effects":[%s]}', f1, nrow(f2), paste(f2[,2], collapse=',' ))
  json_str <- c(json_str,element)
}
json_str <- sprintf('[%s]',paste(json_str, collapse=',' ))
# circle network
r2d3(data=json_str, script = "vis_CN.js", css = "vis_CN.css")'''

    visu_am = '''\
# For adjacent matrix
epsi_nodes <- c(epsi_result[, 1], epsi_result[, 2])
epsi_nodes <- unique(epsi_nodes)
nodes_str<-NULL
for (i in 1:length(epsi_nodes)) {
  f1 <- epsi_nodes[i]
  element<- sprintf('{"name":"%s","group":"Epistatic effect","rank": %d}',f1, 1)
  nodes_str <- c(nodes_str,element)
}
nodes_str<-sprintf('"nodes":[%s]',paste(nodes_str, collapse=',' ))
link_str<-NULL
for(i in 1:nrow(epsi_result)){
  source_index<- match(epsi_result[i,1], epsi_nodes)
  target_index<- match(epsi_result[i,2], epsi_nodes)
  coff<-as.numeric(epsi_result[i,3])
  element<-sprintf('{"source":%d, "target":%d, "coff": %f}',source_index-1, target_index-1, coff)
  link_str <- c(link_str,element)
}

link_str<-sprintf('"links":[%s]',paste(link_str, collapse=',' ))
am_json<-sprintf('{%s,%s}',nodes_str,link_str)
write(am_json,'am.json')
r2d3( d3_version = 4, script = "vis_AM.js", css = "vis_AM.css", dependencies = "d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(main_effect),
                   nbf.v4.new_code_cell(epis_effect),
                   nbf.v4.new_code_cell(visu_cn),
                   nbf.v4.new_code_cell(visu_am)
                   ]

    ssLasso_nb = os.path.join(job_dir, 'ssLASSO_r_notebook.ipynb')
    with open(ssLasso_nb, 'w') as f:
        nbf.write(nb, f)
