const { existsSync } = require("node:fs");
const fs = require("node:fs/promises");
const { createReadStream } = require("node:fs");
const http = require("node:http");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const MOCK_DATA_PATH = path.join(PROJECT_ROOT, "docs", "_data", "landing_visual_mocks.json");
const SITE_ROOT = path.join(PROJECT_ROOT, "docs", "_site");
const DEFAULT_OUTPUT_DIR = path.join(
  PROJECT_ROOT,
  "docs",
  "test_outputs",
  "landing_visual_mocks",
);
const DEFAULT_VIEWPORT = "1440x960";
const CONTENT_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

const parseArgs = (argv) => {
  const options = {
    baseUrl: "",
    chrome: process.env.CHROME_BIN || "",
    help: false,
    list: false,
    mocks: [],
    outputDir: DEFAULT_OUTPUT_DIR,
    viewport: DEFAULT_VIEWPORT,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const nextValue = () => {
      index += 1;
      if (index >= argv.length) {
        throw new Error(`Missing value for ${arg}`);
      }
      return argv[index];
    };

    if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else if (arg === "--list") {
      options.list = true;
    } else if (arg === "--url") {
      options.baseUrl = nextValue();
    } else if (arg === "--out") {
      options.outputDir = path.resolve(nextValue());
    } else if (arg === "--mock") {
      options.mocks.push(nextValue());
    } else if (arg === "--chrome") {
      options.chrome = nextValue();
    } else if (arg === "--viewport") {
      options.viewport = nextValue();
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  return options;
};

const printHelp = () => {
  console.log(`Render LexiShift landing-page visual mocks.

Usage:
  npm --prefix scripts run render:landing-mocks
  npm --prefix scripts run render:landing-mocks -- --mock en-de
  npm --prefix scripts run render:landing-mocks -- --url http://127.0.0.1:4000/ --viewport 390x844

Options:
  --mock <id>       Render one mock. Repeat to render several. Defaults to all.
  --url <url>       Base landing page URL. Defaults to a local docs/_site server.
  --out <dir>       Output directory. Defaults to docs/test_outputs/landing_visual_mocks.
  --viewport <WxH>  Screenshot viewport. Defaults to 1440x960.
  --chrome <path>   Chrome/Chromium executable. Defaults to CHROME_BIN or auto-detect.
  --list            Print available mock ids.
`);
};

const resolveChrome = (requestedPath) => {
  const candidates = [
    requestedPath,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (candidate.includes(path.sep) && existsSync(candidate)) {
      return candidate;
    }
    if (!candidate.includes(path.sep)) {
      const lookup = spawnSync("sh", ["-lc", `command -v ${candidate}`], {
        encoding: "utf8",
      });
      if (lookup.status === 0 && lookup.stdout.trim()) {
        return lookup.stdout.trim();
      }
    }
  }

  throw new Error("Could not find Chrome. Pass --chrome <path> or set CHROME_BIN.");
};

const loadConfig = async () => JSON.parse(await fs.readFile(MOCK_DATA_PATH, "utf8"));

const resolveStaticPath = async (siteRoot, requestUrl) => {
  const url = new URL(requestUrl, "http://127.0.0.1");
  const pathname = decodeURIComponent(url.pathname);
  const relativePath = pathname.replace(/^\/+/, "") || "index.html";
  let filePath = path.normalize(path.join(siteRoot, relativePath));
  const rootRelativePath = path.relative(siteRoot, filePath);
  if (rootRelativePath.startsWith("..") || path.isAbsolute(rootRelativePath)) {
    return "";
  }

  const stat = await fs.stat(filePath).catch(() => null);
  if (stat && stat.isDirectory()) {
    filePath = path.join(filePath, "index.html");
  }
  return filePath;
};

const startStaticServer = async (siteRoot) => {
  const indexPath = path.join(siteRoot, "index.html");
  if (!existsSync(indexPath)) {
    throw new Error("Missing docs/_site/index.html. Run the Jekyll docs build first.");
  }

  const server = http.createServer(async (request, response) => {
    try {
      const filePath = await resolveStaticPath(siteRoot, request.url || "/");
      if (!filePath) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }

      const stat = await fs.stat(filePath).catch(() => null);
      if (!stat || !stat.isFile()) {
        response.writeHead(404);
        response.end("Not found");
        return;
      }

      response.writeHead(200, {
        "Content-Length": stat.size,
        "Content-Type": CONTENT_TYPES[path.extname(filePath)] || "application/octet-stream",
      });
      createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(500);
      response.end(error.message);
    }
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });

  const address = server.address();
  return {
    close: () => new Promise((resolve) => server.close(resolve)),
    url: `http://127.0.0.1:${address.port}/`,
  };
};

const normalizeKey = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-");

const resolveMockIds = (config, requestedMocks) => {
  const mocks = Array.isArray(config.mocks) ? config.mocks : [];
  const ids = new Set(mocks.map((mock) => mock.id));
  const aliases = config.aliases || {};
  const requested = requestedMocks.length > 0
    ? requestedMocks
    : mocks.map((mock) => mock.id);

  return requested.map((key) => {
    const normalized = normalizeKey(key);
    const id = ids.has(normalized) ? normalized : aliases[normalized];
    if (!id || !ids.has(id)) {
      throw new Error(`Unknown mock "${key}". Available: ${Array.from(ids).join(", ")}`);
    }
    return id;
  });
};

const buildMockUrl = (baseUrl, mockId) => {
  const url = new URL(baseUrl);
  url.searchParams.set("mock", mockId);
  return url.toString();
};

const parseViewport = (value) => {
  const match = /^(\d+)x(\d+)$/.exec(value);
  if (!match) {
    throw new Error(`Invalid viewport "${value}". Use WIDTHxHEIGHT, for example 1440x960.`);
  }
  return { width: Number(match[1]), height: Number(match[2]) };
};

const renderMock = ({ chrome, mockId, outputDir, url, viewport }) => new Promise((resolve, reject) => {
  const screenshotPath = path.join(outputDir, `landing-mock-${mockId}-${viewport.width}x${viewport.height}.png`);
  const child = spawn(
    chrome,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--allow-file-access-from-files",
      "--force-device-scale-factor=1",
      `--window-size=${viewport.width},${viewport.height}`,
      `--screenshot=${screenshotPath}`,
      url,
    ],
    { encoding: "utf8" },
  );

  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => {
    stdout += chunk;
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk;
  });
  child.on("error", reject);
  child.on("close", (code) => {
    if (code !== 0) {
      reject(new Error(
      [
        `Chrome failed while rendering ${mockId}.`,
        stdout.trim(),
        stderr.trim(),
      ].filter(Boolean).join("\n"),
      ));
      return;
    }

    resolve(screenshotPath);
  });
});

const main = async () => {
  const options = parseArgs(process.argv.slice(2));
  const config = await loadConfig();
  const availableIds = config.mocks.map((mock) => mock.id);

  if (options.help) {
    printHelp();
    return;
  }

  if (options.list) {
    console.log(availableIds.join("\n"));
    return;
  }

  const mockIds = resolveMockIds(config, options.mocks);
  const chrome = resolveChrome(options.chrome);
  const viewport = parseViewport(options.viewport);
  await fs.mkdir(options.outputDir, { recursive: true });
  const server = options.baseUrl ? null : await startStaticServer(SITE_ROOT);
  const baseUrl = options.baseUrl || server.url;

  try {
    for (const mockId of mockIds) {
      const url = buildMockUrl(baseUrl, mockId);
      const screenshotPath = await renderMock({
        chrome,
        mockId,
        outputDir: options.outputDir,
        url,
        viewport,
      });
      console.log(`${mockId}: ${screenshotPath}`);
    }
  } finally {
    if (server) {
      await server.close();
    }
  }
};

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
