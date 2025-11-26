import React from 'react';
import '../styles/PdfAgreement.css'; 

const PdfViewer = ({ pdfUrl, onClose }) => (
    <div className="pdf-viewer-overlay">
        <div className="pdf-viewer-modal-container">
            <button className="close-pdf-btn" onClick={onClose}>&times;</button>
            <iframe src={pdfUrl} width="100%" height="100%" title="PDF Viewer"></iframe>
        </div>
    </div>
);

export default PdfViewer;