const { spawnSync } = require("child_process");
const path = require("path");

const SCRIPT_ROOT = path.resolve(__dirname, "..");

function resolveCandidates() {
	const candidates = [];
	const envCandidates = [
		process.env.LEXISHIFT_PYTHON,
		process.env.PYTHON,
		process.env.PYTHON3,
	].filter(Boolean);
	for (const value of envCandidates) {
		candidates.push({ command: value, prefixArgs: [] });
	}
	candidates.push({ command: "python3", prefixArgs: [] });
	candidates.push({ command: "python", prefixArgs: [] });
	candidates.push({ command: "py", prefixArgs: ["-3"] });
	return candidates;
}

function commandExists(candidate) {
	const probe = spawnSync(candidate.command, [...candidate.prefixArgs, "--version"], {
		stdio: "ignore",
	});
	if (probe.error) {
		return false;
	}
	return probe.status === 0;
}

function resolvePython() {
	for (const candidate of resolveCandidates()) {
		if (commandExists(candidate)) {
			return candidate;
		}
	}
	return null;
}

function main() {
	const scriptArgs = process.argv.slice(2);
	if (scriptArgs.length === 0) {
		console.error("Usage: node dev/run_python.js <script-or-module> [args...]");
		process.exit(2);
	}

	const python = resolvePython();
	if (!python) {
		console.error(
			"Unable to locate a Python 3 interpreter. Set LEXISHIFT_PYTHON or ensure python3/python/py -3 is available."
		);
		process.exit(1);
	}

	const result = spawnSync(
		python.command,
		[...python.prefixArgs, ...scriptArgs],
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

main();
