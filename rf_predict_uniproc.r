source('rf_predict.r')

test.predictive.accuracy.uniproc <- function(
	rdata_dir,
	selected_vars = NULL,
	max_na_fraction = 0.95,
	test_frac = 1.0 / 3.0,
	n_trees = 50,
	test_indices = NULL,
	draw_plots = FALSE
) {
	library(randomForest)

	train.df <- load.rdata.dir(rdata_dir, selected_vars)
	train.df <- discard.patchy.cols(train.df, max_na_fraction)
	train.df <- na.roughfix(train.df) # dodgy imputation step
	if (is.null(test_indices)) {
		test.size <- round(nrow(train.df) * test_frac)
		test_indices <- sample(nrow(train.df), test.size)
	}
	test.df <- train.df[test_indices, ]
	train.df <- train.df[-test_indices, ]

	rf <- randomForest(
		Grant.Status ~.,
		train.df,
		ntree = n_trees,
		do.trace = 10,
		importance = TRUE
	)
	imp <- importance(rf)
	if(draw_plots) {
		x11()
		plot(rf)

		x11()
		varImpPlot(rf, n.var = 50)

		x11()
		imp.mse <- sort(imp[, 1])
		plot(imp.mse)
		title('importance : mse')

		x11()
		imp.gini <- sort(imp[, 2])
		plot(imp.gini)
		title('importance : gini')
	}

	test.oob.predicted <- predict(rf, test.df, type = 'prob')
	r <- (as.numeric(test.df$Grant.Status) - 1) - test.oob.predicted[, 2]
	test.mse <- mean(r^2)
	# cat(paste('mse on test set:', test.mse, '\n'))

	results <- list()
	results[['importance.mse']] <- imp[, 1]
	results[['importance.gini']] <- imp[, 2]
	results[['test.mse']] <- test.mse
	return(results)
}
