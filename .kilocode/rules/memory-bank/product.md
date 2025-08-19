# Product Overview

## Purpose
ANFSRC is a source code repository that extends and customizes the BRTT Antelope seismic data processing system for the Array Network Facility (ANF). It creates a supplementary tree under `/opt/anf` that works alongside the main Antelope installation.

## Problems It Solves
- **Antelope Extension**: Provides additional tools and capabilities not available in the core Antelope system
- **Version Management**: Supports multiple concurrent Antelope versions for production and testing environments
- **Specialized Seismic Processing**: Implements domain-specific tools for seismic data analysis, station monitoring, and data export
- **Web Integration**: Bridges seismic data systems with modern web technologies (JSON APIs, MongoDB integration)
- **Real-time Processing**: Handles real-time seismic data streams through ORB (Object Ring Buffer) systems

## Core Functionality
- **Data Import/Export**: Tools for importing seismic data from various sources and exporting to different formats
- **Station Management**: Utilities for monitoring and managing seismic station deployments
- **Real-time Monitoring**: Applications for processing live seismic data streams
- **Web Services**: APIs and tools for making seismic data available via web interfaces
- **Quality Control**: Automated systems for data quality assessment and validation
- **Visualization**: Tools for generating maps, plots, and other visual representations of seismic data

## Target Users
- Seismologists and geophysicists
- Network operators managing seismic monitoring systems
- Researchers analyzing earthquake and seismic data
- System administrators maintaining seismic data processing infrastructure

## Key Features
- Multi-language support (Python, Perl, C/C++, MATLAB, Tcl)
- Integration with MongoDB for modern data storage
- AMQP messaging for distributed processing
- Web-based visualization and data access
- Automated quality control and monitoring
- Support for various seismic data formats and protocols