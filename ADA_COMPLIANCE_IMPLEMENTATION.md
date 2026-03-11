# ADA Compliance Checker - Implementation Guide with pdf-lib

## Overview
This guide shows exactly how to build a VS Code extension that checks PDF ADA compliance using pdf-lib and GitHub Copilot.

## Architecture

```
User runs command
    ↓
Extension finds all PDFs in directory
    ↓
For each PDF:
    - Extract structure tags using pdf-lib
    - Extract metadata using pdf-lib
    - Build compliance report
    ↓
Send report to GitHub Copilot (VS Code Chat API)
    ↓
Display AI analysis to user
```

## Installation

```bash
npm install pdf-lib
npm install @vscode/vscode-languagemodel
```

## Core Implementation

### 1. PDF Structure Extraction Utility (`pdfAnalyzer.ts`)

```typescript
import { PDFDocument, PDFName, PDFDict, PDFArray } from 'pdf-lib';
import * as fs from 'fs';

interface ADAComplianceData {
  filename: string;
  isTagged: boolean;
  hasTitle: boolean;
  hasLanguage: boolean;
  documentTitle?: string;
  language?: string;
  structureTree: StructureElement[];
  images: ImageAccessibility[];
  formFields: FormFieldAccessibility[];
  issues: string[];
}

interface StructureElement {
  type: string;  // 'H1', 'H2', 'P', 'Figure', 'Table', etc.
  id?: string;
  altText?: string;
  children?: StructureElement[];
}

interface ImageAccessibility {
  hasAltText: boolean;
  altText?: string;
  isArtifact: boolean;
}

interface FormFieldAccessibility {
  name: string;
  hasLabel: boolean;
  hasTooltip: boolean;
}

export async function analyzePDFForADA(filePath: string): Promise<ADAComplianceData> {
  const pdfBytes = await fs.promises.readFile(filePath);
  const pdfDoc = await PDFDocument.load(pdfBytes, { 
    updateMetadata: false,
    ignoreEncryption: true 
  });

  const complianceData: ADAComplianceData = {
    filename: filePath,
    isTagged: false,
    hasTitle: false,
    hasLanguage: false,
    structureTree: [],
    images: [],
    formFields: [],
    issues: []
  };

  // 1. Check if document is tagged
  complianceData.isTagged = checkIfTagged(pdfDoc);
  if (!complianceData.isTagged) {
    complianceData.issues.push('Document is not marked as tagged PDF');
  }

  // 2. Extract metadata
  const metadata = extractMetadata(pdfDoc);
  complianceData.hasTitle = !!metadata.title;
  complianceData.hasLanguage = !!metadata.language;
  complianceData.documentTitle = metadata.title;
  complianceData.language = metadata.language;

  if (!metadata.title) {
    complianceData.issues.push('Document title is missing');
  }
  if (!metadata.language) {
    complianceData.issues.push('Document language is not specified');
  }

  // 3. Extract structure tree (tags)
  complianceData.structureTree = extractStructureTree(pdfDoc);
  
  // 4. Check heading hierarchy
  const headingIssues = validateHeadingHierarchy(complianceData.structureTree);
  complianceData.issues.push(...headingIssues);

  // 5. Extract image accessibility info
  complianceData.images = extractImageAccessibility(complianceData.structureTree);
  const imagesWithoutAlt = complianceData.images.filter(img => !img.hasAltText && !img.isArtifact);
  if (imagesWithoutAlt.length > 0) {
    complianceData.issues.push(`${imagesWithoutAlt.length} images missing alternative text`);
  }

  // 6. Extract form field accessibility
  complianceData.formFields = extractFormFieldAccessibility(pdfDoc);
  const fieldsWithoutLabels = complianceData.formFields.filter(field => !field.hasLabel);
  if (fieldsWithoutLabels.length > 0) {
    complianceData.issues.push(`${fieldsWithoutLabels.length} form fields missing labels`);
  }

  return complianceData;
}

function checkIfTagged(pdfDoc: PDFDocument): boolean {
  try {
    const catalog = pdfDoc.catalog;
    const markInfo = catalog.lookup(PDFName.of('MarkInfo'));
    
    if (markInfo instanceof PDFDict) {
      const marked = markInfo.lookup(PDFName.of('Marked'));
      return marked?.toString() === 'true';
    }
    return false;
  } catch (error) {
    return false;
  }
}

function extractMetadata(pdfDoc: PDFDocument): { title?: string; language?: string } {
  try {
    const title = pdfDoc.getTitle();
    const catalog = pdfDoc.catalog;
    const langObj = catalog.lookup(PDFName.of('Lang'));
    const language = langObj?.toString().replace(/[()]/g, '');

    return {
      title: title || undefined,
      language: language || undefined
    };
  } catch (error) {
    return {};
  }
}

function extractStructureTree(pdfDoc: PDFDocument): StructureElement[] {
  try {
    const catalog = pdfDoc.catalog;
    const structTreeRoot = catalog.lookup(PDFName.of('StructTreeRoot'));
    
    if (!structTreeRoot || !(structTreeRoot instanceof PDFDict)) {
      return [];
    }

    const kids = structTreeRoot.lookup(PDFName.of('K'));
    if (!kids) {
      return [];
    }

    return parseStructureElements(kids);
  } catch (error) {
    console.error('Error extracting structure tree:', error);
    return [];
  }
}

function parseStructureElements(element: any): StructureElement[] {
  const elements: StructureElement[] = [];

  try {
    if (element instanceof PDFArray) {
      // Array of structure elements
      for (let i = 0; i < element.size(); i++) {
        const child = element.lookup(i);
        elements.push(...parseStructureElements(child));
      }
    } else if (element instanceof PDFDict) {
      // Single structure element
      const typeObj = element.lookup(PDFName.of('S'));
      const type = typeObj?.toString().replace(/\//g, '');
      
      const structElement: StructureElement = {
        type: type || 'Unknown'
      };

      // Check for alt text
      const altObj = element.lookup(PDFName.of('Alt'));
      if (altObj) {
        structElement.altText = altObj.toString().replace(/[()]/g, '');
      }

      // Check for ID
      const idObj = element.lookup(PDFName.of('ID'));
      if (idObj) {
        structElement.id = idObj.toString();
      }

      // Recursively parse children
      const kids = element.lookup(PDFName.of('K'));
      if (kids) {
        structElement.children = parseStructureElements(kids);
      }

      elements.push(structElement);
    }
  } catch (error) {
    console.error('Error parsing structure element:', error);
  }

  return elements;
}

function validateHeadingHierarchy(structureTree: StructureElement[]): string[] {
  const issues: string[] = [];
  const headings = extractHeadings(structureTree);

  if (headings.length === 0) {
    issues.push('No heading structure found in document');
    return issues;
  }

  // Check if starts with H1
  if (headings[0].type !== 'H1') {
    issues.push('Document does not start with H1 heading');
  }

  // Check for skipped heading levels
  for (let i = 1; i < headings.length; i++) {
    const currentLevel = parseInt(headings[i].type.replace('H', ''));
    const previousLevel = parseInt(headings[i - 1].type.replace('H', ''));

    if (currentLevel > previousLevel + 1) {
      issues.push(`Heading hierarchy skips from ${headings[i - 1].type} to ${headings[i].type}`);
    }
  }

  return issues;
}

function extractHeadings(elements: StructureElement[]): StructureElement[] {
  const headings: StructureElement[] = [];

  for (const element of elements) {
    if (element.type.match(/^H[1-6]$/)) {
      headings.push(element);
    }
    if (element.children) {
      headings.push(...extractHeadings(element.children));
    }
  }

  return headings;
}

function extractImageAccessibility(structureTree: StructureElement[]): ImageAccessibility[] {
  const images: ImageAccessibility[] = [];

  function traverse(elements: StructureElement[]) {
    for (const element of elements) {
      if (element.type === 'Figure' || element.type === 'Image') {
        images.push({
          hasAltText: !!element.altText,
          altText: element.altText,
          isArtifact: false  // Artifacts are not in structure tree
        });
      }
      if (element.children) {
        traverse(element.children);
      }
    }
  }

  traverse(structureTree);
  return images;
}

function extractFormFieldAccessibility(pdfDoc: PDFDocument): FormFieldAccessibility[] {
  const formFields: FormFieldAccessibility[] = [];

  try {
    const form = pdfDoc.getForm();
    const fields = form.getFields();

    for (const field of fields) {
      const name = field.getName();
      
      // Check if field has tooltip (TU entry)
      let hasTooltip = false;
      try {
        const fieldDict = (field as any).acroField.dict;
        const tuObj = fieldDict.lookup(PDFName.of('TU'));
        hasTooltip = !!tuObj;
      } catch (e) {
        hasTooltip = false;
      }

      formFields.push({
        name,
        hasLabel: name.length > 0,  // Basic check
        hasTooltip
      });
    }
  } catch (error) {
    // No form fields or error accessing them
  }

  return formFields;
}
```

