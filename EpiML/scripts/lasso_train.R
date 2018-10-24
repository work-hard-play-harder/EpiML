library('glmnet')

args <- commandArgs(trailingOnly = TRUE)
alpha <- args[1]
workspace = args[2]
x_filename = args[3]
y_filename = args[4]

cat(workspace,'\n')
cat(x_filename,'\n')
cat(y_filename,'\n')
cat(file.path(workspace, x_filename),'\n')
cat(file.path(workspace, y_filename),'\n')

x = read.csv(
  file = file.path(workspace, x_filename),
  header = TRUE,
  sep = ','
)
y = read.csv(
  file = file.path(workspace, y_filename),
  header = TRUE,
  sep = ','
)

# basic call
fit = glmnet(as.matrix(x),as.matrix(y), alpha = alpha)
save(fit, file = file.path(workspace, 'lasso.fit'))
# save plot
png(file = file.path(workspace, 'lasso.png'))
plot(fit, label = TRUE, xvar = 'lambda')
dev.off()

# save coefficients
coef = coef(fit, s = 0.1) # extract coefficients at a single value of lambda
write.csv(as.matrix(coef), file = file.path(workspace, 'coefficients.csv'))

cat('Done!')
