# ANFSRC Python 3 Migration Strategy

## Executive Summary

The ANFSRC repository contains **157 Python files** (144 .xpy executables + 13 .py libraries) with **95% requiring migration** from Python 2 to Python 3. This document provides a comprehensive strategy for migration, deprecation, and modernization of the codebase.

**Key Statistics:**
- 214+ Python 2 pattern instances identified
- 4 major component areas affected
- Estimated 6-12 month migration timeline
- 30-40% potential deprecation candidates

## 1. Decision Matrix Framework

### 1.1 Component Evaluation Criteria

Each Python component will be evaluated using the following weighted scoring system:

| Criterion | Weight | Score (0-5) | Description |
|-----------|--------|-------------|-------------|
| **Usage Frequency** | 30% | 0-5 | Daily(5), Weekly(4), Monthly(3), Quarterly(2), Rarely(1), Never(0) |
| **TA/CEUSN Dependency** | 25% | 0-5 | None(5), Historical only(3), Active dependency(0) |
| **Maintenance Burden** | 20% | 0-5 | Low complexity(5), Medium(3), High complexity(1), Critical bugs(0) |
| **Technical Complexity** | 15% | 0-5 | Simple script(5), Standard libraries(3), Complex integrations(1) |
| **Alternative Solutions** | 10% | 0-5 | Better alternative exists(0), No alternative(5) |

### 1.2 Decision Thresholds

Based on weighted score (0-5 scale):
- **Score ≥ 3.5**: Full migration to Python 3
- **Score 2.0-3.4**: Conditional migration (based on resources)
- **Score 1.0-1.9**: Move to `/anf/no_build/` (archive)
- **Score < 1.0**: Deprecate and remove

### 1.3 Initial Component Assessment

#### High Priority Migration Candidates (Score > 4.0)
```
/anf/lib/pyanf/             - Core libraries (Score: 5.0)
/anf/bin/web/db2mongo/      - Active MongoDB integration (Score: 4.5)
/anf/bin/web/orb2json/      - Real-time data export (Score: 4.5)
/anf/bin/import/xi202_import/ - Active data import (Score: 4.2)
/anf/bin/utility/AMQP/      - Message processing (Score: 4.0)
```

#### Deprecation Candidates (Score < 2.0)
```
/anf/bin/utility/check_tastation/    - TA project ended (Score: 0.8)
/anf/bin/utility/dbwfserver_ta_setup/ - TA specific (Score: 0.5)
/anf/bin/web/usarray_deploy_map/     - USArray complete (Score: 1.2)
/anf/bin/utility/baler44_*           - Legacy hardware (Score: 1.5)
```

## 2. Phased Migration Strategy

### Phase 1: Foundation (Weeks 1-4)
**Goal:** Establish core Python 3 infrastructure

#### Components:
- `/anf/lib/pyanf/` (8 files) - Core library modules
- `/anf/data/python/` - Python bootstrap and utilities
- Build system updates for Python 3 support

#### Actions:
1. Create Python 3.8/3.10 virtual environments
2. Migrate core `pyanf` modules using 2to3
3. Update import statements and exception handling
4. Establish testing framework with pytest
5. Document API changes for downstream dependencies

#### Success Metrics:
- All core libraries pass unit tests
- No regression in existing Python 2 functionality
- Documentation updated for Python 3 patterns

### Phase 2: Critical Infrastructure (Weeks 5-12)
**Goal:** Migrate essential real-time and data processing tools

#### Components:
- `/anf/bin/web/orb2json/` - ORB to JSON converter
- `/anf/bin/web/db2mongo/` - Database to MongoDB
- `/anf/bin/import/xi202_import/` - Critical data import
- `/anf/bin/web/soh2mongo/` - State of health monitoring

#### Actions:
1. Address string/bytes handling for ORB connections
2. Update MongoDB drivers to pymongo 3.x
3. Migrate exception handling patterns
4. Implement integration tests with test ORB
5. Parallel run testing (Python 2 vs Python 3)

#### Critical Considerations:
- ORB binary protocol compatibility
- MongoDB connection pooling changes
- Real-time data stream integrity

### Phase 3: Utility Migration (Weeks 13-20)
**Goal:** Migrate high-value utility applications

#### Components:
- `/anf/bin/utility/AMQP/` - Message queue processing
- `/anf/bin/utility/auto_qc/` - Quality control systems
- `/anf/bin/utility/pymail_parser/` - Email processing
- `/anf/bin/web/station_maps/` - Visualization tools

#### Actions:
1. Batch conversion using lib2to3 custom fixers
2. Manual review of file I/O operations
3. Update plotting libraries (matplotlib compatibility)
4. Migrate from `urllib2` to `urllib.request`
5. Address `pickle` protocol compatibility

### Phase 4: Cleanup and Deprecation (Weeks 21-26)
**Goal:** Complete migration and remove obsolete code

#### Components:
- Remaining `/anf/bin/utility/` tools
- Low-priority web services
- Test and example code