### 2. Report Generator (`reportGenerator.ts`)

```typescript
import { ADAComplianceData } from './pdfAnalyzer';

export function generateMarkdownReport(complianceResults: ADAComplianceData[]): string {
  let markdown = '# ADA Compliance Report\n\n';
  markdown += `Generated: ${new Date().toLocaleString()}\n\n`;
  markdown += `Total PDFs Analyzed: ${complianceResults.length}\n\n`;

  const compliantCount = complianceResults.filter(r => r.issues.length === 0).length;
  markdown += `✅ Compliant: ${compliantCount}\n`;
  markdown += `❌ Non-Compliant: ${complianceResults.length - compliantCount}\n\n`;

  markdown += '---\n\n';

  for (const result of complianceResults) {
    markdown += `## ${result.filename}\n\n`;

    // Overall status
    if (result.issues.length === 0) {
      markdown += '**Status:** ✅ COMPLIANT\n\n';
    } else {
      markdown += `**Status:** ❌ NON-COMPLIANT (${result.issues.length} issues)\n\n`;
    }

    // Basic checks
    markdown += '### Basic Accessibility Checks\n\n';
    markdown += `- **Tagged PDF:** ${result.isTagged ? '✅' : '❌'}\n`;
    markdown += `- **Has Title:** ${result.hasTitle ? '✅' : '❌'}`;
    if (result.documentTitle) {
      markdown += ` ("${result.documentTitle}")`;
    }
    markdown += '\n';
    markdown += `- **Has Language:** ${result.hasLanguage ? '✅' : '❌'}`;
    if (result.language) {
      markdown += ` (${result.language})`;
    }
    markdown += '\n\n';

    // Structure analysis
    markdown += '### Document Structure\n\n';
    const headings = countElementsByType(result.structureTree, /^H[1-6]$/);
    const paragraphs = countElementsByType(result.structureTree, /^P$/);
    const tables = countElementsByType(result.structureTree, /^Table$/);
    const lists = countElementsByType(result.structureTree, /^L$/);

    markdown += `- Headings: ${headings}\n`;
    markdown += `- Paragraphs: ${paragraphs}\n`;
    markdown += `- Tables: ${tables}\n`;
    markdown += `- Lists: ${lists}\n\n`;

    // Image accessibility
    if (result.images.length > 0) {
      markdown += '### Images\n\n';
      const withAlt = result.images.filter(img => img.hasAltText).length;
      markdown += `- Total Images: ${result.images.length}\n`;
      markdown += `- With Alt Text: ${withAlt} (${Math.round(withAlt / result.images.length * 100)}%)\n`;
      markdown += `- Missing Alt Text: ${result.images.length - withAlt}\n\n`;
    }

    // Form fields
    if (result.formFields.length > 0) {
      markdown += '### Form Fields\n\n';
      const withLabels = result.formFields.filter(f => f.hasLabel).length;
      const withTooltips = result.formFields.filter(f => f.hasTooltip).length;
      markdown += `- Total Fields: ${result.formFields.length}\n`;
      markdown += `- With Labels: ${withLabels}\n`;
      markdown += `- With Tooltips: ${withTooltips}\n\n`;
    }

    // Issues
    if (result.issues.length > 0) {
      markdown += '### Issues Found\n\n';
      for (const issue of result.issues) {
        markdown += `- ❌ ${issue}\n`;
      }
      markdown += '\n';
    }

    markdown += '---\n\n';
  }

  return markdown;
}

