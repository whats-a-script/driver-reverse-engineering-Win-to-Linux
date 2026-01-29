# Security Guidelines

This document provides comprehensive security guidelines for the Windows to Linux Driver Conversion Framework. Security is paramount when dealing with kernel-level code and binary analysis.

---

## 🔒 Security Principles

### Core Principles
1. **Defense in Depth:** Multiple layers of security controls
2. **Least Privilege:** Minimize permissions and access
3. **Secure by Default:** Security features enabled by default
4. **Fail Secure:** Failures should not compromise security
5. **Zero Trust:** Never trust input, always validate

---

## 1. Analysis Security

### 1.1 Sandboxing Windows Driver Analysis

**Threat:** Malicious driver binary executed during analysis

**Mitigations:**

#### Container-Based Sandboxing
```bash
# Run analyzer in Docker container
docker run --rm \
    --security-opt=no-new-privileges \
    --cap-drop=ALL \
    --network=none \
    -v /path/to/driver:/input:ro \
    -v /path/to/output:/output \
    driver-analyzer:latest \
    analyze /input/driver.sys
```

**Container Security:**
- [ ] Read-only input mounts
- [ ] No network access
- [ ] Dropped capabilities (CAP_DROP=ALL)
- [ ] no-new-privileges flag
- [ ] Resource limits (CPU, memory)
- [ ] Temporary filesystem for writes

#### VM-Based Sandboxing
```bash
# Run analyzer in dedicated VM
qemu-system-x86_64 \
    -enable-kvm \
    -m 4G \
    -net none \
    -drive file=analyzer-vm.qcow2 \
    -fsdev local,security_model=mapped,id=fsdev0,path=/input,readonly \
    -device virtio-9p-pci,fsdev=fsdev0,mount_tag=input
```

**VM Security:**
- [ ] No network connectivity
- [ ] Snapshot-based (revert after analysis)
- [ ] Read-only input sharing
- [ ] Resource limits
- [ ] Automated cleanup

---

### 1.2 Static Analysis Safety

**Disassembly Tools:**
- Use Ghidra in headless mode (no GUI exploits)
- Limit analysis time (timeout after X minutes)
- Monitor resource usage
- Validate input file format before processing

**File Validation:**
```python
def validate_driver_binary(file_path):
    """Validate driver binary before analysis."""
    
    # Check file size (reject suspiciously large files)
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    if os.path.getsize(file_path) > MAX_SIZE:
        raise SecurityError("File too large")
    
    # Verify PE format
    if not is_valid_pe_file(file_path):
        raise SecurityError("Invalid PE file format")
    
    # Scan with antivirus (optional)
    if ANTIVIRUS_ENABLED:
        scan_result = scan_with_clamav(file_path)
        if scan_result.is_malware:
            raise SecurityError(f"Malware detected: {scan_result.signature}")
    
    return True
```

---

## 2. Wrapper Runtime Security

### 2.1 Kernel Module Isolation

**Threat:** Malicious or buggy vendor driver code in kernel space

**Mitigations:**

#### Memory Isolation
```c
// Allocate isolated memory region for vendor driver
void *driver_memory = vmalloc_user(DRIVER_MEMORY_SIZE);
if (!driver_memory)
    return -ENOMEM;

// Set memory protections
set_memory_nx(driver_memory, DRIVER_MEMORY_SIZE >> PAGE_SHIFT);  // No-execute
```

#### API Filtering
```c
// Intercept and validate all driver API calls
static struct ndis_shim_ops safe_ops = {
    .AllocateMemory = validate_and_allocate_memory,
    .RegisterInterrupt = validate_and_register_interrupt,
    .DmaAlloc = validate_and_dma_alloc,
    // ... other filtered operations
};

static int validate_and_allocate_memory(size_t size, void **ptr) {
    // Enforce limits
    if (size > MAX_ALLOCATION_SIZE) {
        pr_warn("Driver requested excessive memory: %zu bytes\n", size);
        return -EINVAL;
    }
    
    // Track allocations
    track_allocation(size);
    
    // Proceed with allocation
    return real_allocate_memory(size, ptr);
}
```

#### Runtime Monitoring
```c
// Monitor driver behavior
static void monitor_driver_activity(void) {
    // Log all API calls
    if (AUDIT_ENABLED)
        audit_log_driver_call(current_driver, current_function);
    
    // Check for anomalies
    if (excessive_interrupts() || memory_leak_detected()) {
        pr_alert("Suspicious driver behavior detected\n");
        trigger_kill_switch();
    }
}
```

