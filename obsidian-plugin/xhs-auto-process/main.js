const { Plugin, Notice } = require("obsidian");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const SOURCES_MARKER = ".obsidian-knowledge-sources";

module.exports = class XhsAutoProcessPlugin extends Plugin {
  async onload() {
    this.timer = null;
    this.running = false;

    const schedule = (file) => {
      if (!file || !file.path.startsWith("Clippings/") || !file.path.endsWith(".md")) return;
      clearTimeout(this.timer);
      this.timer = setTimeout(() => this.runProcessor(), 12000);
    };

    this.registerEvent(this.app.vault.on("create", schedule));
    this.registerEvent(this.app.vault.on("modify", schedule));
    this.addCommand({
      id: "run-now",
      name: "立即处理待沉淀的网页素材",
      callback: () => this.runProcessor(true),
    });

    // Catch notes created while Obsidian was closed.
    this.registerEvent(this.app.workspace.on("layout-ready", () => {
      setTimeout(() => this.runProcessor(), 5000);
    }));
  }

  onunload() {
    clearTimeout(this.timer);
  }

  runProcessor(showNotice = false) {
    if (this.running) return;
    this.running = true;
    if (showNotice) new Notice("开始处理知识收件箱…");

    const vaultPath = this.app.vault.adapter.basePath;
    const sourcesRoot = this.findSourcesRoot(vaultPath);
    const script = path.join(sourcesRoot, "Automation", "xhs_auto_process.py");
    if (!fs.existsSync(script)) {
      this.running = false;
      new Notice(`找不到知识自动沉淀脚本：${script}`, 8000);
      return;
    }

    const python = process.env.OBSIDIAN_KNOWLEDGE_PYTHON || (process.platform === "win32" ? "python" : "python3");
    const child = spawn(python, [script], {
      cwd: vaultPath,
      detached: false,
      stdio: "ignore",
    });
    child.on("error", (error) => {
      this.running = false;
      new Notice(`知识自动沉淀启动失败：${error.message}`, 8000);
    });
    child.on("exit", (code) => {
      this.running = false;
      if (showNotice) {
        new Notice(code === 0 ? "知识收件箱处理完成" : `处理未完成，退出码 ${code}`, 6000);
      }
    });
  }

  findSourcesRoot(vaultPath) {
    const override = process.env.OBSIDIAN_KNOWLEDGE_SOURCES;
    if (override) return path.join(vaultPath, override);
    const candidates = fs.readdirSync(vaultPath, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => path.join(vaultPath, entry.name))
      .filter((directory) => fs.existsSync(path.join(directory, SOURCES_MARKER)));
    if (candidates.length === 1) return candidates[0];
    return path.join(vaultPath, "06 - Sources");
  }
};