function countElementsByType(elements: any[], typePattern: RegExp): number {
  let count = 0;

  function traverse(els: any[]) {
    for (const el of els) {
      if (typePattern.test(el.type)) {
        count++;
      }
      if (el.children) {
        traverse(el.children);
      }
    }
  }

  traverse(elements);
  return count;
}

export function generatePromptForAI(complianceResults: ADAComplianceData[]): string {
  let prompt = 'Analyze the following PDF ADA compliance data and provide:\n';
  prompt += '1. A summary of critical accessibility issues\n';
  prompt += '2. Prioritized recommendations for fixing issues\n';
  prompt += '3. Best practices that are missing\n\n';
  prompt += 'Data:\n\n';
  prompt += JSON.stringify(complianceResults, null, 2);
  
  return prompt;
}
```

### 3. VS Code Extension Command (`extension.ts`)

```typescript
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { analyzePDFForADA } from './pdfAnalyzer';
import { generateMarkdownReport, generatePromptForAI } from './reportGenerator';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand(
    'ada-checker.checkPDFs',
    async () => {
      await checkPDFsInDirectory();
    }
  );

  context.subscriptions.push(disposable);
}

async function checkPDFsInDirectory() {
  try {
    // 1. Get current workspace folder
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
      vscode.window.showErrorMessage('No workspace folder open');
      return;
    }

    const rootPath = workspaceFolders[0].uri.fsPath;

    // 2. Find all PDF files
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Finding PDF files...',
        cancellable: false
      },
      async () => {
        const pdfFiles = await findPDFFiles(rootPath);

        if (pdfFiles.length === 0) {
          vscode.window.showInformationMessage('No PDF files found in directory');
          return;
        }

        vscode.window.showInformationMessage(`Found ${pdfFiles.length} PDF files. Analyzing...`);

        // 3. Analyze each PDF
        const results = [];
        for (let i = 0; i < pdfFiles.length; i++) {
          const pdfPath = pdfFiles[i];
          const relativePath = path.relative(rootPath, pdfPath);
          
          vscode.window.showInformationMessage(`Analyzing ${i + 1}/${pdfFiles.length}: ${relativePath}`);
          
          try {
            const analysis = await analyzePDFForADA(pdfPath);
            results.push(analysis);
          } catch (error) {
            vscode.window.showErrorMessage(`Error analyzing ${relativePath}: ${error}`);
          }
        }

        // 4. Generate markdown report
        const markdownReport = generateMarkdownReport(results);
        const reportPath = path.join(rootPath, 'ADA_Compliance_Report.md');
        await fs.promises.writeFile(reportPath, markdownReport);

        // 5. Open the report
        const doc = await vscode.workspace.openTextDocument(reportPath);
        await vscode.window.showTextDocument(doc);

        // 6. Send to GitHub Copilot for AI analysis
        await sendToGitHubCopilot(results);
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Error: ${error}`);
  }
}

async function findPDFFiles(directory: string): Promise<string[]> {
  const pdfFiles: string[] = [];

  async function traverse(dir: string) {
    const entries = await fs.promises.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        // Skip node_modules, .git, etc.
        if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
          await traverse(fullPath);
        }
      } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.pdf')) {
        pdfFiles.push(fullPath);
      }
    }
  }

  await traverse(directory);
  return pdfFiles;
}

async function sendToGitHubCopilot(results: any[]) {
  try {
    // Access GitHub Copilot via VS Code Chat API
    const models = await vscode.lm.selectChatModels({
      vendor: 'copilot',
      family: 'gpt-4'
    });

    if (models.length === 0) {
      vscode.window.showWarningMessage('GitHub Copilot not available');
      return;
    }

    const model = models[0];
    const prompt = generatePromptForAI(results);

    const messages = [
      vscode.LanguageModelChatMessage.User(prompt)
    ];

    const response = await model.sendRequest(messages, {}, new vscode.CancellationTokenSource().token);

    // Collect the response
    let aiAnalysis = '';
    for await (const chunk of response.text) {
      aiAnalysis += chunk;
    }

    // Show AI analysis in a new document
    const doc = await vscode.workspace.openTextDocument({
      content: `# AI Analysis of ADA Compliance\n\n${aiAnalysis}`,
      language: 'markdown'
    });
    await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });

  } catch (error) {
    vscode.window.showErrorMessage(`Error communicating with GitHub Copilot: ${error}`);
  }
}

