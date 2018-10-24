
#*******************************************************************************

cv.bh <- function(object, nfolds = 10, foldid = NULL, ncv = 1, verbose = TRUE)
{
  start.time <- Sys.time()
  
  if (any(class(object) %in% "glm")) 
    out <- cv.bh.glm(object = object, nfolds = nfolds, foldid = foldid, ncv = ncv, verbose = verbose)
  
  if (any(class(object) %in% "coxph")) 
    out <- cv.bh.coxph(object = object, nfolds = nfolds, foldid = foldid, ncv = ncv, verbose = verbose)
  
  if (any(class(object) %in% "glmNet") | any(class(object) %in% "bmlasso")) 
    out <- cv.bh.lasso(object = object, nfolds = nfolds, foldid = foldid, ncv = ncv, verbose = verbose)
  
  if (any(class(object) %in% "polr")) 
    out <- cv.bh.polr(object = object, nfolds = nfolds, foldid = foldid, ncv = ncv, verbose = verbose)
  
  stop.time <- Sys.time()
  Time <- round(difftime(stop.time, start.time, units = "min"), 3)
  if(verbose) {
    cat("\n")
    cat("Cross-validation time:", Time, "minutes \n")
  }
  
  out
}

### for bglm, glm
cv.bh.glm <- function(object, nfolds = 10, foldid = NULL, ncv = 1, verbose = TRUE)
{  
  #  data.obj <- object$model
  #  x.obj <- as.matrix(data.obj[, -1, drop = FALSE])
  #  y.obj <- data.obj[, 1]
  #  n <- NROW(y.obj)
  
  x.obj <- model.matrix(object)
  if (colnames(x.obj)[1] == "(Intercept)") x.obj <- x.obj[, -1, drop = FALSE]
  y.obj <- object$y
  n <- NROW(y.obj)
  offset <- object$offset
  if (is.null(offset)) offset <- rep(0, n)
  
  out <- list()
  out$y.obs <- y.obj
  
  measures0 <- NULL
  y.fitted0 <- lp0 <- NULL
  fold <- foldid
  foldid0 <- NULL
  if (!is.null(foldid)) {
    fold <- as.matrix(foldid)
    nfolds <- max(foldid)
    ncv <- ncol(fold)
  }
  j <- 0
  
  if (nfolds > n) nfolds <- n
  if (nfolds == n) ncv <- 1
  
  for (k in 1:ncv) {
    
    y.fitted <- lp <- rep(NA, n)
    deviance <- NULL
    
    if (!is.null(fold)) foldid <- fold[, k]
    else foldid <- sample(rep(seq(nfolds), length = n)) #sample(1:nfolds, size = n, replace = TRUE)
    
    for (i in 1:nfolds) {
      subset1 <- rep(TRUE, n)
      omit <- which(foldid == i)
      subset1[omit] <- FALSE
      if (!is.null(object$prior.sd)) fit <- update(object, subset = subset1, verbose = FALSE)
      else fit <- update(object, subset = subset1) 
      dd <- predict.bh(fit, new.x = x.obj[omit, , drop = FALSE], new.y = y.obj[omit], offset = offset[omit])
      y.fitted[omit] <- dd$y.fitted
      lp[omit] <- dd$lp  #- (names(fit$coefficients)[1] == "(Intercept)") * fit$coefficients[1]
      deviance <- c(deviance, dd$measures["deviance"])
      
      if (verbose) {
        J <- nfolds * ncv
        j <- j + 1
        pre <- rep("\b", J)
        cat(pre, j, "/", J, sep = "")
        flush.console()
      }
    }
    
    deviance <- sum(deviance)
    mse <- mean((y.obj - y.fitted)^2, na.rm = TRUE)
    mae <- mean(abs(y.obj - y.fitted), na.rm = TRUE)
    measures <- list(deviance = deviance, mse = mse, mae = mae)
    if (object$family[[1]] == "gaussian") {
      R2 <- (var(y.obj) - mse)/var(y.obj)
      measures <- list(deviance = deviance, mse = mse, R2 = R2)
    }
    if (object$family[[1]] == "binomial") {
      auc <- roc(y.obj, y.fitted, plot = FALSE)$AUC
      misclassification <- mean(abs(y.obj - y.fitted) > 0.5, na.rm = T)
      measures <- list(deviance = deviance, auc = auc, mse = mse, misclassification = misclassification)
    }
    
    measures <- unlist(measures)
    
    measures0 <- rbind(measures0, measures)
    lp0 <- cbind(lp0, lp)
    y.fitted0 <- cbind(y.fitted0, y.fitted)
    foldid0 <- cbind(foldid0, foldid)
    
  }
  
  if (!any(is.na(y.fitted0))) out$y.fitted <- rowMeans(y.fitted0)
  if (nrow(measures0) == 1) out$measures <- colMeans(measures0)
  else {
    out$measures <- rbind(colMeans(measures0), apply(measures0, 2, sd))
    rownames(out$measures) <- c("mean", "sd")
  }
  out$lp <- rowMeans(lp0)
  out$foldid <- foldid0
  
  if (ncv > 1){
    rownames(measures0) <- NULL
    out$detail <- list(measures = measures0, lp = lp0)
  }
  
  out
}