---

### 2.2 Kill Switch Mechanism

**Purpose:** Immediately disable driver if security issue detected

```c
static atomic_t kill_switch = ATOMIC_INIT(0);

void trigger_kill_switch(void) {
    atomic_set(&kill_switch, 1);
    pr_alert("KILL SWITCH ACTIVATED - Driver disabled\n");
    
    // Disable interrupts
    disable_driver_interrupts();
    
    // Stop DMA
    stop_all_dma_operations();
    
    // Notify userspace
    send_userspace_notification(DRIVER_KILLED);
}

// Check kill switch before every operation
int wrapper_operation(void) {
    if (atomic_read(&kill_switch))
        return -EPERM;
    
    // ... proceed with operation
}
```

---

### 2.3 Userspace Helper Security

**Rust Userspace Helper (Recommended):**

```rust
use seccomp::{Context, Action};

fn setup_seccomp_sandbox() -> Result<(), Error> {
    let mut ctx = Context::default(Action::Kill)?;
    
    // Allow only necessary syscalls
    ctx.allow_syscall(libc::SYS_read)?;
    ctx.allow_syscall(libc::SYS_write)?;
    ctx.allow_syscall(libc::SYS_ioctl)?;
    ctx.allow_syscall(libc::SYS_exit)?;
    ctx.allow_syscall(libc::SYS_exit_group)?;
    
    // Load seccomp filter
    ctx.load()?;
    Ok(())
}

fn main() {
    // Drop privileges
    drop_privileges();
    
    // Setup seccomp sandbox
    setup_seccomp_sandbox().expect("Failed to setup seccomp");
    
    // Setup namespaces
    setup_namespaces();
    
    // Run helper
    run_driver_helper();
}
```

---

## 3. Generated Driver Security

### 3.1 Code Generation Security

**Template Validation:**
```python
def validate_template_safety(template_code):
    """Ensure generated code follows security best practices."""
    
    security_checks = [
        check_buffer_overflows,
        check_integer_overflows,
        check_race_conditions,
        check_resource_leaks,
        check_unsafe_functions,
    ]
    
    issues = []
    for check in security_checks:
        result = check(template_code)
        if not result.passed:
            issues.append(result.issue)
    
    return issues
```

**Banned Unsafe Functions:**
```c
// Never use these in generated code:
// - strcpy, strcat, sprintf (use strscpy, strlcat, snprintf)
// - gets (use fgets)
// - scanf without field width
// - Unchecked pointer arithmetic
```

**Safe Alternatives:**
```c
// Use kernel-safe functions
strscpy(dest, src, sizeof(dest));  // Not strcpy
snprintf(buf, sizeof(buf), fmt, args);  // Not sprintf
copy_from_user(kernel_buf, user_ptr, size);  // Not direct access
```

---

### 3.2 Input Validation

**IOCTL Handler Template:**
```c
static long driver_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    void __user *argp = (void __user *)arg;
    int ret;
    
    // Validate IOCTL command
    if (_IOC_TYPE(cmd) != DRIVER_IOC_MAGIC) {
        pr_warn("Invalid IOCTL magic: 0x%x\n", _IOC_TYPE(cmd));
        return -ENOTTY;
    }
    
    // Validate size
    if (_IOC_SIZE(cmd) > MAX_IOCTL_SIZE) {
        pr_warn("IOCTL size too large: %u\n", _IOC_SIZE(cmd));
        return -EINVAL;
    }
    
    switch (cmd) {
    case DRIVER_IOC_SET_CONFIG:
        {
            struct driver_config config;
            
            // Safe copy from userspace
            if (copy_from_user(&config, argp, sizeof(config)))
                return -EFAULT;
            
            // Validate input
            if (!validate_config(&config))
                return -EINVAL;
            
            ret = set_driver_config(&config);
        }
        break;
        
    default:
        return -ENOTTY;
    }
    
    return ret;
}
```

---

### 3.3 Concurrency Safety

