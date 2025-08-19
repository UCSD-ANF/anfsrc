# Technology Stack

## Primary Languages
- **Python**: Modern utilities, web services, data processing (migrating from Python 2 to Python 3)
- **Perl**: Legacy system integration, many existing utilities
- **C/C++**: Performance-critical seismic data processing
- **MATLAB**: Scientific analysis and visualization tools
- **Tcl**: Some legacy applications
- **Shell Scripts**: System administration (bash/csh)
- **Fortran**: Limited legacy scientific computing

## Core Dependencies

### BRTT Antelope
- **Version Support**: Currently 5.9 (production), 5.7 (legacy)
- **Integration**: Core seismic data processing framework
- **Database**: Antelope database system for seismic data storage
- **ORB**: Object Ring Buffer for real-time data distribution

### Python Ecosystem
- **Version**: Transitioning from Python 2 to Python 3.8/3.10
- **Key Modules**: 
  - `simplekml`: KML generation for mapping
  - `amqplib`: AMQP message processing
  - `antelope`: Python bindings for Antelope system
  - `obspy`: Seismic data processing
  - Various scientific computing libraries
- **Package Management**: pip 23.1.2, custom bootstrap system

### Database Systems
- **Antelope DB**: Primary seismic data storage
- **MongoDB**: Document storage for web applications
- **JSON**: Data interchange format for web APIs

### Messaging and Communication
- **AMQP**: Message queuing for distributed processing
- **ORB**: Real-time data distribution
- **Mail Processing**: Email parsing and notification systems

### Web Technologies
- **JSON APIs**: RESTful web services
- **Static File Generation**: High-performance web content
- **Mapping**: Integration with mapping services and KML

## Build System
- **Custom Makefiles**: Based on Antelope's build conventions
- **Multi-Version Support**: Concurrent Antelope version handling
- **Environment Variables**: `$ANF` similar to `$ANTELOPE`
- **Bootstrap Installation**: `build_sourcetree` derived system

## Development Environment

### Setup Requirements
- BRTT Antelope installation
- Shell environment (csh or sh/bash support)
- Python development environment
- Perl with required modules
- MATLAB (for specific analysis tools)

### Build Process
1. Bootstrap installation creates `/opt/anf` tree
2. Environment setup scripts configure `$ANF` variable
3. Individual components build using local Makefiles
4. Installation integrates with existing Antelope setup

### File Organization Conventions
- **`.xpy`**: Python executables (Antelope convention)
- **`.xpl`**: Perl executables (Antelope convention)
- **`.pf`**: Parameter files for configuration
- **Makefiles**: Build configuration following ANF patterns

## Integration Patterns

### Antelope Integration
- Uses Antelope's peculiar build system for interpreted languages
- Parameter files (`.pf`) for configuration
- Database schema extensions in CSS3.0 format
- Integration with Antelope's tool ecosystem

### Web Service Architecture
- Database → JSON conversion utilities
- MongoDB integration for document storage
- RESTful APIs for data access
- Static file generation for performance

### Real-Time Processing
- ORB-based data distribution
- AMQP message processing
- Automated quality control systems
- Status monitoring and alerting

## Configuration Management
- **Parameter Files**: `.pf` files for application configuration
- **Local Modifications**: `pf_localmods` directories for customizations
- **Environment Setup**: Shell scripts for development environment
- **Multi-Version**: Support for multiple concurrent Antelope versions

## Testing and Quality Assurance
- **Test Suites**: Dedicated test directories for major components
- **Example Code**: Reference implementations and usage examples
- **Quality Control**: Automated data validation tools
- **Pre-commit Hooks**: Git pre-commit configuration for code quality

## Performance Considerations
- **C/C++ Extensions**: Performance-critical processing
- **Static File Generation**: Pre-computed web content
- **Database Optimization**: Efficient seismic data queries
- **Real-Time Processing**: Low-latency data stream handling