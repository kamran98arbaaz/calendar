# Changelog

All notable changes to the Wedding Hall Booking System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Production Release - 2026-01-10

- Implemented robust database backup and restore functionality with JSON format
- Added admin utilities page with organized backup, restore, and CSV export tools
- Enhanced search bar with special queries for months and hall names
- Optimized database queries and added composite indexes for better performance

## [0.0.25] - 2026-01-09

- Added hall name search functionality to quickly find bookings by venue
- Improved PDF receipt generation with company/customer copies and line breaks
- Removed highlights from booked/confirmed dates and highlighted hall details
- Reordered payment information in receipts for better readability

## [0.0.24] - 2026-01-09

- Implemented mini calendar navigation with previous/next month arrows
- Made dashboard counters clickable to view monthly booking lists
- Added Hall column to booking list tables for better context
- Synchronized counters with selected calendar month

## [0.0.23] - 2026-01-09

- Added performance optimizations with composite database indexes
- Optimized hall calendar queries to reduce loading times
- Improved database query efficiency for booking statistics
- Enhanced data fetching to minimize memory usage

## [0.0.22] - 2026-01-09

- Introduced month-based search with "Month Year" format support
- Added timestamp to CSV export filenames for better organization
- Included payment columns in CSV exports
- Improved search result formatting and display

## [0.0.21] - 2026-01-09

- Created admin backup and restore system with JSON data format
- Added schema dumping for complete database restoration
- Implemented in-memory file handling for serverless compatibility
- Fixed foreign key constraints in restore operations

## [0.0.20] - 2026-01-08

- Refined PDF receipt styling with compact layout and reduced font sizes
- Made receipt content fit on single page for better printing
- Enhanced receipt visual hierarchy with proper highlighting
- Improved receipt generation performance

## [0.0.19] - 2026-01-08

- Added company and customer copy sections to PDF receipts
- Implemented tear-line break between receipt copies
- Removed unnecessary highlights from date fields
- Highlighted hall information as key booking detail

## [0.0.18] - 2026-01-08

- Redesigned admin utilities page with elegant card-based layout
- Moved Export CSV to organized admin utils section
- Added icons and improved visual design consistency
- Enhanced admin interface usability

## [0.0.17] - 2026-01-08

- Made dashboard counters visible to all users including guests
- Improved counter display and accessibility
- Enhanced dashboard information transparency
- Better user experience for non-registered visitors

## [0.0.16] - 2026-01-07

- Added Hall column to date-based booking lists
- Improved table readability and information density
- Enhanced booking list context and navigation
- Better data presentation in search results

## [0.0.15] - 2026-01-07

- Implemented monthly booking list views for counters
- Added clickable counters for detailed booking information
- Created hall-specific monthly booking pages
- Improved dashboard interactivity

## [0.0.14] - 2026-01-07

- Added navigation arrows to mini calendar
- Implemented month-based counter synchronization
- Enhanced calendar user experience
- Improved dashboard functionality

## [0.0.13] - 2026-01-06

- Refined booking list templates with consistent styling
- Improved table layouts and responsive design
- Enhanced visual hierarchy in data displays
- Better mobile compatibility

## [0.0.12] - 2026-01-06

- Added payment fields to booking forms and models
- Implemented payment information tracking
- Enhanced booking data completeness
- Improved financial record keeping

## [0.0.11] - 2026-01-05

- Introduced PDF receipt generation functionality
- Added reportlab integration for document creation
- Implemented receipt download feature
- Enhanced booking confirmation process

## [0.0.10] - 2026-01-04

- Completed responsive design implementation
- Added mobile-friendly navigation and layouts
- Improved touch interactions and usability
- Enhanced cross-device compatibility

## [0.0.09] - 2026-01-04

- Implemented comprehensive search functionality
- Added booking search by multiple criteria
- Created search results page with filtering
- Improved data discovery capabilities

## [0.0.08] - 2026-01-03

- Added user authentication and authorization system
- Implemented role-based access control
- Created login and registration pages
- Enhanced security and user management

## [0.0.07] - 2026-01-03

- Developed hall-specific calendar views
- Added booking statistics and analytics
- Implemented date-based navigation
- Enhanced booking management interface

## [0.0.06] - 2026-01-02

- Created booking creation and editing forms
- Added form validation and error handling
- Implemented booking status management
- Enhanced user input experience

## [0.0.05] - 2026-01-02

- Built hall listing and selection interface
- Added upcoming bookings display
- Implemented booking counter widgets
- Improved dashboard information display

## [0.0.04] - 2026-01-01

- Designed and implemented main dashboard layout
- Added mini calendar component
- Created navigation header and footer
- Established consistent UI theme

## [0.0.03] - 2025-12-31

- Set up Flask application structure
- Configured database models and relationships
- Implemented basic routing system
- Added initial template framework

## [0.0.02] - 2025-12-30

- Initialized project with Flask and SQLAlchemy
- Created basic database schema
- Set up development environment
- Added initial configuration files

## [0.0.01] - 2025-12-29

- Project initialization
- Basic folder structure setup
- Dependency installation
- Initial commit to version control