**Locking Best Practices:**
```c
// Use appropriate lock types
spinlock_t driver_lock;           // For short critical sections
struct mutex driver_mutex;         // For longer operations
struct rw_semaphore driver_rwsem;  // For read-heavy workloads

// Lock ordering (prevent deadlocks)
// Always acquire locks in this order:
// 1. driver_global_lock
// 2. driver_device_lock
// 3. driver_queue_lock

// Example with lock validation
static int safe_update_config(struct driver_data *data, struct config *cfg)
{
    might_sleep();  // Catch atomic context bugs
    
    mutex_lock(&data->mutex);
    
    // Validate while holding lock
    if (!validate_config_locked(cfg)) {
        mutex_unlock(&data->mutex);
        return -EINVAL;
    }
    
    // Update configuration
    memcpy(&data->config, cfg, sizeof(*cfg));
    
    mutex_unlock(&data->mutex);
    return 0;
}
```

---

### 3.4 DMA Security

**Safe DMA Operations:**
```c
// Allocate DMA buffer safely
static int allocate_dma_buffer(struct driver_data *data)
{
    // Use kernel DMA API
    data->dma_vaddr = dma_alloc_coherent(
        &data->pdev->dev,
        DMA_BUFFER_SIZE,
        &data->dma_addr,
        GFP_KERNEL
    );
    
    if (!data->dma_vaddr)
        return -ENOMEM;
    
    // Set IOMMU protections if available
    // (kernel handles this with DMA API)
    
    return 0;
}

// Validate DMA addresses
static bool validate_dma_address(dma_addr_t addr, size_t size)
{
    // Check alignment
    if (addr & (DMA_ALIGNMENT - 1)) {
        pr_warn("Misaligned DMA address: 0x%llx\n", addr);
        return false;
    }
    
    // Check bounds
    if (addr + size < addr) {  // Overflow check
        pr_warn("DMA address overflow\n");
        return false;
    }
    
    return true;
}
```

---

## 4. Module Signing and Secure Boot

### 4.1 Module Signing

**Generate Signing Key:**
```bash
# Generate private key (KEEP SECURE!)
openssl req -new -x509 -newkey rsa:4096 -keyout MOK.priv -outform DER \
    -out MOK.der -nodes -days 36500 -subj "/CN=Driver Signing Key/"

# Enroll key with MOK (Machine Owner Key)
sudo mokutil --import MOK.der
# Reboot and complete enrollment
```

**Sign Module:**
```bash
# Sign the kernel module
/usr/src/linux-headers-$(uname -r)/scripts/sign-file \
    sha256 \
    MOK.priv \
    MOK.der \
    driver.ko

# Verify signature
modinfo driver.ko | grep signature
```

**DKMS Integration:**
```bash
# Add to dkms.conf
SIGN_TOOL="/usr/src/linux-headers-$(uname -r)/scripts/sign-file"
SIGN_HASH="sha256"
SIGN_KEY="/path/to/MOK.priv"
SIGN_CERT="/path/to/MOK.der"
```

---

### 4.2 Secure Boot Compatibility

**Requirements:**
- [ ] Module must be signed with trusted key
- [ ] No use of `CONFIG_MODULE_FORCE_LOAD`
- [ ] Compliance with kernel lockdown mode
- [ ] No unsigned firmware loading

**Check Secure Boot Status:**
```bash
# Check if Secure Boot is enabled
mokutil --sb-state

# Check kernel lockdown mode
cat /sys/kernel/security/lockdown
```

**Lockdown Mode Compliance:**
```c
// Check lockdown restrictions
#include <linux/security.h>

static int driver_init(void)
{
    // Check if module loading is restricted
    if (kernel_is_locked_down("Module loading")) {
        pr_err("Cannot load: kernel is locked down\n");
        return -EPERM;
    }
    
    // ... proceed with initialization
}
```

---

## 5. Security Testing

### 5.1 Static Analysis

**Tools:**
- **sparse:** Kernel static analyzer
- **Coccinelle:** Pattern-based code analysis
- **smatch:** Source code checker
- **clang static analyzer**

**Run Static Analysis:**
```bash
# Build with sparse
make C=1 CF="-D__CHECK_ENDIAN__" M=drivers/net/wireless/mt7927

# Run Coccinelle checks
spatch --sp-file checks/security.cocci --dir drivers/net/wireless/mt7927

# Run smatch
smatch -p=kernel drivers/net/wireless/mt7927/*.c
```

---

### 5.2 Dynamic Analysis

**Kernel Sanitizers:**
```bash
# Enable KASAN (Kernel Address Sanitizer)
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y

# Enable UBSAN (Undefined Behavior Sanitizer)
CONFIG_UBSAN=y
CONFIG_UBSAN_SANITIZE_ALL=y

# Enable KCSAN (Kernel Concurrency Sanitizer)
CONFIG_KCSAN=y
```

