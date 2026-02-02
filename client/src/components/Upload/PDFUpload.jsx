import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadPortfolio } from '../../services/api';
import './PDFUpload.css';

export default function PDFUpload({ onUploadSuccess }) {
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null); // 'success' | 'error' | null
    const [errorMessage, setErrorMessage] = useState('');

    const onDrop = useCallback(async (acceptedFiles) => {
        const file = acceptedFiles[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            setUploadStatus('error');
            setErrorMessage('Please upload a PDF file');
            return;
        }

        setUploading(true);
        setUploadStatus(null);
        setErrorMessage('');

        try {
            const result = await uploadPortfolio(file);
            setUploadStatus('success');
            if (onUploadSuccess) {
                onUploadSuccess(result.portfolio);
            }
        } catch (error) {
            setUploadStatus('error');
            setErrorMessage(error.response?.data?.detail || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    }, [onUploadSuccess]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: false,
        disabled: uploading,
    });

    return (
        <div className="pdf-upload-container">
            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''} ${uploadStatus || ''}`}
            >
                <input {...getInputProps()} />

                <div className="dropzone-content">
                    {uploading ? (
                        <>
                            <Loader2 className="icon spinning" size={48} />
                            <h3>Processing Portfolio...</h3>
                            <p>Extracting holdings and fetching live prices</p>
                        </>
                    ) : uploadStatus === 'success' ? (
                        <>
                            <CheckCircle className="icon success" size={48} />
                            <h3>Portfolio Uploaded Successfully!</h3>
                            <p>Click or drop another file to update</p>
                        </>
                    ) : uploadStatus === 'error' ? (
                        <>
                            <AlertCircle className="icon error" size={48} />
                            <h3>Upload Failed</h3>
                            <p>{errorMessage}</p>
                        </>
                    ) : (
                        <>
                            {isDragActive ? (
                                <>
                                    <Upload className="icon active" size={48} />
                                    <h3>Drop your PDF here</h3>
                                </>
                            ) : (
                                <>
                                    <FileText className="icon" size={48} />
                                    <h3>Upload Portfolio Holdings</h3>
                                    <p>Drag & drop your PDF here, or click to browse</p>
                                </>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
