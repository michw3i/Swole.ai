import { useState, useRef } from 'react';
import './ImageUpload.css';

const ImageUpload = ({ uploadedImage, setUploadedImage }) => {
  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image')) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setUploadedImage(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image')) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setUploadedImage(file);
    }
  };

  const handleRemove = () => {
    setImageFile(null);
    setPreviewUrl(null);
    setUploadedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="image-upload-container">
      <h2 className="upload-title">Photo</h2>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        style={{ display: 'none' }}
      />

      {!previewUrl ? (
        <div
          className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
          onClick={() => fileInputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="drop-zone-icon">+</div>
          <p className="drop-zone-text">Click or drag an image here</p>
          <span className="drop-zone-hint">JPG, PNG, WEBP up to 10MB</span>
        </div>
      ) : (
        <div className="preview-wrapper">
          <img src={previewUrl} alt="Preview" className="preview-image" />
          <div className="preview-actions">
            <button onClick={handleRemove} className="btn-remove">Remove</button>
            <button onClick={() => fileInputRef.current.click()} className="btn-change">Change Photo</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
