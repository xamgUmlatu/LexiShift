"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");
const { formatVersion, resolvePython } = require("./python_environment");

const SCRIPT_ROOT = path.resolve(__dirname, "..");

function main() {
	const scriptArgs = process.argv.slice(2);
	if (scriptArgs.length === 0) {
		console.error("Usage: node dev/run_python.js <script-or-module> [args...]");
		process.exit(2);
	}

	const allowSystemFallback = Boolean(process.env.CI);
	const resolution = resolvePython({ includeSystem: allowSystemFallback });
	if (!resolution.command) {
		console.error(
			"Unable to locate the supported Python 3.10 environment. Run `npm --prefix scripts run setup:python`, activate a Python 3.10 virtualenv, or set LEXISHIFT_PYTHON explicitly."
		);
		for (const rejected of resolution.rejected || []) {
			console.error(
				`Rejected ${rejected.version.executable}: Python ${formatVersion(rejected.version)} (requires 3.10.x).`
			);
		}
		process.exit(1);
	}

	const result = spawnSync(
		resolution.command,
		[...resolution.prefixArgs, ...scriptArgs],
		{
			cwd: SCRIPT_ROOT,
			stdio: "inherit",
		}
	);
	if (result.error) {
		console.error(result.error.message);
		process.exit(1);
	}
	process.exit(result.status === null ? 1 : result.status);
}

if (require.main === module) {
	main();
}

module.exports = { main };
