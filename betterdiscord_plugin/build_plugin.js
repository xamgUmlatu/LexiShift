const fs = require("fs");
const path = require("path");

const srcDir = path.join(__dirname, "src");
const outPath = path.join(__dirname, "VocabReplacer.plugin.js");

const parts = [
	"header.js",
	"constants.js",
	"state.js",
	"lzstring.js",
	"cjk_codec.js",
	"replacer.js",
	"ui.js",
	"plugin_class.js",
	"footer.js"
];

function buildPlugin() {
	const chunks = parts.map((filename) => {
		const fullPath = path.join(srcDir, filename);
		return fs.readFileSync(fullPath, "utf8").trimEnd();
	});

	const output = `${chunks.join("\n\n")}\n`;
	fs.writeFileSync(outPath, output);
	return outPath;
}

if (require.main === module) {
	const builtPath = buildPlugin();
	console.log(`Built ${builtPath}`);
}

module.exports = { buildPlugin };
