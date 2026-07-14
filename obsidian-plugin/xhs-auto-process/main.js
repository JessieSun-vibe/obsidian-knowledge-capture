const { Plugin, Notice } = require("obsidian");
const { spawn } = require("child_process");

module.exports = class XhsAutoProcessPlugin extends Plugin {
  async onload() {
    this.timer = null;
    this.running = false;
    this.script = `${this.app.vault.adapter.basePath}/06 - Sources/Automation/xhs_auto_process.py`;

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

    const child = spawn("/usr/bin/python3", [this.script], {
      cwd: this.app.vault.adapter.basePath,
      detached: false,
      stdio: "ignore",
    });
    child.on("error", (error) => {
      this.running = false;
      new Notice(`小红书自动沉淀启动失败：${error.message}`, 8000);
    });
    child.on("exit", (code) => {
      this.running = false;
      if (showNotice) {
        new Notice(code === 0 ? "知识收件箱处理完成" : `处理未完成，退出码 ${code}`, 6000);
      }
    });
  }
};
