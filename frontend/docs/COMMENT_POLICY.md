# Comment Policy for Quantum Forge Frontend

## Purpose

This document explains the permanent comment policy for the Quantum Forge frontend codebase. These comments are intentionally preserved to ensure that non-programmers can understand the codebase and its components.

## Permanent Comment Requirements

### 1. File Header Comments
Every file must include a header comment block with:
```javascript
// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
```

### 2. Module Documentation
Each file must have a detailed comment explaining:
- **Module Purpose**: What the file is intended to do
- **What it renders/provides**: Specific functionality or UI elements
- **How it fits into the app**: Relationship to the broader Quantum Forge platform
- **Author**: Attribution for the scaffold stage

### 3. Component Documentation
React components must include:
- **User-friendly summary**: Plain English explanation of what the component does
- **Props documentation**: Explanation of expected properties and their purposes
- **Data contract shapes**: Examples of data structures used

### 4. Function Documentation
Functions must include:
- **Plain English description**: What the function does
- **Parameter explanations**: What each parameter represents
- **Return value description**: What the function returns

## Why Comments Are Preserved

### Educational Value
The Quantum Forge platform is designed for scientists who understand quantum physics but may not be experienced programmers. The comments serve as:

1. **Learning aids** for understanding how the frontend works
2. **Documentation** for future maintenance and extension
3. **Onboarding tools** for new team members
4. **Reference materials** for integrating with backend services

### Non-Coder Accessibility
Comments are written in plain English with minimal technical jargon to ensure:
- Scientists can understand the codebase without programming expertise
- Domain experts can contribute to requirements and validation
- Cross-functional teams can collaborate effectively
- Knowledge transfer is facilitated between technical and scientific team members

## Comment Structure Examples

### File Header Template
```javascript
// NOTE (permanent): This file contains educational notes for non-coders.
// Do not remove comments unless explicitly requested in a written instruction.
// These notes explain purpose, props, and data contract shapes.
//
// Module Purpose: [Brief description of what this file does]
// What this file renders: [Specific UI elements or functionality]
// How it fits into the Quantum Forge app: [Relationship to broader platform]
// Author: [Author attribution]
```

### Component Documentation Template
```javascript
/**
 * Component Name
 * 
 * Plain English description of what this component does and why it exists.
 * 
 * For non-coders: Explanation of the component's purpose using familiar concepts
 * and analogies that relate to scientific workflows.
 * 
 * @param paramName - Description of what this parameter represents
 * @param anotherParam - Description with expected data type and examples
 */
```

### Function Documentation Template
```javascript
/**
 * Function Name
 * 
 * Plain English description of what this function does.
 * 
 * For non-coders: Explanation using familiar concepts about what operation
 * is being performed and why.
 * 
 * @param parameter - Description of what this parameter represents
 * @returns Description of what the function returns
 */
```

## Enforcement Policy

### Automatic Preservation
Comments are preserved through:
- Version control tracking of comment changes
- Code review requirements for comment modifications
- Automated checks in the build process
- Documentation generation from preserved comments

### Modification Guidelines
Comments may only be removed or modified when:
- Explicitly requested in writing by a project stakeholder
- Technically inaccurate and requiring correction
- Redundant with other preserved documentation
- Obsolete due to major architectural changes

## Benefits of Permanent Comments

### Knowledge Retention
- Prevents loss of institutional knowledge
- Maintains context for future developers
- Preserves design decisions and rationale
- Documents data contracts and API expectations

### Collaboration Enhancement
- Enables scientists to participate in code reviews
- Facilitates cross-team communication
- Reduces onboarding time for new contributors
- Improves documentation quality and completeness

### Quality Assurance
- Ensures consistent understanding of component purposes
- Maintains clear data flow documentation
- Preserves architectural decision rationale
- Supports long-term maintainability

This policy ensures that the Quantum Forge frontend remains accessible and understandable to all team members, regardless of their programming background.