# for bcoxph, coxph
cv.bh.coxph <- function(object, nfolds = 10, foldid = NULL, ncv = 1, verbose = TRUE)
{
  require(survival)
  x.obj <- model.matrix(object)
  y.obj <- object$y
  n <- NROW(y.obj)
  
  out <- list()
  out$y.obs <- y.obj
  
  measures0 <- lp0 <- NULL
  fold <- foldid
  foldid0 <- NULL
  if (!is.null(foldid)) {
    fold <- as.matrix(foldid)
    nfolds <- max(foldid)
    ncv <- ncol(fold)
  }
  j <- 0
  
  if (nfolds > n) nfolds <- n
  if (nfolds == n) ncv <- 1
  
  for (k in 1:ncv) {
    
    lp <- rep(NA, n)
    pl <- NULL
    
    if (!is.null(fold)) foldid <- fold[, k]
    else foldid <- sample(rep(seq(nfolds), length = n)) 
    
    for (i in 1:nfolds) {
      subset1 <- rep(TRUE, n)
      omit <- which(foldid == i)
      subset1[omit] <- FALSE
      if (!is.null(object$prior.sd)) fit <- update(object, subset = subset1, verbose = FALSE)
      else fit <- update(object, subset = subset1) 
      xb <- x.obj %*% fit$coefficients
      dd1 <- coxph(y.obj ~ xb, init = 1, control = coxph.control(iter.max=1), method = object$method)
      dd2 <- coxph(y.obj ~ xb, init = 1, control = coxph.control(iter.max=1), subset = subset1, method = object$method)
      lp[omit] <- xb[omit]        
      pl <- c(pl, dd1$loglik[1] - dd2$loglik[1])
      
      if (verbose) {
        J <- nfolds * ncv
        j <- j + 1
        pre <- rep("\b", J)
        cat(pre, j, "/", J, sep = "")
        flush.console()
      }
    }
    
    pl <- sum(pl)
    cindex <- Cindex(y.obj, lp)$cindex
    ppl <- coxph(y.obj ~ lp, init = 1, control = coxph.control(iter.max=1), method = "breslow")$loglik[1]
    measures <- list(CVPL = pl, pl = ppl, Cindex = cindex)
    
    measures <- unlist(measures)
    
    measures0 <- rbind(measures0, measures)
    lp0 <- cbind(lp0, lp)
    foldid0 <- cbind(foldid0, foldid)
    
  }
  
  if (nrow(measures0) == 1) out$measures <- colMeans(measures0)
  else {
    out$measures <- rbind(colMeans(measures0), apply(measures0, 2, sd))
    rownames(out$measures) <- c("mean", "sd")
  }
  out$lp <- rowMeans(lp0)
  out$foldid <- foldid0
  
  if (ncv > 1){
    rownames(measures0) <- NULL
    out$detail <- list(measures = measures0, lp = lp0)
  }
  
  out
}

