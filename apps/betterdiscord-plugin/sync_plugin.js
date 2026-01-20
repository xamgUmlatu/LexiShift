const fs = require("fs");
const path = require("path");
const os = require("os");

const pluginName = "LexiShift.plugin.js";
const sourcePath = path.join(__dirname, pluginName);

function defaultPluginsDir() {
	if (process.platform === "darwin") {
		return path.join(os.homedir(), "Library", "Application Support", "BetterDiscord", "plugins");
	}
	if (process.platform === "win32") {
		if (!process.env.APPDATA) return null;
		return path.join(process.env.APPDATA, "BetterDiscord", "plugins");
	}
	return path.join(os.homedir(), ".config", "BetterDiscord", "plugins");
}

const targetDir = process.env.BD_PLUGINS_DIR || defaultPluginsDir();
if (!targetDir) {
	console.error("BetterDiscord plugins dir not found. Set BD_PLUGINS_DIR.");
	process.exit(1);
}

const targetPath = path.join(targetDir, pluginName);

if (!fs.existsSync(sourcePath)) {
	console.error(`Missing built plugin: ${sourcePath}`);
	process.exit(1);
}

fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(sourcePath, targetPath);
console.log(`Synced ${targetPath}`);
