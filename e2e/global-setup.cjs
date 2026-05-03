const { execSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.join(__dirname, "..");

module.exports = function globalSetup() {
  fs.mkdirSync(path.join(repoRoot, ".e2e"), { recursive: true });
  const rulesPath = path.join(repoRoot, ".e2e", "rules.yaml");
  if (!fs.existsSync(rulesPath)) {
    fs.writeFileSync(rulesPath, "rules: []\n", "utf8");
  }
  execSync("npm run build", { cwd: path.join(repoRoot, "frontend"), stdio: "inherit" });
};