#### Actions:
1. Move deprecated TA/CEUSN tools to `/anf/no_build/`
2. Final migration of low-priority utilities
3. Remove Python 2 compatibility code
4. Update all documentation
5. Archive historical components

## 3. Technical Approach

### 3.1 Migration Tools and Process

#### Automated Conversion Pipeline
```bash
# Step 1: Initial conversion
2to3 -w -n --no-diffs \
  -f import -f except -f print -f exec \
  -f has_key -f dict -f xrange \
  <source_file.py>

# Step 2: Custom fixers for Antelope patterns
python3 anf_migration_fixer.py <source_file.py>

# Step 3: Manual review checklist
- [ ] String/bytes handling for binary data
- [ ] File I/O encoding specifications
- [ ] Integer division operators
- [ ] Dictionary iteration methods
- [ ] Exception chaining
```

#### Testing Strategy
1. **Unit Tests**: pytest framework for all libraries
2. **Integration Tests**: Test with Antelope 5.9 bindings
3. **System Tests**: Full pipeline testing with real data
4. **Performance Tests**: Benchmark critical paths
5. **Regression Tests**: Compare outputs with Python 2 version

### 3.2 Common Migration Patterns

#### ORB Connection Updates
```python
# Python 2 (old)
orbfd = orb.orbopen(orbname, "r&")
pktbuf = orb.orbreap(orbfd)

# Python 3 (new)
orbfd = orb.orbopen(orbname, "r&")
pktbuf = orb.orbreap(orbfd).encode('utf-8')  # Handle bytes
```

#### MongoDB Driver Updates
```python
# Python 2 (old)
from pymongo import Connection
conn = Connection(host, port)

# Python 3 (new)
from pymongo import MongoClient
client = MongoClient(host, port)
```

## 4. Resource Planning

### 4.1 Team Requirements

| Role | FTE | Duration | Responsibilities |
|------|-----|----------|------------------|
| Lead Developer | 1.0 | 6 months | Architecture, core libraries, integration |
| Python Developer | 1.0 | 6 months | Utility migration, testing |
| QA Engineer | 0.5 | 4 months | Test development, validation |
| System Admin | 0.25 | 6 months | Environment setup, deployment |

### 4.2 Time Estimates by Phase

| Phase | Duration | Effort | Risk Level |
|-------|----------|--------|------------|
| Phase 1: Foundation | 4 weeks | 2 person-months | Low |
| Phase 2: Critical Infrastructure | 8 weeks | 4 person-months | High |
| Phase 3: Utility Migration | 8 weeks | 3 person-months | Medium |
| Phase 4: Cleanup | 6 weeks | 1.5 person-months | Low |
| Testing & Validation | Ongoing | 2 person-months | Medium |
| **Total** | **26 weeks** | **12.5 person-months** | **Medium-High** |

### 4.3 Infrastructure Requirements

- **Development Environment**
  - Python 3.8 and 3.10 installations
  - Antelope 5.9 development license
  - MongoDB test instance
  - AMQP test broker

- **Testing Infrastructure**
  - Isolated test ORB instance
  - Sample seismic data sets
  - Continuous Integration pipeline
  - Performance monitoring tools

- **Documentation Platform**
  - Migration guide wiki
  - API documentation system
  - Training materials repository

## 5. Risk Assessment

### 5.1 Critical Risk Areas

#### High Risk Components
| Component | Risk | Impact | Mitigation |
|-----------|------|--------|------------|
| ORB Binary Protocol | Breaking real-time data | Operational failure | Extensive integration testing, gradual rollout |
| MongoDB Integration | Data loss/corruption | Data integrity | Parallel run period, data validation |
| AMQP Processing | Message queue failure | Processing delays | Queue monitoring, fallback mechanisms |
| Cython Modules | Compilation failures | Performance degradation | Pre-compiled wheels, fallback Python |

### 5.2 Dependency Risks

```
Critical External Dependencies:
├── Antelope Python bindings (version compatibility)
├── MongoDB drivers (pymongo 2.x → 3.x breaking changes)
├── AMQP libraries (protocol version support)
├── Scientific libraries (NumPy, ObsPy compatibility)
└── System libraries (GLIBC version requirements)
```

### 5.3 Mitigation Strategies

1. **Gradual Rollout**
   - Maintain Python 2 and 3 versions in parallel
   - Use feature flags for version switching
   - Implement canary deployments

2. **Rollback Procedures**
   ```bash
   # Quick rollback script
   #!/bin/bash
   ln -sf /opt/anf/5.9-python2 /opt/anf/current
   systemctl restart anf-services
   ```

3. **Data Integrity Checks**
   - Checksum validation for migrated data
   - Automated comparison of outputs
   - Manual verification of critical paths

4. **Performance Monitoring**
   - Baseline performance metrics
   - Real-time monitoring during migration
   - Alert thresholds for degradation

## 6. Deprecation Strategy

### 6.1 Deprecation Criteria

