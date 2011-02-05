load.rdata.dir <- function(dir.name) {
	col.env <- new.env()
	invisible(
		lapply(
			dir(dir.name),
			function(file.name) load(paste(dir.name, file.name, sep = '/'),
			col.env)
		)
	)
	return(as.data.frame(as.list(col.env)))
}

discard.patchy.cols <- function(df, max.na.fraction) {
	n <- nrow(df)
	df <- df[, colSums(is.na(df)) < n * max.na.fraction]
	return(df)
}

# based on Hadley's na.roughfix thing from the mailing list
# but using distinct source and dest data frames
# (so we can impute missing values in test data using
# all the values in training ...)
na.roughhack <- function (dst, src = dst) {
	for(col_name in colnames(dst)) {
		if(!(col_name %in% colnames(src))) {
			stop('missing src for for dst col name: ', col_name)
		}
		dst_missing = is.na(dst[, col_name])
		src_missing = is.na(src[, col_name])
		if(is.numeric(dst[, col_name])) {
			dst[dst_missing, col_name] <- median.default(src[!src_missing, col_name])
		} else if (is.factor(dst[, col_name])) {
			freq = table(src[, col_name])
			dst[dst_missing, col_name] <- names(freq)[which.max(freq)]
		} else {
			stop("i only work for numeric or factor")
		}
	}
	dst
}

test.predictive.accuracy <- function(
	rdata.dir,
	max.na.fraction = 0.95,
	test.frac = 1.0 / 3.0,
	n.trees = 50,
	n.procs = 2,
	test.indices = NULL
) {
	library(randomForest)
	library(foreach)
	library(doMC)
	registerDoMC()

	train.df <- load.rdata.dir('rdata_train_base')
	train.df <- discard.patchy.cols(train.df, max.na.fraction)
	train.df <- na.roughfix(train.df)
	if (is.null(test.indices)) {
		test.size <- round(nrow(train.df) * test.frac)
		test.indices <- sample(nrow(train.df), test.size)
	}
	test.df <- train.df[test.indices, ]
	train.df <- train.df[-test.indices, ]

	rf <- foreach(
		trees.per.proc = rep(n.trees / n.procs, n.procs),
		.combine = combine,
		.packages = 'randomForest'
	) %dopar% {
		randomForest(
			Grant.Status ~.,
			train.df,
			ntree = trees.per.proc,
			do.trace = TRUE,
			importance = FALSE
		)
	}

	test.oob.predicted <- predict(rf, test.df, type = 'prob')
	r <- (as.numeric(test.df$Grant.Status) - 1) - test.oob.predicted[, 2]
	test.mse <-  mean(r^2)

	results <- list()
	results[['importance']] <- rf$importance[order(rf$importance), ]
	results[['test.mse']] <- test.mse
	return(results)
}
