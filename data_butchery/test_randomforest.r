
csv_file_name = 'butchered_data.csv'
# use first col as row names
data <- read.csv(csv_file_name, header = TRUE, row.names = 1)
is.na(data)[data == ""] <- TRUE # replace blank cells with NAs

# parse cols according to info encoded in col names
for (i in 1:ncol(data)) {
	name = colnames(data)[i]
	print(name)

	# get the first damn character of the bloody string
	dtype = strsplit(name, "\\.")[[1]][1]

	as.whatever = as.character
	if (dtype == "I") {
		as.whatever = as.integer
	} else if (dtype == "F") {
		as.whatever = as.numeric
	} else if (dtype == "S") {
		as.whatever = as.character
	} else {
		stop("unknown dtype: ", dtype)
	}
	
	# get the second damn token in the bloody string
	vartype = strsplit(name, "\\.")[[1]][2]

	factorise = FALSE
	if (vartype == "FAC") {
		factorise = TRUE
	}

	data[, i] <- as.whatever(as.character(data[, i]))
	if(factorise) {
		data[, i] <- as.factor(data[, i])
	}
}

traindat <- data



# hadley's suggested roughfix impl., stolen from the mailing list
# generalised to support distinct source and dest arrays
# this appears to be a little broken (it seems to destroy
# the factors in the data ...)

na.roughfix2 <- function (dst, src = dst) {
	res <- mapply(roughfix, dst, src)
	as.data.frame(res, row.names = seq_len(nrow(dst)))
}

roughfix <- function(dst, src) {
	missing.dst <- is.na(dst)
	missing.src <- is.na(src)
	if (!any(missing.dst)) return(dst)

	if (is.numeric(dst)) {
		dst[missing.dst] <- median.default(src[!missing.src])
	} else if (is.factor(dst)) {
		freq <- table(src)
		dst[missing.dst] <- names(freq)[which.max(freq)]
	} else {
		stop("na.roughfix only works for numeric or factor")
	}
	dst
}



library(randomForest)


max_na_fraction = 0.95 # throw away cols that have more missing values than this fraction
col_mask = colSums(is.na(traindat)) < (nrow(traindat) * max_na_fraction)
print(paste('discarding', ncol(traindat) - sum(col_mask), 'of', ncol(traindat), 'variables due to missing value fraction exceeding', max_na_fraction))
traindat <- traindat[, col_mask]
print(paste('data has', ncol(traindat) * nrow(traindat), 'values,', sum(is.na(traindat)), 'of which are missing'))

n = nrow(traindat)
training_weight = 2.0 / 3.0
indices = sample(2, n, replace = TRUE, prob = c(training_weight, 1.0 - training_weight))
training_mask = (indices == 1)
testing_mask = (indices == 2)

alldat = traindat
traindat = alldat[training_mask, ]
testdat = alldat[testing_mask, ]

print('replacing missing values roughly and horribly')
traindat.imputed <- na.roughfix(traindat)
print('done')


# run a short first pass of randomForest to estimate variable importance
# then discard a bunch of the seemingly less important variables
if (FALSE) {
	print('estimating variable importance')
	rf.filter <- randomForest(I.FAC.Grant.Status ~ ., traindat.imputed, ntree = 50, do.trace = TRUE, importance = TRUE)
	# arbitrarily use mean decrease accuracy as importance estimate
	z <- rf.filter$importance$MeanDecreaseAccuracy
	# XXX TODO Z ISNT GOING TO HAVE SAME COLS AS DATA FRAME AS IT EXCLUDES RESPONSE DERP DERP
	# get indices to order cols by importance
	ind <- order(z, decreasing = TRUE)
	# only keep the most important ones
	n_important_vars = 100
	unimportant_cols <- ind[-n_important_vars]
	print('done')
}


rf <- randomForest(I.FAC.Grant.Status ~ ., traindat.imputed, ntree = 500, do.trace = TRUE, importance = TRUE)

testdat.imputed <- na.roughfix(testdat)
predicted_class = predict(rf, testdat.imputed, type = 'prob')

results = data.frame(response = testdat$I.FAC.Grant.Status, predicted = predicted_class[, 2])

library(ROCR)
pred <- prediction(results$predicted, results$response)
perf <- performance(pred, measure = "tpr", x.measure = "fpr") 
# perf <- performance(pred, "acc")
# plot(perf, avg= "vertical")
plot(perf, colorize = T)


print(rf$importance)
