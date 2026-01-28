# Contributing to MT7927 Linux Driver

Thank you for your interest in contributing to the MediaTek MT7927 Linux driver project! This is an experimental, community-driven reverse engineering effort, and all contributions are welcome.

## How to Contribute

There are many ways to contribute to this project, even if you're not a kernel developer:

### 1. Hardware Testing
If you own an MT7927-based device:
- Test the driver and report results
- Capture PCI configuration space
- Dump register values
- Monitor hardware behavior
- Share findings

### 2. Reverse Engineering
- Analyze Windows drivers
- Extract firmware binaries
- Document register layouts
- Trace hardware initialization
- Identify command protocols

### 3. Code Development
- Implement TODOs in the code
- Add new features
- Fix bugs
- Improve documentation
- Write tests

### 4. Documentation
- Document findings
- Write tutorials
- Translate documentation
- Create diagrams
- Improve README

### 5. Issue Reporting
- Report bugs
- Request features
- Ask questions
- Share ideas

## Getting Started

### Prerequisites

1. **Development Environment**
   ```bash
   # Install build tools
   sudo apt-get install build-essential linux-headers-$(uname -r)
   
   # Install optional tools
   sudo apt-get install git ghidra qemu-system-x86
   ```

2. **Fork and Clone**
   ```bash
   # Fork on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/TP-link-wifi-MT7927-reverse-engineer.git
   cd TP-link-wifi-MT7927-reverse-engineer
   ```

3. **Build the Driver**
   ```bash
   cd driver
   make
   ```

### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/my-feature
   # or
   git checkout -b fix/my-bugfix
   ```

2. **Make Changes**
   - Follow Linux kernel coding style
   - Add comments explaining your changes
   - Mark unknowns with TODO/FIXME
   - Test your changes

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```
   
   See [Commit Message Guidelines](#commit-message-guidelines) below.

4. **Push and Create PR**
   ```bash
   git push origin feature/my-feature
   ```
   Then create a Pull Request on GitHub.

## Coding Standards

### Linux Kernel Style

This project follows the Linux kernel coding style. Key points:

- **Indentation**: Tabs (8 spaces wide), not spaces
- **Line Length**: 80 columns preferred, 100 maximum
- **Braces**: K&R style
- **Naming**: lowercase_with_underscores for functions/variables

**Check your code**:
```bash
# Get checkpatch.pl from Linux kernel tree
wget https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/scripts/checkpatch.pl
chmod +x checkpatch.pl

# Check your patches
./checkpatch.pl --no-tree --file driver/mt7927_*.c
```

### Code Documentation

- Add comments explaining WHY, not WHAT
- Mark speculative code with TODO
- Document unknowns explicitly
- Explain assumptions and limitations

**Example**:
```c
/*
 * Set DMA burst size to 128 bytes
 * TODO: This is based on MT7921 - needs verification for MT7927
 */
mt7927_wr(dev, MT7927_DMA_BURST, 0x80);  /* 128 bytes */
```

### Function Documentation

Use kernel-doc format for functions:

```c
/**
 * mt7927_init_dma - Initialize DMA rings
 * @dev: pointer to device structure
 *
 * Allocates and configures TX/RX DMA descriptor rings.
 *
 * Return: 0 on success, negative error code on failure
 */
static int mt7927_init_dma(struct mt7927_dev *dev)
{
    /* ... */
}
```

## Commit Message Guidelines

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Build process, tools, etc.
- **reverse**: Reverse engineering findings

### Examples

**Good commit messages**:
```
feat(pci): Add MT7927 PCI device probe function

Implements PCI device detection and resource allocation for MT7927.
Maps BAR0 for register access and requests IRQ.

Signed-off-by: John Doe <john@example.com>
```

```
reverse(regs): Document interrupt status register layout

Based on analysis of Windows driver v1.0.2.3, the interrupt status
register at offset 0x1200 has the following layout:
- Bit 0: TX complete
- Bit 1: RX ready
- Bit 2: MCU event
(Additional bits still unknown)

Signed-off-by: Jane Smith <jane@example.com>
```

**Bad commit messages**:
```
fix stuff
Update file
Changes
WIP
```

## Pull Request Process

1. **Before Submitting**
   - Code compiles without warnings
   - Follows coding style (check with checkpatch.pl)
   - Includes appropriate documentation
   - No unrelated changes
   - Commit messages are clear

2. **PR Description**
   - Explain what changes were made
   - Explain why changes were made
   - Reference related issues
   - Include test results if applicable

3. **Review Process**
   - Maintainers will review your PR
   - Address feedback and questions
   - Make requested changes
   - Be patient - this is a volunteer project

4. **Merging**
   - PR will be merged when approved
   - You may be asked to rebase or squash commits

## Reverse Engineering Contributions

### Documenting Findings

When documenting reverse engineering findings:

1. **Be Specific**
   - Exact register addresses
   - Bit positions and meanings
   - Initialization sequences
   - Command/response formats

2. **Show Your Work**
   - How you discovered this
   - What tools you used
   - Evidence (dumps, traces, etc.)
   - Confidence level (Low/Medium/High)

3. **Update Documentation**
   - Add to docs/REVERSE_ENGINEERING.md
   - Update register definitions in code
   - Add inline comments

### Reverse Engineering Ethics

- **Legal**: Ensure your methods are legal in your jurisdiction
- **Clean Room**: Don't copy proprietary code
- **Attribution**: Credit sources when applicable
- **Safety**: Be cautious with untested register writes

### Example Finding Documentation

```markdown
## Date: 2024-01-15 - Interrupt Status Register

**Component**: Interrupt Controller
**Confidence**: High

**Method**: 
- Traced Windows driver with WinDbg
- Monitored MMIO reads during interrupt handling
- Correlated with TX/RX activity

**Finding**:
Interrupt status register is at offset 0x1200 from BAR0.

Register layout (32-bit):
- Bit 0 (0x00000001): TX queue 0 complete
- Bit 1 (0x00000002): TX queue 1 complete
- Bit 2 (0x00000004): TX queue 2 complete
- Bit 3 (0x00000008): TX queue 3 complete
- Bit 4 (0x00000010): RX queue 0 ready
- Bit 5 (0x00000020): RX queue 1 ready
- Bit 6 (0x00000040): MCU command complete
- Bits 7-31: Unknown/unused

**Evidence**:
```
WinDbg trace:
00:12:34.567 READ  BAR0+0x1200 -> 0x00000011 (TX0 + RX0)
00:12:34.568 WRITE BAR0+0x1200 <- 0x00000011 (clear)
```
```

## Testing Contributions

If you test on hardware:

1. Follow docs/TESTING.md
2. Document your setup
3. Record results (success or failure)
4. Share logs and traces
5. Report unexpected behavior

## Issue Reporting

### Bug Reports

Include:
- **Description**: What went wrong
- **Expected**: What should happen
- **Actual**: What actually happened
- **System Info**: Kernel version, hardware, etc.
- **Logs**: Relevant dmesg output
- **Steps**: How to reproduce

### Feature Requests

Include:
- **Description**: What feature you want
- **Use Case**: Why it's needed
- **Examples**: How it would be used

## Code Review Process

All contributions go through code review:

### Review Criteria
- Correctness
- Code quality
- Documentation
- Testing
- Follows project standards

### Addressing Review Comments
- Respond to all comments
- Make requested changes
- Ask questions if unclear
- Be respectful and professional

## Questions and Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Code Comments**: For technical questions about specific code

## Legal Considerations

### License

This project is licensed under GPL-2.0-only to match Linux kernel requirements.

By contributing, you agree that your contributions will be licensed under the same license.

### Contributor Agreement

By submitting a pull request, you certify that:

1. The contribution is your original work, or you have rights to submit it
2. You grant the project the right to use your contribution under the GPL-2.0 license
3. You have not included any proprietary code or violated any copyrights

### Reverse Engineering

When contributing reverse engineering findings:

- Use clean-room techniques
- Don't include proprietary code
- Don't redistribute proprietary firmware
- Be aware of legal restrictions in your jurisdiction

## Recognition

Contributors are recognized in:
- Git commit history
- Release notes
- README acknowledgments (for significant contributions)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Our Standards

- **Be Respectful**: Treat others with respect
- **Be Constructive**: Provide helpful feedback
- **Be Collaborative**: Work together toward common goals
- **Be Patient**: Remember this is a volunteer project

### Unacceptable Behavior

- Harassment or discrimination
- Personal attacks
- Trolling or insulting comments
- Publishing others' private information

## Project Structure

```
.
├── driver/              # Driver source code
│   ├── mt7927.h        # Main header
│   ├── mt7927_regs.h   # Register definitions
│   ├── mt7927_main.c   # mac80211 integration
│   ├── mt7927_pci.c    # PCI interface
│   ├── Makefile        # Build system
│   └── Kconfig         # Kernel config
├── docs/               # Documentation
│   ├── REVERSE_ENGINEERING.md
│   ├── TESTING.md
│   └── CONTRIBUTING.md (this file)
└── README.md          # Project overview
```

## Maintainers

This is a community project. Active contributors may become maintainers.

Current maintainers will be listed here as the project grows.

## Thank You!

Your contributions help make Linux support better for everyone. Whether you're fixing a typo, testing on hardware, or reverse engineering protocols, every contribution matters.

Happy hacking! 🚀

---

**Last Updated**: January 2024
