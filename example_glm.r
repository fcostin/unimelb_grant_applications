# anthony goldblum's (of kaggle) sample R code

traindat <- read.csv('unimelb_training.csv',header=TRUE)
testdat  <- read.csv('unimelb_test.csv',header=TRUE)

blank <- traindat == "" #find all blank cells 
is.na(traindat)[blank] <- TRUE #change them to NAs
blank <- testdat == "" #find all blank cells 
is.na(testdat)[blank] <- TRUE #change them to NAs

personIDs<-c(27,42,57,72,87,102,117,132,147,162,177,192,207,222,237,252)
nv0 <- c(personIDs+10,personIDs+11,personIDs+12,personIDs+13,personIDs+14,personIDs+9) #numerical values that should be 0
nv <- c(1,8,10,12,14,16,18,20,22,24,26,nv0)  #numerical values

for (i in 1:ncol(traindat)) {
    if (i %in% nv) {
        traindat[,i] <- as.numeric(as.character(traindat[,i]))
        testdat[,i] <- as.numeric(as.character(testdat[,i]))
        #if (i %in% nv0) # 
            #A[is.na(A[,i]),i] <- 0 
    } else if (i == 6 ) { #dates
        #traindat[,i] <- as.Date(traindat[,i],"%d-%b-%y")
        #testdat[,i] <- as.Date(testdat[,i],"%d-%b-%y")
        traindat[,i] <- as.Date(traindat[,i])
        testdat[,i] <- as.Date(testdat[,i])
    } else {
        traindat[,i] <- as.factor(traindat[,i])
        testdat[,i] <- as.factor(testdat[,i])
    }
}
#RF.predict(RF,testdat[,-c(1,5,removeVar)])

require('ROCR')

logit.fit <- glm(Grant.Status ~ 
                             + Number.of.Successful.Grant 
                             + Number.of.Unsuccessful.Grant
							 + Grant.Application.ID
							 #+ Grant.Category.Code	
							 #+ Contract.Value.Band...see.note.A
							,
                 data = traindat,
                 family = binomial(link = 'logit'))

GLMPred <- predict(logit.fit,testdat,type = "response")
