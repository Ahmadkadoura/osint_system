import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

export async function downloadResultsPdf(element, filename = "osint-report.pdf") {
  if (!element) return;

  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#0d1117",
    logging: false,
  });

  const imgData = canvas.toDataURL("image/png");
  const pdf = new jsPDF({ orientation: "p", unit: "mm", format: "a4" });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 10;

  const imgWidth = pageWidth - margin * 2;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  let heightLeft = imgHeight;
  let position = margin;

  pdf.addImage(imgData, "PNG", margin, position, imgWidth, imgHeight);
  heightLeft -= pageHeight - margin * 2;

  while (heightLeft > 0) {
    position = heightLeft - imgHeight + margin;
    pdf.addPage();
    pdf.addImage(imgData, "PNG", margin, position, imgWidth, imgHeight);
    heightLeft -= pageHeight - margin * 2;
  }

  pdf.save(filename);
}
