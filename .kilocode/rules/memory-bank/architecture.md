# System Architecture

## High-Level Structure
ANFSRC follows a three-tier directory structure that complements the BRTT Antelope system:

```
/opt/anf/
├── adm/     # Administrative and build system files
├── anf/     # Core ANF extensions and tools
└── antelope/ # Antelope-specific customizations
```

## Directory Organization

### `/adm` - Administrative Layer
- **Build System**: Custom Makefile system based on Antelope's build conventions
- **Bootstrap**: `coldstart/` contains initial setup and installation scripts
- **Documentation**: Man pages and technical documentation (`docs/`)
- **Setup Scripts**: Environment setup for both csh and sh shells (`setup/`)

### `/anf` - Core Application Layer
Primary application directory with specialized tools organized by function:

#### `/anf/bin` - Executable Applications
- **`/db`**: Database manipulation tools (arrivals, build checking, reassociation)
- **`/export`**: Data export utilities (IMQ330 updates)
- **`/import`**: Data import tools (GPS downloads, xi202 imports)
- **`/matlab`**: MATLAB-based analysis tools (journal mapping, testing)
- **`/rt`**: Real-time processing applications
- **`/utility`**: General-purpose utilities (AMQP, mail parsing, station monitoring)
- **`/web`**: Web services and APIs (JSON conversion, MongoDB integration)

#### `/anf/lib` - Libraries and Modules
- **`/pyanf`**: Python library modules for ANF-specific functionality
- **`/seispy`**: Seismic data processing libraries
- **`/makerules`**: Build system extensions

#### `/anf/data` - Data and Configuration
- **`/perl`**: Perl modules and templates
- **`/python`**: Python modules and bootstrapping
- **`/pf_localmods`**: Parameter file modifications
- **`/system`**: System-level configuration

### `/antelope` - Antelope Integration Layer
- **Response Files**: Instrument response data (`/data/responses`)
- **Schema Extensions**: Database schema modifications (`/data/schemas`)
- **Local Modifications**: Customizations to core Antelope functionality

## Key Architectural Patterns

### Multi-Language Integration
- **Python**: Primary language for modern utilities and web services
- **Perl**: Legacy scripts and system integration
- **C/C++**: Performance-critical seismic processing
- **MATLAB**: Scientific analysis and visualization
- **Shell Scripts**: System administration and deployment

### Build System Architecture
- Uses Antelope's custom build system with local extensions
- Each component has its own Makefile following ANF conventions
- Support for multiple Antelope versions simultaneously
- Automated dependency management and installation

### Data Flow Architecture
```
Seismic Stations → ORB → Processing Tools → Database → Web APIs → Visualization
```

### Real-Time Processing Pipeline
- **ORB (Object Ring Buffer)**: Central data distribution system
- **AMQP Integration**: Message queuing for distributed processing
- **MongoDB**: Modern document storage for web services
- **JSON APIs**: RESTful interfaces for data access

## Critical Implementation Paths

### Data Import Pipeline
1. Raw seismic data → Import utilities (`/anf/bin/import`)
2. Format conversion → Database storage
3. Quality control → Automated validation
4. Web export → JSON/MongoDB integration

### Real-Time Monitoring
1. Live data streams → ORB system
2. Processing → Utility applications
3. Status monitoring → Web dashboards
4. Alerting → Mail parsing and notification

### Web Services Architecture
- Database backends → JSON converters → Web APIs
- Static file generation for high-performance access
- Integration with mapping and visualization tools

## Technology Integration Points
- **Antelope Database**: Core seismic data storage
- **MongoDB**: Document storage for web applications
- **AMQP**: Distributed message processing
- **Web Standards**: JSON, REST APIs, modern web frameworks