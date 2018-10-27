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
---\n'''
introduction = '''## This is a Jupyter Notebook based on R kernel.'''


def generate_ssLasso_notebook(job_dir, input_x, input_y, s0=0.03, s1=0.5, nFolds=5, seed=28213):
    load_library = '''\
    # load library
    library("BhGLM");
    library("Matrix");
    library("foreach");
    library("glmnet");
    source("cv.bh.R");'''

    load_data = '''\
    # load data
    x_filename <- {0}
    y_filename <- {1}

    x <- read.table(
        file= x_filename,
        header=TRUE,
        check.names = FALSE,
                      row.names = 1
    )
    sprintf('Geno size: (%d, %d)', nrow(x), ncol(x))
    y <- read.table(
        file= y_filename,
        header=TRUE,
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

    load_params = '''\
    # load parameters
    s0 <- {0};
    s1 <- {1};
    nFolds <- {2};
    seed <- {3};
    set.seed(seed);'''.format(s0, s1, nFolds, seed)

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

    write_table = '''\
    # write table
    write.table(
      output_main,
      file = 'main_result.txt',
      quote = F,
      sep = "\\t",
      col.names = T,
      row.names = F
    )
    write.table(
      output_epi,
      file = 'epis_result.txt',
      quote = F,
      sep = "\\t",
      col.names = T,
      row.names = F
    )'''

    # for data visualization
    load_r2d3 = '''\
    library(r2d3)'''
    visu_cn = '''\
    json<-'[{"name": "miRNA.epis.X33070_chrI_33070_A_T", "size": 1, "effects": ["miRNA.epis.X9509901_chrXIV_262265_G_A"]}, {"name": "miRNA.epis.X361238_chrII_131020_A_G", "size": 1, "effects": ["miRNA.epis.X3662991_chrVI_194162_A_G"]}, {"name": "miRNA.epis.X446164_chrII_215946_G_C", "size": 1, "effects": ["miRNA.epis.X3926164_chrVII_187174_A_G"]}, {"name": "miRNA.epis.X570523_chrII_340305_A_G", "size": 1, "effects": ["miRNA.epis.X4859981_chrVIII_30051_C_T"]}, {"name": "miRNA.epis.X759011_chrII_528793_T_C", "size": 1, "effects": ["miRNA.epis.X8953451_chrXIII_630246_T_A"]}, {"name": "miRNA.epis.X776950_chrII_546732_C_G", "size": 1, "effects": ["miRNA.epis.X2081015_chrIV_720993_C_G"]}, {"name": "miRNA.epis.X1640881_chrIV_280859_C_T", "size": 1, "effects": ["miRNA.epis.X6971854_chrXI_393642_A_G"]}, {"name": "miRNA.epis.X1662633_chrIV_302611_G_A", "size": 1, "effects": ["miRNA.epis.X7503296_chrXII_258268_G_A"]}, {"name": "miRNA.epis.X1977864_chrIV_617842_C_T", "size": 1, "effects": ["miRNA.epis.X10124638_chrXV_92669_T_C"]}, {"name": "miRNA.epis.X2301085_chrIV_941063_T_C", "size": 1, "effects": ["miRNA.epis.X3415134_chrV_523179_A_G"]}, {"name": "miRNA.epis.X2948126_chrV_56171_A_G", "size": 1, "effects": ["miRNA.epis.X11626574_chrXVI_503314_A_G"]}, {"name": "miRNA.epis.X3136068_chrV_244113_G_A", "size": 1, "effects": ["miRNA.epis.X6140249_chrX_307788_T_C"]}, {"name": "miRNA.epis.X3252364_chrV_360409_C_A", "size": 1, "effects": ["miRNA.epis.X8702982_chrXIII_379777_A_G"]}, {"name": "miRNA.epis.X3511784_chrVI_42955_A_G", "size": 2, "effects": ["miRNA.epis.X6538042_chrX_705581_A_G", "miRNA.epis.X8093870_chrXII_848842_A_G"]}, {"name": "miRNA.epis.X3841157_chrVII_102167_G_A", "size": 1, "effects": ["miRNA.epis.X10635015_chrXV_603046_C_T"]}, {"name": "miRNA.epis.X3926164_chrVII_187174_A_G", "size": 1, "effects": ["miRNA.epis.X8053217_chrXII_808189_T_C"]}, {"name": "miRNA.epis.X5550381_chrIX_157808_T_G", "size": 1, "effects": ["miRNA.epis.X6171890_chrX_339429_T_C"]}, {"name": "miRNA.epis.X6005118_chrX_172657_A_T", "size": 1, "effects": ["miRNA.epis.X7558993_chrXII_313965_G_A"]}, {"name": "miRNA.epis.X6760046_chrXI_181834_T_C", "size": 1, "effects": ["miRNA.epis.X6992548_chrXI_414336_C_T"]}, {"name": "miRNA.epis.X7130105_chrXI_551893_C_T", "size": 1, "effects": ["miRNA.epis.X7802889_chrXII_557861_C_G"]}, {"name": "miRNA.epis.X7802889_chrXII_557861_C_G", "size": 1, "effects": ["miRNA.epis.X10518104_chrXV_486135_A_G"]}, {"name": "miRNA.epis.X8465411_chrXIII_142206_T_G", "size": 1, "effects": ["miRNA.epis.X10178520_chrXV_146551_T_A"]}, {"name": "miRNA.epis.X8551719_chrXIII_228514_G_A", "size": 1, "effects": ["miRNA.epis.X9279748_chrXIV_32112_G_A"]}, {"name": "miRNA.epis.X10235916_chrXV_203947_T_C", "size": 1, "effects": ["miRNA.epis.X11664756_chrXVI_541496_T_G"]}, {"name": "miRNA.epis.X9509901_chrXIV_262265_G_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X3662991_chrVI_194162_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X4859981_chrVIII_30051_C_T", "size": 0, "effects": []}, {"name": "miRNA.epis.X8953451_chrXIII_630246_T_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X2081015_chrIV_720993_C_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X6971854_chrXI_393642_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X7503296_chrXII_258268_G_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X10124638_chrXV_92669_T_C", "size": 0, "effects": []}, {"name": "miRNA.epis.X3415134_chrV_523179_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X11626574_chrXVI_503314_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X6140249_chrX_307788_T_C", "size": 0, "effects": []}, {"name": "miRNA.epis.X8702982_chrXIII_379777_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X6538042_chrX_705581_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X8093870_chrXII_848842_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X10635015_chrXV_603046_C_T", "size": 0, "effects": []}, {"name": "miRNA.epis.X8053217_chrXII_808189_T_C", "size": 0, "effects": []}, {"name": "miRNA.epis.X6171890_chrX_339429_T_C", "size": 0, "effects": []}, {"name": "miRNA.epis.X7558993_chrXII_313965_G_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X6992548_chrXI_414336_C_T", "size": 0, "effects": []}, {"name": "miRNA.epis.X10518104_chrXV_486135_A_G", "size": 0, "effects": []}, {"name": "miRNA.epis.X10178520_chrXV_146551_T_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X9279748_chrXIV_32112_G_A", "size": 0, "effects": []}, {"name": "miRNA.epis.X11664756_chrXVI_541496_T_G", "size": 0, "effects": []}]'
    r2d3(data=json, script = "vis_CN.js", css = "vis_CN.css")'''

    visu_am = '''\
    r2d3( d3_version = 4, script = "vis_AM.js", css = "vis_AM.css", dependencies = "d3-scale-chromatic.js")'''

    nb['cells'] = [nbf.v4.new_markdown_cell(title),
                   nbf.v4.new_markdown_cell(introduction),
                   nbf.v4.new_code_cell(load_library),
                   nbf.v4.new_code_cell(load_data),
                   nbf.v4.new_code_cell(load_params),
                   nbf.v4.new_code_cell(main_effect),
                   nbf.v4.new_code_cell(epis_effect),
                   nbf.v4.new_code_cell(write_table),
                   nbf.v4.new_code_cell(load_r2d3),
                   nbf.v4.new_code_cell(visu_cn),
                   nbf.v4.new_code_cell(visu_am)
                   ]

    ssLasso_nb = os.path.join(job_dir, 'ssLasso_r_notebook.ipynb')
    with open(ssLasso_nb, 'w') as f:
        nbf.write(nb, f)