# for lasso, mlasso
cv.bh.lasso <- function(object, nfolds = 10, foldid = NULL, ncv = 1, verbose = TRUE)
{ 
  require(glmnet)
  x.obj <- object$x
  y.obj <- object$y
  n <- NROW(y.obj)
  offset <- object$offset
  if (is.null(offset)) offset <- rep(0, n)
  
  out <- list()
  out$y.obs <- y.obj
  
  measures0 <- NULL
  y.fitted0 <- lp0 <- NULL
  fold <- foldid
  foldid0 <- NULL
  if (!is.null(foldid)) {
    fold <- as.matrix(foldid)
    nfolds <- max(foldid)
    ncv <- ncol(fold)
  }
  j <- 0
  
  if (nfolds > n) nfolds <- n
  if (nfolds == n) ncv <- 1
  
  for (k in 1:ncv) {
    
    y.fitted <- lp <- rep(NA, n)
    deviance <- pl <- NULL
    
    if (!is.null(fold)) foldid <- fold[, k]
    else foldid <- sample(rep(seq(nfolds), length = n)) #sample(1:nfolds, size = n, replace = TRUE)
    
    for (i in 1:nfolds) {
      subset1 <- rep(TRUE, n)
      omit <- which(foldid == i)
      subset1[omit] <- FALSE
      if (any(class(object) %in% "glmNet"))
        fit <- update(object, x = x.obj[-omit, ], y = y.obj[-omit], weights = object$weights[-omit], offset = object$offset[-omit],
                      lambda = object$lambda, verbose = FALSE)
      if (any(class(object) %in% "bmlasso"))
        fit <- update(object, x = x.obj[-omit, ], y = y.obj[-omit], weights = object$weights[-omit], offset = object$offset[-omit], 
                      init = object$beta, verbose = FALSE)  
      family <- object$family
      if (family %in% c("gaussian", "binomial", "poisson")) {
        dd <- predict.bh(fit, new.x = x.obj[omit, , drop = FALSE], new.y = y.obj[omit], offset = offset[omit])
        y.fitted[omit] <- dd$y.fitted
        lp[omit] <- dd$lp  
        deviance <- c(deviance, dd$measures["deviance"])
      }
      if (family == "cox") {
        xb <- x.obj %*% fit$coefficients 
        dd1 <- coxph(y.obj ~ xb, init = 1, control = coxph.control(iter.max=1), method = "breslow")
        dd2 <- coxph(y.obj ~ xb, init = 1, control = coxph.control(iter.max=1), subset = subset1, method = "breslow")
        lp[omit] <- xb[omit]
        pl <- c(pl, dd1$loglik[1] - dd2$loglik[1])
      }
      
      if (verbose) {
        J <- nfolds * ncv
        j <- j + 1
        pre <- rep("\b", J)
        cat(pre, j, "/", J, sep = "")
        flush.console()
      }
    }
    
    if (any(class(object) %in% "GLM")) {
      deviance <- sum(deviance)
      mse <- mean((y.obj - y.fitted)^2, na.rm = TRUE)
      measures <- list(deviance = deviance, mse = mse)
      if (object$family[[1]] == "gaussian") {
        R2 <- (var(y.obj) - mse)/var(y.obj)
        measures <- list(deviance = deviance, mse = mse, R2 = R2)
      }
      if (object$family[[1]] == "binomial") {
        auc <- roc(y.obj, y.fitted, plot = FALSE)$AUC
        misclassification <- mean(abs(y.obj - y.fitted) > 0.5, na.rm = T)
        measures <- list(deviance = deviance, auc = auc, mse = mse,  
                         misclassification = misclassification)
      }
    }
    if (any(class(object) %in% "COXPH")) {
      pl <- sum(pl)
      cindex <- Cindex(y.obj, lp)$cindex
      ppl <- coxph(y.obj ~ lp, init = 1, control = coxph.control(iter.max=1), method = "breslow")$loglik[1]
      measures <- list(CVPL = pl, pl = ppl, Cindex = cindex)
    }
    measures <- unlist(measures)
    
    measures0 <- rbind(measures0, measures)
    lp0 <- cbind(lp0, lp)
    y.fitted0 <- cbind(y.fitted0, y.fitted)
    foldid0 <- cbind(foldid0, foldid)
    
  }
  
  if (!any(is.na(y.fitted0))) out$y.fitted <- rowMeans(y.fitted0)
  if (nrow(measures0) == 1) out$measures <- colMeans(measures0)
  else {
    out$measures <- rbind(colMeans(measures0), apply(measures0, 2, sd))
    rownames(out$measures) <- c("mean", "sd")
  }
  out$lp <- rowMeans(lp0)
  out$foldid <- foldid0
  
  if (ncv > 1){
    rownames(measures0) <- NULL
    out$detail <- list(measures = measures0, lp = lp0)
  }
  
  out
}

