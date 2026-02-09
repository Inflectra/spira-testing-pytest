# PyTest Extension for SpiraTest

This version of the plugin is compatible with Python 3.x and SpiraTest/SpiraTeam/SpiraPlan 6.+

The latest documentation for using this extension can be found at http://spiradoc.inflectra.com/Unit-Testing-Integration/Integrating-with-PyTest/

## Performance Optimization

The plugin is optimized to have **zero overhead** when disabled. If you're not using Spira integration, you can disable it in several ways:

### Option 1: CLI Flag (Fastest - Zero Overhead)
```bash
pytest --spira-disabled
```

### Option 2: Configuration File
Set `enabled = false` in your `spira.cfg`:
```ini
[settings]
enabled = false
```

### Option 3: Remove Config Files
If you're not using Spira at all, simply don't include `spira.cfg` or `.env.spira` files in your project.

### Performance Notes
- When disabled, the plugin performs minimal checks and exits immediately
- No configuration parsing or file I/O occurs after the first test when disabled
- Tests run at full speed with no measurable overhead from the plugin