# 📋 Kanban Board Desktop

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue.svg)]()
[![Version](https://img.shields.io/badge/Version-1.0-purple.svg)](https://github.com/krishna-dev639/KanbanDesktop/releases)

> **A lightweight, portable Kanban task manager for Windows & Linux. No installation required.**

![Main Board View](screenshot_main.png)

---

## ✨ Features

### 🚀 Truly Portable
- **Single executable file** - No installation required
- **platform** - Works on Windows and Linux

### 📊 Visual Organization
Track tasks across multiple statuses with drag-and-drop:
- **To Do** - Tasks waiting to be started
- **In Progress** - Tasks currently being worked on
- **Waiting for Response** - Tasks blocked on external input
- **Done** - Completed tasks

### 📈 Built-in Analytics
![Statistics Dashboard](screenshot_stats.png)
- Task distribution charts
- Completion rates
- Priority breakdown
- Group filtering

### ⚙️ Powerful Settings
![Settings Panel](screenshot_settings.png)
- **Dark/Light Mode** - Toggle between themes
- **Backup System** - Automatic backups every 24 hours
- **Retention Policy** - 7/30/60 days backup retention

### 📦 Export Options
![Export to ZIP](screenshot_export.png)
- **JSON Export** - Save board data for backup
- **ZIP Export** - Include attachments with your data
- **CSV Reports** - Generate detailed reports for analysis

![CSV Reports](screenshot_csv.png)

### 📎 Additional Features
- **Subtasks** - Track progress with nested subtasks
- **File Attachments** - Link or copy files to app storage
- **Keyboard Shortcuts** - `Ctrl+Shift+K` for quick task add
- **Groups** - Organize tasks by project or category

---

## 📥 Download

| Platform | Download |
|----------|----------|
| Windows | [📦 KanbanBoard_Windows_v1.0.exe](https://github.com/krishna-dev639/KanbanDesktop/releases/tag/V1.0) |
| Linux | [📦 KanbanBoard_Linux_v1.0](https://github.com/krishna-dev639/KanbanDesktop/releases/tag/V1.0) |

---

## 🚀 Getting Started

### Running from Executable

**Windows:**
1. Download `KanbanBoard_Windows_v1.0.exe` from [Releases](https://github.com/krishna-dev639/KanbanDesktop/releases)
2. Double-click to run - no installation needed!

**Linux:**
1. Download `KanbanBoard_Linux_v1.0` from [Releases](https://github.com/krishna-dev639/KanbanDesktop/releases)
2. Make it executable: `chmod +x KanbanBoard_Linux_v1.0`
3. Run: `./KanbanBoard_Linux_v1.0`

---

##  Data Storage

Data is stored in a `data` folder next to the executable:
```
KanbanBoard/
├── kanban_data.json    # Tasks, groups, settings
├── backups/            # Automated backups
└── attachments/        # Task attachments
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+K` | Quick Add Task (Global) |
| `Escape` | Close Modals |

---

## ❓ Troubleshooting

### Linux: "Unable to open" or Crash
- Install GTK dependencies: `sudo apt install libwebkit2gtk-4.0-37`
- Run from terminal to see errors: `./KanbanBoard_Linux_v1.0`

### Windows: Defender Warning
- Click "More Info" → "Run Anyway" (common for unsigned apps)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Murali Krishna**
- GitHub: [@krishna-dev639](https://github.com/krishna-dev639)

---

<p align="center">
  <b>⭐ Star this repo if you find it useful! ⭐</b>
</p>
