document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    const downloadButton = document.getElementById('invoice_download_btn');
    const invoiceWrapper = document.getElementById('invoice_wrapper');
    const PDFConstructor = window.jsPDF || (window.jspdf && window.jspdf.jsPDF);

    if (!downloadButton || !invoiceWrapper || !window.html2canvas || !PDFConstructor) {
        return;
    }

    downloadButton.addEventListener('click', function() {
        const contentWidth = invoiceWrapper.offsetWidth;
        const contentHeight = invoiceWrapper.offsetHeight;
        const topLeftMargin = 20;
        const pdfWidth = contentWidth + (topLeftMargin * 2);
        const pdfHeight = (pdfWidth * 1.5) + (topLeftMargin * 2);
        const canvasImageWidth = contentWidth;
        const canvasImageHeight = contentHeight;
        const totalPDFPages = Math.ceil(contentHeight / pdfHeight) - 1;

        html2canvas(invoiceWrapper, {
            allowTaint: true
        }).then(function(canvas) {
            const imgData = canvas.toDataURL('image/jpeg', 1.0);
            const pdf = new PDFConstructor('p', 'pt', [pdfWidth, pdfHeight]);
            pdf.addImage(imgData, 'JPG', topLeftMargin, topLeftMargin, canvasImageWidth, canvasImageHeight);

            for (let i = 1; i <= totalPDFPages; i++) {
                pdf.addPage(pdfWidth, pdfHeight);
                pdf.addImage(imgData, 'JPG', topLeftMargin, -(pdfHeight * i) + (topLeftMargin * 4), canvasImageWidth, canvasImageHeight);
            }

            pdf.save('invoice.pdf');
        });
    });
});
