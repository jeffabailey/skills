# Install Scripts

## install-skills.sh

Auto-detects installed AI tools and symlinks skills from `src/` to their config directories.

### Usage

```bash
# Auto-detect tools and install
./scripts/install-skills.sh

# Specify source directory
./scripts/install-skills.sh /path/to/skills/repo
```

### Supported Tools

The script automatically detects and installs skills for:

- **Claude Desktop** (`~/.config/Claude/skills`)
- **Cursor** (`~/.config/Cursor/skills`)
- **OpenCode** (`~/.config/opencode/skills`)
- **Zed** (`~/.agents/skills`)

### What It Does

1. Scans for installed AI tool config directories
2. Creates symlinks from `src/*/` to each tool's skills directory
3. Reports how many skills were installed to each location

### Why Symlinks?

Symlinks allow you to:
- Edit skills in one place (this repo)
- Have changes immediately available to all tools
- Version control your skills
- Avoid duplication

### Troubleshooting

**No tools detected?**
- Install at least one supported AI tool
- Check that config directories exist in `~/.config/` or `~/.agents/`

**Skills not showing up?**
- Restart the AI tool
- Check symlinks: `ls -l ~/.config/Claude/skills/`
