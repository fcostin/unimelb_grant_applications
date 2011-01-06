# anthony goldblum's (of kaggle) sample R code

load_unimelb_data = function(data) {
	# modify data in place so it's more understandable for prediction routines
	is.na(data)[data == ""] <- TRUE # replace blank cells with NAs

	personIDs<-c(27,42,57,72,87,102,117,132,147,162,177,192,207,222,237,252)
	nv0 <- c(personIDs+10,personIDs+11,personIDs+12,personIDs+13,personIDs+14,personIDs+9) #numerical values that should be 0
	nv <- c(1,8,10,12,14,16,18,20,22,24,26,nv0)  #numerical values
	for (i in 1:ncol(data)) {
		if (i %in% nv) {
			data[,i] <- as.numeric(as.character(data[,i]))
		} else if (i == 6 ) { #dates
			data[,i] <- as.Date(data[,i])
		} else {
			data[,i] <- as.factor(data[,i])
		}
	}
	return(data)
}

get_unimelb_data = function(csv_file_name) {
	cache_file_name <- paste(csv_file_name, 'cache', sep = '.')
	if (file.exists(cache_file_name)) {
		print(paste('loading', csv_file_name, 'from cache file'))
		return(read.csv(cache_file_name, header = TRUE))
	} else {
		print(paste('loading', csv_file_name))
		data <- read.csv(csv_file_name, header = TRUE)
		print('converting data to more reasonable format')
		nice_data <- load_unimelb_data(data)
		print('caching nicer data for next time ...')
		write.csv(nice_data, file = cache_file_name)
		return(nice_data)
	}
}

traindat <- get_unimelb_data('data/unimelb_training.csv')
testdat  <- get_unimelb_data('data/unimelb_test.csv')

# use randomForest to fill in missing values (ie most of the table)
library(randomForest)
print('using randomForest to impute missing values...')
traindat.imputed <- rfImpute(Grant.Status ~ ., traindat)
print('...done imputing.')



if(FALSE) {
	require('ROCR')

	logit.fit <- glm(
		Grant.Status ~ Number.of.Successful.Grant.1 + Number.of.Unsuccessful.Grant.1 + Grant.Application.ID,
		data = traindat,
		family = binomial(link = 'logit')
	)

	GLMPred <- predict(logit.fit,testdat,type = "response")

	print(GLMPred)
}
