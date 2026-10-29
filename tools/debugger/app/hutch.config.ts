// @hutch cli=0.28.2 cottontail=0.7.3
export default {
	scripts: {
		start: ["hutch", "electrobun", "dev"],
		dev: ["hutch", "electrobun", "dev", "--watch"],
	},
	electrobun: {
		version: "2.0.5",
	},
};
