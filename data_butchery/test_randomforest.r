library(randomForest)



get_data = function(csv_file_name) {
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

	max_na_fraction = 0.95 # throw away cols that have more missing values than this fraction
	col_mask = colSums(is.na(traindat)) < (nrow(traindat) * max_na_fraction)
	print(paste('discarding', ncol(traindat) - sum(col_mask), 'of', ncol(traindat), 'variables due to missing value fraction exceeding', max_na_fraction))
	traindat <- traindat[, col_mask]
	print(paste('data has', ncol(traindat) * nrow(traindat), 'values,', sum(is.na(traindat)), 'of which are missing'))

	print('replacing missing values roughly and horribly')
	traindat.imputed <- na.roughfix(traindat)
	print('done')
	traindat.imputed
}

add_missing_cols = function(train, test) {
	n_test_rows = nrow(test)
	# firstly, drop any new cols that may have appeared in the test data
	res = test[, (colnames(test) %in% colnames(train))]

	train_cols = colnames(train)
	test_cols = colnames(res)
	for(a in train_cols) {
		a_missing = TRUE
		for(b in test_cols) {
			if (a == b) {
				a_missing = FALSE
				break
			}
		}
		if (a_missing) {
			# hack : this will die if there are more test rows than train rows but i dont care
			new_col = train[1:n_test_rows, a]
			prev_col_names = colnames(res)
			res = cbind(res, new_col)
			colnames(res) = c(prev_col_names, a)
			is.na(res[, a]) = TRUE
		}
	}
	res
}

remove_new_factor_values = function(train, test) {
	for(a in colnames(train)) {
		if(!is.factor(train[, a])) {
			if(is.factor(test[, a])) {
				stop('what the')
			}
			next
		}
		# if there are any levels in the test data
		# that didnt appear in the training data
		# we have to get rid of them
		train_levels = levels(train[, a])
		test_levels = levels(test[, a])
		unseen_levels = !(test_levels %in% train_levels)
		new_test_levels = test_levels
		new_test_levels[unseen_levels] = NA
		print(paste('factor name', a))
		print('then')
		print(test_levels)
		print('now')
		print(new_test_levels)
		print('train')
		print(train_levels)
		levels(test[, a]) = new_test_levels
		# kill me, do it do it nowwww
		test[, a] = factor(as.character(test[, a]), levels = levels(train[, a]))
		if(!all(levels(test[, a]) == levels(train[, a]))) {
			print(levels(test[, a]))
			print(levels(train[, a]))
			stop('i\'m here! kill me! kill me do it nowwww!')
		}
	# stop('haltlol')
	}
	for(a in colnames(test)) {
		if(is.factor(test[, a])) {
			if(!a %in% colnames(train)) {
				stop('test has a factor variable that train doesnt: ', a)
			}
			if(!is.factor(train[, a])) {
				stop('what the hell?!')
			}
		}
	}
	test
}

traindat = get_data('butchered_data.csv')
testdat = get_data('butchered_data_test.csv')
testdat = add_missing_cols(traindat, testdat)
testdat = remove_new_factor_values(traindat, testdat)
testdat <- na.roughfix(testdat)

rf <- randomForest(I.FAC.Grant.Status ~ ., traindat, ntree = 2, do.trace = TRUE, importance = TRUE)

predicted_class = predict(rf, testdat, type = 'prob')

print(predicted_class)

if (FALSE) {
	results = data.frame(response = testdat$I.FAC.Grant.Status, predicted = predicted_class[, 2])

	library(ROCR)
	pred <- prediction(results$predicted, results$response)
	perf <- performance(pred, measure = "tpr", x.measure = "fpr") 
	# perf <- performance(pred, "acc")
	# plot(perf, avg= "vertical")
	plot(perf, colorize = T)
}

# print(rf$importance)
