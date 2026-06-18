/**
 * PDF Generation Utilities
 *
 * Converts HTML reports to PDF using puppeteer or other tools
 * Can be run server-side or client-side
 *
 * For production: Install puppeteer via `npm install puppeteer`
 * For lightweight: Use client-side html2pdf via CDN
 */

/**
 * Server-side PDF generation using puppeteer
 * Requires: npm install puppeteer
 *
 * Usage:
 *   import { generatePDFFromHTML } from '@/lib/reports/pdf-generator';
 *   const pdf = await generatePDFFromHTML(htmlContent);
 *   return new Response(pdf, {
 *     headers: { 'Content-Type': 'application/pdf' }
 *   });
 */
export async function generatePDFFromHTML(
  htmlContent: string,
  options?: {
    format?: 'A4' | 'Letter';
    margin?: {
      top?: number;
      right?: number;
      bottom?: number;
      left?: number;
    };
    scale?: number;
  }
): Promise<Buffer> {
  try {
    // Lazy load puppeteer only if needed
    const puppeteer = await import('puppeteer');

    const browser = await puppeteer.default.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

    const pdfBuffer = await page.pdf({
      format: options?.format || 'A4',
      margin: options?.margin || {
        top: '0.4in',
        right: '0.4in',
        bottom: '0.4in',
        left: '0.4in',
      },
      scale: options?.scale || 1,
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate:
        '<div style="width: 100%; text-align: center; font-size: 10px; color: #999;">' +
        '<span class="pageNumber"></span> / <span class="totalPages"></span>' +
        '</div>',
    });

    await browser.close();

    return pdfBuffer;
  } catch (error) {
    console.error('PDF generation failed:', error);
    throw new Error(
      'PDF generation requires puppeteer. Install with: npm install puppeteer'
    );
  }
}

/**
 * Client-side PDF generation script snippet
 * Can be injected into HTML or used as a download link
 */
export const html2pdfClientScript = `
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<script>
function downloadReportAsPDF() {
  const element = document.body;
  const opt = {
    margin: 10,
    filename: 'trading-report-' + new Date().getTime() + '.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
  };
  html2pdf().set(opt).from(element).save();
}
</script>
`;

/**
 * Alternative: Use PDFKit for more control
 * Requires: npm install pdfkit
 *
 * This is lighter than puppeteer but less flexible for complex HTML
 */
export async function generatePDFWithPDFKit(
  htmlContent: string
): Promise<Buffer> {
  try {
    const PDFDocument = await import('pdfkit');
    // PDFKit doesn't render HTML directly
    // Would need to parse HTML and build PDF programmatically
    throw new Error('PDFKit requires manual HTML parsing. Use puppeteer instead.');
  } catch (error) {
    throw error;
  }
}

/**
 * Stream PDF response for large files
 * Useful for reports that might be large
 */
export async function streamPDFResponse(
  htmlContent: string,
  filename: string
): Promise<ReadableStream<Uint8Array>> {
  // Using Web Streams API for streaming
  return new ReadableStream(async (controller) => {
    try {
      const pdfBuffer = await generatePDFFromHTML(htmlContent);
      controller.enqueue(new Uint8Array(pdfBuffer));
      controller.close();
    } catch (error) {
      controller.error(error);
    }
  });
}

/**
 * Generate PDF and save to temporary location
 */
export async function savePDFToTemp(
  htmlContent: string,
  filename: string
): Promise<string> {
  try {
    const fs = await import('fs').then((m) => m.promises);
    const path = await import('path');
    const os = await import('os');

    const pdfBuffer = await generatePDFFromHTML(htmlContent);
    const tempPath = path.join(os.tmpdir(), filename);

    await fs.writeFile(tempPath, pdfBuffer);

    return tempPath;
  } catch (error) {
    console.error('Failed to save PDF:', error);
    throw error;
  }
}

/**
 * Configuration for different rendering engines
 */
export const rendererConfigs = {
  puppeteer: {
    name: 'Puppeteer',
    description: 'Full-featured HTML to PDF with complex CSS support',
    pros: ['Best quality', 'CSS support', 'Charts rendering'],
    cons: ['Larger bundle', 'Needs headless browser'],
    setupCommand: 'npm install puppeteer',
  },
  html2pdf: {
    name: 'html2pdf.js',
    description: 'Lightweight client-side HTML to PDF',
    pros: ['No server required', 'Small bundle'],
    cons: ['Limited CSS', 'Client-side only'],
    setupCommand: 'CDN only',
  },
  pdfkit: {
    name: 'PDFKit',
    description: 'Node.js PDF generation library',
    pros: ['No headless browser', 'Lightweight'],
    cons: ['No HTML rendering', 'Manual parsing'],
    setupCommand: 'npm install pdfkit',
  },
  weasyprint: {
    name: 'WeasyPrint',
    description: 'Python-based HTML/CSS to PDF',
    pros: ['Excellent CSS support', 'Python integration'],
    cons: ['Python dependency', 'Server-side only'],
    setupCommand: 'pip install weasyprint',
  },
};
