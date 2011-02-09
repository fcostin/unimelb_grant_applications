make_logit_prediction <- function(x, y, x_test) {
	logit.fit <- glm(y ~ x, family = binomial(link = 'logit'))
	predict(logit.fit, list(x = x_test), type = 'response')
}
