#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const {
	REPO_ROOT,
	SUPPORTED_PYTHON,
	formatVersion,
	probePython,
	resolvePython,
	venvCandidates,
} = require("./python_environment");

const DEV_MODULES = Object.freeze([
	"fsrs",
	"mypy",
	"numpy",
	"pre_commit",
	"pytest",
	"ruff",
	"simplemma",
]);
const BUILD_MODULES = Object.freeze(["PyInstaller", "PySide6"]);
const PIP_VERSION = "26.2.1";

function run(candidate, args) {
	console.log(`+ ${[candidate.command, ...candidate.prefixArgs, ...args].join(" ")}`);
	const result = spawnSync(candidate.command, [...candidate.prefixArgs, ...args], {
		cwd: REPO_ROOT,
		stdio: "inherit",
	});
	if (result.error) {
		console.error(result.error.message);
		return 1;
	}
	return result.status === null ? 1 : result.status;
}

function existingVenvPython() {
	for (const candidate of venvCandidates(path.resolve(REPO_ROOT, ".venv"), "repo .venv")) {
		const version = probePython(candidate);
		if (version) {
			return { ...candidate, version };
		}
	}
	return null;
}

function verifyModules(candidate, modules) {
	const code = [
		"import importlib.util, json",
		`modules = ${JSON.stringify(modules)}`,
		"missing = [name for name in modules if importlib.util.find_spec(name) is None]",
		"print(json.dumps({'missing': missing}))",
		"raise SystemExit(1 if missing else 0)",
	].join("\n");
	const result = spawnSync(candidate.command, [...candidate.prefixArgs, "-c", code], {
		cwd: REPO_ROOT,
		encoding: "utf8",
	});
	if (result.stdout) {
		try {
			return JSON.parse(result.stdout.trim()).missing || [];
		} catch (_error) {
			// Fall through to the generic failure below.
		}
	}
	return modules;
}

function loadPinnedRequirements(requirementsPath, seen = new Set()) {
	const resolved = path.resolve(requirementsPath);
	if (seen.has(resolved)) {
		return {};
	}
	seen.add(resolved);
	const pins = {};
	for (const rawLine of fs.readFileSync(resolved, "utf8").split(/\r?\n/)) {
		const line = rawLine.trim();
		if (!line || line.startsWith("#")) {
			continue;
		}
		if (line.startsWith("-r ")) {
			Object.assign(
				pins,
				loadPinnedRequirements(path.resolve(path.dirname(resolved), line.slice(3).trim()), seen)
			);
			continue;
		}
		const match = /^([A-Za-z0-9_.-]+)==([^\s;]+)$/.exec(line);
		if (!match) {
			throw new Error(`Expected an exact package pin in ${resolved}: ${line}`);
		}
		pins[match[1]] = match[2];
	}
	return pins;
}

function verifyPinnedRequirements(candidate, pins) {
	const code = [
		"import importlib.metadata, json",
		`pins = ${JSON.stringify(pins)}`,
		"installed = {}",
		"for name in pins:",
		"    try:",
		"        installed[name] = importlib.metadata.version(name)",
		"    except importlib.metadata.PackageNotFoundError:",
		"        installed[name] = None",
		"mismatches = {name: {'expected': expected, 'actual': installed[name]} for name, expected in pins.items() if installed[name] != expected}",
		"print(json.dumps({'mismatches': mismatches}, sort_keys=True))",
		"raise SystemExit(1 if mismatches else 0)",
	].join("\n");
	const result = spawnSync(candidate.command, [...candidate.prefixArgs, "-c", code], {
		cwd: REPO_ROOT,
		encoding: "utf8",
	});
	if (result.stdout) {
		try {
			return JSON.parse(result.stdout.trim()).mismatches || {};
		} catch (_error) {
			// Fall through to the generic failure below.
		}
	}
	return Object.fromEntries(
		Object.entries(pins).map(([name, expected]) => [name, { expected, actual: null }])
	);
}