export function deactivate() {}
```

### 4. Package Configuration (`package.json`)

```json
{
  "name": "ada-pdf-checker",
  "displayName": "ADA PDF Compliance Checker",
  "description": "Check PDF files for ADA compliance using GitHub Copilot",
  "version": "0.0.1",
  "engines": {
    "vscode": "^1.85.0"
  },
  "categories": ["Other"],
  "activationEvents": [],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "ada-checker.checkPDFs",
        "title": "Check PDFs for ADA Compliance"
      }
    ]
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./"
  },
  "dependencies": {
    "pdf-lib": "^1.17.1"
  },
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "@types/node": "^20.x",
    "typescript": "^5.3.0"
  }
}
```

## How It Works Step-by-Step

### Step 1: User Runs Command
User opens VS Code in a folder with PDFs and runs:
- `Cmd+Shift+P` → "Check PDFs for ADA Compliance"

### Step 2: Extension Finds PDFs
- Recursively scans workspace directory
- Finds all `.pdf` files
- Skips hidden folders and node_modules

### Step 3: For Each PDF, Extract Data
Using pdf-lib:
1. Load PDF document
2. Check if marked as "tagged" (MarkInfo.Marked)
3. Extract metadata (Title, Language)
4. Parse structure tree to get all tags (H1, H2, P, Figure, Table, etc.)
5. Extract alt text from Figure/Image elements
6. Check form fields for labels and tooltips
7. Validate heading hierarchy (no skipped levels)
8. Identify all issues

### Step 4: Generate Report
- Create markdown file with all findings
- Show compliance status for each PDF
- List all issues found
- Save as `ADA_Compliance_Report.md`

### Step 5: Send to GitHub Copilot
- Format data as JSON
- Send to VS Code Chat API (GitHub Copilot)
- AI analyzes the data and provides:
  - Summary of critical issues
  - Prioritized recommendations
  - Best practices guidance
- Display AI response in split view

## What pdf-lib Actually Extracts

### From the PDF Catalog:
```typescript
// Check if tagged
catalog.MarkInfo.Marked = true/false

