const path = require("path");
const fs = require("fs");
const { buildPlugin } = require("./build_plugin");

const srcDir = path.join(__dirname, "src");

let pending = null;

function rebuild() {
	try {
		const builtPath = buildPlugin();
		console.log(`Rebuilt ${builtPath}`);
	}
	catch (error) {
		console.error("Build failed:", error && error.message ? error.message : error);
	}
}

function scheduleBuild() {
	if (pending) clearTimeout(pending);
	pending = setTimeout(() => {
		pending = null;
		rebuild();
	}, 150);
}

if (!fs.existsSync(srcDir)) {
	console.error(`Missing src directory: ${srcDir}`);
	process.exit(1);
}

console.log(`Watching ${srcDir}...`);
rebuild();

fs.watch(srcDir, { recursive: true }, (eventType, filename) => {
	if (!filename || !filename.endsWith(".js")) return;
	scheduleBuild();
});