Components will be deprecated if they meet ANY of these criteria:
- TA/CEUSN specific with no ongoing use
- Replaced by better alternatives
- Unmaintained for >2 years
- Incompatible with modern infrastructure

### 6.2 Deprecation Process

#### Stage 1: Identification (Week 1-2)
```bash
# Move to no_build directory
git mv /anf/bin/utility/check_tastation /anf/no_build/bin/utility/
git mv /anf/bin/web/usarray_deploy_map /anf/no_build/bin/web/
```

#### Stage 2: Documentation (Week 3)
- Create DEPRECATED.md listing all deprecated components
- Document alternatives for each deprecated tool
- Update user documentation

#### Stage 3: Communication (Week 4)
- Email notification to users
- GitHub announcement
- 90-day grace period

#### Stage 4: Archival (Week 13)
- Final backup to `/anf/no_build/`
- Remove from build system
- Archive to cold storage

### 6.3 Components for Immediate Deprecation

```
Confirmed Deprecation List:
/anf/bin/utility/check_tastation/        # TA project ended
/anf/bin/utility/dbwfserver_ta_setup/    # TA specific
/anf/bin/utility/baler44_uploaded/       # Legacy hardware
/anf/bin/utility/update_baler44_firmware/ # Legacy hardware
/anf/bin/web/usarray_deploy_map/         # USArray complete
/anf/bin/utility/ftp_uploads/            # Replaced by SFTP
```

## 7. Implementation Timeline

### Q1 2025 (January - March)
- **Week 1-4**: Phase 1 - Foundation migration
- **Week 5-12**: Phase 2 - Critical infrastructure

### Q2 2025 (April - June)
- **Week 13-20**: Phase 3 - Utility migration
- **Week 21-26**: Phase 4 - Cleanup and deprecation

### Q3 2025 (July - September)
- Production deployment
- Performance optimization
- Documentation completion

## 8. Success Metrics

### Technical Metrics
- 100% of critical path components migrated
- <5% performance degradation
- Zero data loss during migration
- 90% test coverage for migrated code

### Operational Metrics
- <1 hour downtime for migration
- 100% backward compatibility for APIs
- All critical alerts functioning
- Documentation 100% updated

## 9. Next Steps for GitHub Issues

### Immediate Issues to Create

#### Epic: Python 3 Migration
```markdown
Title: [EPIC] Migrate ANFSRC to Python 3
Description: Complete migration of 157 Python files from Python 2 to Python 3
Labels: epic, python3-migration, priority-high
```

#### Phase 1 Issues
```markdown
1. Title: [P1] Create Python 3 development environment
   Labels: phase-1, infrastructure

2. Title: [P1] Migrate pyanf core libraries
   Labels: phase-1, core-libraries

3. Title: [P1] Establish pytest framework
   Labels: phase-1, testing
```

#### Phase 2 Issues
```markdown
4. Title: [P2] Migrate orb2json to Python 3
   Labels: phase-2, critical-path, orb

5. Title: [P2] Update MongoDB integrations
   Labels: phase-2, database, mongodb

6. Title: [P2] Migrate xi202_import
   Labels: phase-2, data-import
```

#### Deprecation Issues
```markdown
7. Title: [DEPRECATE] Remove TA-specific utilities
   Labels: deprecation, cleanup

8. Title: [DEPRECATE] Archive baler44 tools
   Labels: deprecation, legacy
```

### Issue Templates

```markdown
## Migration Issue Template

**Component:** [path to component]
**Current Python:** 2.7
**Target Python:** 3.8/3.10
**Priority:** [High/Medium/Low]
**Dependencies:** [list dependencies]

### Migration Checklist
- [ ] Run 2to3 conversion
- [ ] Manual code review
- [ ] Update imports
- [ ] Fix string/bytes issues
- [ ] Update exception handling
- [ ] Add type hints
- [ ] Write/update tests
- [ ] Update documentation
- [ ] Integration testing
- [ ] Performance validation

### Acceptance Criteria
- All tests pass
- No performance regression
- Documentation updated
- Code review approved
```

## 10. Conclusion

This migration represents a critical modernization effort for ANFSRC. With 95% of Python files requiring updates and the end of Python 2 support, this migration is essential for:

1. **Security**: Continued security updates and patches
2. **Performance**: Modern Python 3 optimizations
3. **Maintainability**: Improved code quality and developer experience
4. **Compatibility**: Support for modern libraries and tools

The phased approach minimizes risk while ensuring systematic progress. The decision matrix provides objective criteria for migration vs deprecation decisions, optimizing resource allocation.

**Recommended immediate actions:**
1. Approve migration strategy and timeline
2. Allocate resources (2 FTE developers for 6 months)
3. Create GitHub issues for Phase 1
4. Begin deprecation of TA-specific components
5. Set up Python 3 development environment

**Expected outcomes:**
- Full Python 3 migration by Q3 2025
- 30-40% code reduction through deprecation
- Improved system reliability and performance
- Modern, maintainable codebase

---

*Document Version: 1.0*  
*Date: January 2025*  
*Next Review: February 2025*