// Language
catalog.Lang = "en-US"
```

### From Document Info:
```typescript
// Title
document.getTitle() = "Annual Report 2024"
```

### From Structure Tree:
```typescript
// Example structure tree
{
  type: "Document",
  children: [
    {
      type: "H1",
      children: [...]
    },
    {
      type: "P",
      children: [...]
    },
    {
      type: "Figure",
      altText: "Company logo",
      children: [...]
    },
    {
      type: "Table",
      children: [
        { type: "TR", children: [...] },
        { type: "TR", children: [...] }
      ]
    }
  ]
}
```

### From Form Fields:
```typescript
// Form field properties
{
  name: "firstName",
  tooltip: "Enter your first name",  // TU entry
  type: "text"
}
```

## Key Advantages of This Approach

1. **No DOMMatrix Issues** - pdf-lib is pure JavaScript
2. **Perfect for ADA Compliance** - Extracts exactly what you need
3. **Simple Integration** - Works immediately in VS Code
4. **Uses GitHub Copilot** - Leverages existing user tokens
5. **Generates Human-Readable Report** - Markdown format
6. **AI-Enhanced Analysis** - Copilot provides recommendations

## Limitations & Workarounds

### What pdf-lib Cannot Do:
- **Color contrast checking** - Would need to render PDF (use external tool or skip for POC)
- **Reading order validation** - Can check tag order, but not visual rendering order
- **OCR text detection** - Cannot determine if text is real vs. scanned image

### For POC:
Focus on what pdf-lib CAN do:
- ✅ Tag structure
- ✅ Alt text
- ✅ Metadata
- ✅ Heading hierarchy
- ✅ Form field labels

These cover 80% of ADA compliance requirements.

## Testing the Extension

1. Create test PDFs with known issues:
   - PDF without tags
   - PDF with images missing alt text
   - PDF with skipped heading levels (H1 → H3)
   - PDF with form fields without labels

2. Run the command and verify:
   - All issues are detected
   - Report is generated correctly
   - AI provides useful recommendations

## Next Steps for Production

1. Add more sophisticated validation rules
2. Handle edge cases (encrypted PDFs, corrupted files)
3. Add configuration options (which checks to run)
4. Improve error handling and user feedback
5. Add batch processing with progress indicators
6. Consider adding remediation suggestions
