const fs = require("fs");
const path = require("path");

const srcDir = path.join(__dirname, "src");
const outPath = path.join(__dirname, "LexiShift.plugin.js");

const sharedContentProcessing = path.resolve(__dirname, "..", "chrome-extension", "content", "processing");
const sharedLanguage = path.resolve(__dirname, "..", "chrome-extension", "shared", "language");
const parts = [
	"header.js",
	path.join(sharedLanguage, "language_prefs.js"),
	path.join(sharedContentProcessing, "tokenizer.js"),
	path.join(sharedContentProcessing, "matcher.js"),
	"constants.js",
	"state.js",
	"lzstring.js",
	"cjk_codec.js",
	"annotations.js",
	"replacer.js",
	"ui.js",
	"plugin_class.js",
	"footer.js"
];

function buildPluginOutput() {
	const chunks = parts.map((filename) => {
		const fullPath = path.isAbsolute(filename) ? filename : path.join(srcDir, filename);
		return fs.readFileSync(fullPath, "utf8").trimEnd();
	});
	return `${chunks.join("\n\n")}\n`;
}

function buildPlugin() {
	const output = buildPluginOutput();
	fs.writeFileSync(outPath, output);
	return outPath;
}

function checkPluginBuild() {
	const expected = buildPluginOutput();
	if (!fs.existsSync(outPath)) {
		console.error(`Missing built plugin: ${outPath}`);
		return false;
	}
	const current = fs.readFileSync(outPath, "utf8");
	if (current !== expected) {
		console.error(`Built plugin is out of date: ${outPath}`);
		return false;
	}
	console.log(`Plugin build is up to date: ${outPath}`);
	return true;
}

if (require.main === module) {
	if (process.argv.includes("--check")) {
		process.exit(checkPluginBuild() ? 0 : 1);
	}
	const builtPath = buildPlugin();
	console.log(`Built ${builtPath}`);
}

module.exports = { buildPlugin, buildPluginOutput, checkPluginBuild };