function parseArgs(argv) {
	const allowed = new Set(["--build", "--check"]);
	const unknown = argv.filter((value) => !allowed.has(value));
	if (unknown.length) {
		throw new Error(`Unknown argument(s): ${unknown.join(", ")}`);
	}
	return {
		build: argv.includes("--build"),
		check: argv.includes("--check"),
	};
}

function main() {
	let args;
	try {
		args = parseArgs(process.argv.slice(2));
	} catch (error) {
		console.error(error.message);
		console.error("Usage: node dev/bootstrap_python_env.js [--build] [--check]");
		return 2;
	}

	const venvRoot = path.resolve(REPO_ROOT, ".venv");
	let venvPython = existingVenvPython();
	if (fs.existsSync(venvRoot) && !venvPython) {
		console.error(
			`Existing ${venvRoot} is not a usable Python virtual environment. Move it aside and rerun setup.`
		);
		return 1;
	}
	if (venvPython && (
		venvPython.version.major !== SUPPORTED_PYTHON.major
		|| venvPython.version.minor !== SUPPORTED_PYTHON.minor
	)) {
		console.error(
			`Existing .venv uses Python ${formatVersion(venvPython.version)}; LexiShift requires Python 3.10.x. Move it aside and rerun setup.`
		);
		return 1;
	}

	if (!venvPython && args.check) {
		console.error("LexiShift .venv is missing. Run: npm --prefix scripts run setup:python");
		return 1;
	}

	if (!venvPython) {
		const resolution = resolvePython({
			includeRepoVenv: false,
			includeEnvironment: true,
			includeSystem: true,
		});
		if (!resolution.command) {
			console.error(
				"Python 3.10.x was not found. Install Python 3.10, or set LEXISHIFT_PYTHON to its executable."
			);
			return 1;
		}
		console.log(
			`Creating .venv with Python ${formatVersion(resolution.version)} (${resolution.version.executable}).`
		);
		if (run(resolution, ["-m", "venv", venvRoot]) !== 0) {
			return 1;
		}
		venvPython = existingVenvPython();
		if (!venvPython) {
			console.error("Virtual environment creation completed without a usable .venv Python.");
			return 1;
		}
	}

	const requirements = args.build ? "requirements-build.txt" : "requirements-dev.txt";
	const requiredModules = args.build ? [...DEV_MODULES, ...BUILD_MODULES] : [...DEV_MODULES];
	const pinnedRequirements = {
		pip: PIP_VERSION,
		...loadPinnedRequirements(path.resolve(REPO_ROOT, requirements)),
	};
	if (!args.check) {
		if (run(venvPython, ["-m", "pip", "install", `pip==${PIP_VERSION}`]) !== 0) {
			return 1;
		}
		if (run(venvPython, ["-m", "pip", "install", "-r", requirements]) !== 0) {
			return 1;
		}
	}

	const missing = verifyModules(venvPython, requiredModules);
	if (missing.length) {
		console.error(`LexiShift .venv is missing required modules: ${missing.join(", ")}`);
		console.error(
			`Repair it with: npm --prefix scripts run ${args.build ? "setup:python:build" : "setup:python"}`
		);
		return 1;
	}
	const mismatches = verifyPinnedRequirements(venvPython, pinnedRequirements);
	if (Object.keys(mismatches).length) {
		for (const [name, versions] of Object.entries(mismatches)) {
			console.error(
				`${name}: expected ${versions.expected}, found ${versions.actual || "not installed"}`
			);
		}
		console.error(
			`Synchronize it with: npm --prefix scripts run ${args.build ? "setup:python:build" : "setup:python"}`
		);
		return 1;
	}
	console.log(
		`LexiShift .venv is ready: Python ${formatVersion(venvPython.version)}, ${args.build ? "build" : "development"} dependencies verified.`
	);
	return 0;
}

if (require.main === module) {
	process.exit(main());
}

module.exports = {
	BUILD_MODULES,
	DEV_MODULES,
	PIP_VERSION,
	loadPinnedRequirements,
	parseArgs,
	verifyModules,
	verifyPinnedRequirements,
};