### for bpolr, polr
cv.bh.polr <- function(object, nfolds = 10, foldid = NULL, ncv = 1, verbose = TRUE)
{ 
  library(MASS) 
  data <- object$model
  x.obj <- data[, -1, drop = FALSE]
  y.obj <- data[, 1]
  n <- NROW(y.obj)
  offset <- object$offset
  if (is.null(offset)) offset <- rep(0, n)
  
  out <- list()
  out$y.obs <- y.obj
  
  measures0 <- NULL
  y.fitted0 <- list()
  lp0 <- NULL
  fold <- foldid
  foldid0 <- NULL
  if (!is.null(foldid)) {
    fold <- as.matrix(foldid)
    nfolds <- max(foldid)
    ncv <- ncol(fold)
  }
  j <- 0
  
  if (nfolds > n) nfolds <- n
  if (nfolds == n) ncv <- 1
  
  for (k in 1:ncv) {
    
    y.fitted <- array(0, c(n, length(levels(y.obj))))
    lp <- rep(NA, n)
    deviance <- NULL
    
    if (!is.null(fold)) foldid <- fold[, k]
    else foldid <- sample(rep(seq(nfolds), length = n)) #sample(1:nfolds, size = n, replace = TRUE)
    
    for (i in 1:nfolds) {
      subset1 <- rep(TRUE, n)
      omit <- which(foldid == i)
      subset1[omit] <- FALSE
      if (!is.null(object$prior.scale)) fit <- update(object, subset=subset1, Hess=FALSE, verbose=FALSE)
      else fit <- update(object, subset=subset1, Hess=FALSE) 
      dd <- predict.bh(fit, new.x=x.obj[omit, , drop=FALSE], new.y=y.obj[omit], offset=offset[omit])
      y.fitted[omit, ] <- dd$y.fitted
      lp[omit] <- dd$lp  
      
      if (verbose) {
        J <- nfolds * ncv
        j <- j + 1
        pre <- rep("\b", J)
        cat(pre, j, "/", J, sep = "")
        flush.console()
      }
    }
    
    #    deviance <- polr(y.obj ~ offset(lp))$deviance
    auc <- mse <- misclassification <- 0
    y.level <- levels(y.obj)
    for(c in 1:NCOL(y.fitted)) {
      y1 <- ifelse(y.obj == y.level[c], 1, 0)
      auc <- auc + roc(y1, y.fitted[, c], plot = FALSE)$AUC
      misclassification <- misclassification + mean(abs(y1 - y.fitted[, c]) > 0.5, na.rm = TRUE)
      mse <- mse + mean((y1 - y.fitted[, c])^2, na.rm = TRUE)
    }
    auc <- auc/NCOL(y.fitted)
    mse <- mse/NCOL(y.fitted)
    misclassification <- misclassification/NCOL(y.fitted)
    L <- rep(NA, NROW(y.fitted))
    for (ii in 1:NROW(y.fitted)){
      y2 <- rep(0, NCOL(y.fitted))
      for (kk in 1:NCOL(y.fitted)) y2[kk] <- ifelse(y.obj[ii]==y.level[kk], 1, 0)
      L[ii] <- sum(y2*y.fitted[ii,])
    }
    L <- ifelse(L==0, 1e-04, L)
    deviance <- -2 * sum(log(L))
    
    measures <- list(deviance = deviance, auc = auc, mse = mse, misclassification = misclassification)
    measures <- unlist(measures)
    
    measures0 <- rbind(measures0, measures)
    lp0 <- cbind(lp0, lp)
    y.fitted0[[k]] <- y.fitted
    foldid0 <- cbind(foldid0, foldid)
    
  }
  
  out$y.fitted <- array(0, c(n, length(levels(y.obj))))
  for (k in 1:ncv) out$y.fitted <- out$y.fitted + y.fitted0[[k]]/ncv 
  if (nrow(measures0) == 1) out$measures <- colMeans(measures0)
  else {
    out$measures <- rbind(colMeans(measures0), apply(measures0, 2, sd))
    rownames(out$measures) <- c("mean", "sd")
  }
  out$lp <- rowMeans(lp0)
  out$foldid <- foldid0
  
  if (ncv > 1){
    rownames(measures0) <- NULL
    out$detail <- list(measures = measures0, lp = lp0)
  }
  
  out
}


#*******************************************************************************