**Fuzzing:**
```bash
# Fuzz IOCTL handlers with syzkaller
# See: https://github.com/google/syzkaller

# Create syscall descriptions for your driver IOCTLs
# Run syzkaller in VM
```

---

### 5.3 Security Audit Checklist

**Pre-Release Security Audit:**

#### Code Review
- [ ] All user input validated
- [ ] No unsafe string functions
- [ ] Proper locking (no race conditions)
- [ ] DMA operations validated
- [ ] Error handling complete
- [ ] Resource cleanup on all paths
- [ ] No hardcoded secrets/credentials

#### Testing
- [ ] KASAN build tested
- [ ] UBSAN build tested
- [ ] Fuzzing completed (IOCTL handlers)
- [ ] Concurrency testing completed
- [ ] Stress testing completed
- [ ] Module load/unload cycles tested

#### Documentation
- [ ] Security considerations documented
- [ ] Threat model documented
- [ ] Known limitations documented
- [ ] Incident response plan documented

---

## 6. Incident Response

### 6.1 Security Vulnerability Handling

**Vulnerability Report Process:**

1. **Report Reception:**
   - Email: security@[project].org (create this)
   - PGP key available for encrypted reports
   - Acknowledge within 24 hours

2. **Triage:**
   - Assess severity (Critical/High/Medium/Low)
   - Determine affected versions
   - Assign to security team member

3. **Fix Development:**
   - Develop fix privately
   - Test thoroughly
   - Prepare security advisory

4. **Coordinated Disclosure:**
   - Notify distros via distros@vs.openwall.org (7 days advance)
   - Prepare CVE request if applicable
   - Release fix and advisory simultaneously

5. **Post-Incident:**
   - Post-mortem analysis
   - Update security processes
   - Improve testing to catch similar issues

---

### 6.2 Security Advisory Template

```markdown
# Security Advisory: [TITLE]

**CVE ID:** CVE-YYYY-NNNNN (if assigned)
**Severity:** [Critical/High/Medium/Low]
**Affected Versions:** [Version range]
**Fixed In:** [Version number]
**Reported By:** [Reporter name] (if permission granted)

## Summary
[Brief description of vulnerability]

## Impact
[What can an attacker do?]

## Affected Components
- Component 1
- Component 2

## Mitigation
1. Upgrade to version X.Y.Z
2. Or apply patch: [link]
3. Workaround (if available): [description]

## Timeline
- YYYY-MM-DD: Vulnerability reported
- YYYY-MM-DD: Fix developed
- YYYY-MM-DD: Fix released

## References
- CVE link
- Patch link
- Related advisories

## Credits
[Reporter name] for responsible disclosure
```

---

## 7. Security Best Practices Summary

### For Developers

**DO:**
- ✅ Validate all input from userspace
- ✅ Use kernel-provided safe functions
- ✅ Test with sanitizers (KASAN, UBSAN)
- ✅ Sign modules before distribution
- ✅ Document security considerations
- ✅ Follow kernel coding standards
- ✅ Use appropriate locking primitives
- ✅ Check return values
- ✅ Clean up resources on error paths

**DON'T:**
- ❌ Use unsafe string functions (strcpy, sprintf)
- ❌ Access userspace memory directly
- ❌ Ignore race conditions
- ❌ Skip input validation
- ❌ Leak memory or other resources
- ❌ Use unchecked pointer arithmetic
- ❌ Trust hardware/firmware implicitly
- ❌ Hardcode credentials or secrets

---

## 8. Resources

### Security Tools
- **Sparse:** https://sparse.docs.kernel.org/
- **Coccinelle:** https://coccinelle.gitlabpages.inria.fr/website/
- **Syzkaller:** https://github.com/google/syzkaller
- **KASAN:** https://www.kernel.org/doc/html/latest/dev-tools/kasan.html

### Security Guidelines
- **Kernel Self-Protection:** https://kernsec.org/wiki/index.php/Kernel_Self_Protection_Project
- **Linux Driver Security:** https://www.kernel.org/doc/html/latest/security/
- **CWE Top 25:** https://cwe.mitre.org/top25/

### Reporting
- **CVE Numbering:** https://cve.mitre.org/
- **Distros List:** https://oss-security.openwall.org/wiki/mailing-lists/distros

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Security Contact:** security@[project].org (to be created)  
**PGP Key:** [To be generated]

---

**🔒 Remember:** Security is not a feature, it's a requirement. When in doubt, choose the more secure option.
